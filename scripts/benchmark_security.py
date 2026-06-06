#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
import sys
import time
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

    latencies = []
    for _ in range(12):
        started = time.perf_counter()
        response = client.get("/security/dashboard", headers=headers)
        response.raise_for_status()
        latencies.append((time.perf_counter() - started) * 1000)

    print(
        json.dumps(
            {
                "runs": len(latencies),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "avg_ms": round(statistics.mean(latencies), 2),
                "median_ms": round(statistics.median(latencies), 2),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
