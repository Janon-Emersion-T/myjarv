from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import Header, HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.secops import security_engine


_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_PUBLIC_PATH_PREFIXES = (
    "/auth/login",
    "/auth/logout",
    "/auth/mfa/verify",
    "/health",
)
_LOCKDOWN_ALLOWED_PREFIXES = (
    "/auth/",
    "/health",
    "/security",
)


def _extract_token(authorization: str | None, x_jarvis_token: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return x_jarvis_token


def _is_auth_required() -> bool:
    return settings.SECURITY_REQUIRE_AUTH or settings.PRODUCTION_LOCK_MODE


def _check_rate_limit(client_id: str) -> None:
    window = settings.SECURITY_RATE_LIMIT_WINDOW_SECONDS
    limit = settings.SECURITY_RATE_LIMIT_MAX_REQUESTS
    bucket = _RATE_BUCKETS[client_id]
    now = time.time()
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        security_engine.record_event("abuse", "HIGH", client_id, "Rate limit exceeded.", {"window": window, "limit": limit})
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    bucket.append(now)


async def enforce_local_auth(
    request: HTTPConnection,
    x_jarvis_token: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any] | None:
    client_id = request.client.host if request.client else "unknown"
    _check_rate_limit(client_id)
    path = request.url.path
    method = getattr(request, "method", "WEBSOCKET")
    request.state.security_subject = None

    if path.startswith(_PUBLIC_PATH_PREFIXES):
        return None

    token = _extract_token(authorization, x_jarvis_token)
    subject: dict[str, Any] | None = None

    if x_api_key:
        try:
            api_key = security_engine.validate_api_key(x_api_key)
            subject = {
                "username": f"api-key:{api_key['label']}",
                "role": api_key["role_scope"],
                "department": api_key["attributes"].get("department", "operations"),
            }
        except Exception as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    elif token:
        try:
            subject = security_engine.authenticate_token(token)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    elif settings.LOCAL_AUTH_TOKEN and x_jarvis_token == settings.LOCAL_AUTH_TOKEN:
        subject = {"username": "local-token", "role": "admin", "department": "executive"}

    if security_engine.is_lockdown_active():
        if subject is None or (subject.get("role") != "admin" and not path.startswith("/security")):
            if not path.startswith(_LOCKDOWN_ALLOWED_PREFIXES):
                raise HTTPException(status_code=423, detail="Jarvis security lockdown is active.")

    if security_engine.is_offline_mode():
        if path.startswith(("/tasks", "/voice", "/collaboration", "/routing")) and method in {"POST", "PUT", "PATCH", "DELETE"}:
            if subject is None or subject.get("role") != "admin":
                raise HTTPException(status_code=503, detail="Jarvis secure offline mode is active.")

    if subject is None and _is_auth_required():
        raise HTTPException(status_code=401, detail="Missing or invalid security credentials.")

    if subject is not None:
        request.state.security_subject = subject
        security_engine.enforce_path(subject, request.url.path, method)
    return subject


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        if body:
            try:
                parsed = body.decode("utf-8")
                issues = security_engine.inspect_text(parsed)
                if issues:
                    security_engine.record_event(
                        "inspection",
                        "HIGH",
                        request.client.host if request.client else "unknown",
                        "Suspicious request body detected.",
                        {"issues": issues, "path": request.url.path},
                    )
                    return JSONResponse(status_code=400, content={"detail": "Suspicious request body blocked.", "issues": issues})
            except Exception:
                pass
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' ws: http: https:; img-src 'self' data:;"
        return response
