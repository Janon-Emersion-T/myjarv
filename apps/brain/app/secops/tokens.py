from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def _b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _b64decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def issue_token(data: dict[str, Any], secret: str, expires_in: int = 3600) -> str:
    payload = {**data, "exp": int(time.time()) + expires_in, "nonce": secrets.token_hex(8)}
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return f"{body}.{_b64encode(signature)}"


def verify_token(token: str, secret: str) -> dict[str, Any]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Malformed token.") from exc
    expected = _b64encode(hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Invalid token signature.")
    payload = json.loads(_b64decode(body).decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expired.")
    return payload
