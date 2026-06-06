#!/usr/bin/env python3
import json
import statistics
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.orchestrator import orchestrate_task  # noqa: E402
from app.schemas import TaskCreateRequest  # noqa: E402
from app.task_manager import task_manager  # noqa: E402


def run_once(index: int) -> float:
    started = time.perf_counter()
    request = TaskCreateRequest(
        message=f"Benchmark collaborative Laravel website planning run {index} {uuid.uuid4().hex[:6]}",
        requested_action="implementation plan",
        metadata={"client": "lkprofessionals", "memory_scopes": ["company", "project"]},
    )
    task = task_manager.create_task(orchestrate_task(request))
    if task["approval_level"] != "LOW":
        task_manager.approve_task(task["id"], "Benchmark", "Automated collaboration benchmark approval.")
    task_manager.execute_task(task["id"], executor="Benchmark", force_retry=False)
    return (time.perf_counter() - started) * 1000


def main() -> int:
    samples = [run_once(index) for index in range(5)]
    payload = {
        "runs": len(samples),
        "min_ms": round(min(samples), 2),
        "max_ms": round(max(samples), 2),
        "avg_ms": round(statistics.mean(samples), 2),
        "median_ms": round(statistics.median(samples), 2),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
