#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
venv_site_packages = sorted((APP_ROOT / "venv" / "lib").glob("python*/site-packages"))
for path in venv_site_packages:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> int:
    started = time.perf_counter()
    client = TestClient(app)
    created_ids: list[str] = []

    for _ in range(3):
        response = client.post(
            "/tasks",
            json={
                "message": f"Delete production files and deploy rollback plan {uuid.uuid4().hex[:6]}",
                "requested_action": "delete production files and deploy rollback",
            },
        )
        response.raise_for_status()
        task = response.json()
        created_ids.append(task["id"])
        approvals = [
            {"reviewer": "Ops Lead", "reviewer_role": "manager", "department": "engineering"},
            {"reviewer": "Infra Director", "reviewer_role": "director", "department": "engineering"},
            {"reviewer": "CEO", "reviewer_role": "executive", "department": "finance"},
        ]
        for item in approvals:
            approved = client.post(
                f"/tasks/{task['id']}/approve",
                json={
                    **item,
                    "written_document": {"title": "Approval", "body": f"Signed by {item['reviewer']}."},
                },
            )
            approved.raise_for_status()

    metrics = client.get("/approvals/metrics")
    metrics.raise_for_status()
    elapsed = round(time.perf_counter() - started, 3)
    print(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "tasks_created": created_ids,
                "metrics": metrics.json(),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
