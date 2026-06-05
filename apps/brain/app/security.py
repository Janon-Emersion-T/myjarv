from fastapi import Header, HTTPException

from app.config import settings


def enforce_local_auth(x_jarvis_token: str | None = Header(default=None)) -> None:
    if not settings.PRODUCTION_LOCK_MODE and not settings.LOCAL_AUTH_TOKEN:
        return

    if not x_jarvis_token or x_jarvis_token != settings.LOCAL_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Missing or invalid Jarvis auth token.")

