#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
venv_site_packages = sorted((APP_ROOT / "venv" / "lib").glob("python*/site-packages"))
for path in venv_site_packages:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.task_manager import task_manager  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Jarvis approval state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    queue_parser = subparsers.add_parser("queue")
    queue_parser.add_argument("--limit", type=int, default=20)

    history_parser = subparsers.add_parser("history")
    history_parser.add_argument("--limit", type=int, default=20)
    history_parser.add_argument("--task-id", default=None)

    subparsers.add_parser("metrics")
    subparsers.add_parser("shutdown")

    args = parser.parse_args()
    if args.command == "queue":
        payload = {"queue": task_manager.list_approval_queue(limit=args.limit)}
    elif args.command == "history":
        payload = {"approvals": task_manager.list_approval_history(limit=args.limit, task_id=args.task_id)}
    elif args.command == "shutdown":
        payload = task_manager.get_emergency_shutdown()
    else:
        payload = task_manager.approval_metrics()
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
