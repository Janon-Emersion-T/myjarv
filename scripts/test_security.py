#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)
    login = client.post(
        "/auth/login",
        json={"username": settings.SECURITY_BOOTSTRAP_ADMIN, "password": settings.SECURITY_BOOTSTRAP_PASSWORD},
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    summary = {
        "health": client.get("/health").json(),
        "me": client.get("/auth/me", headers=headers).json(),
        "compliance": client.get("/security/compliance", headers=headers).json(),
        "metrics": client.get("/security/metrics", headers=headers).json(),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
