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

from app.self_learning import self_learning_engine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Jarvis self-learning state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--limit", type=int, default=100)
    run.add_argument("--reviewer", default="CLI")
    subparsers.add_parser("dashboard")
    subparsers.add_parser("analytics")
    subparsers.add_parser("updates")

    args = parser.parse_args()
    if args.command == "run":
        payload = self_learning_engine.run(limit=args.limit, reviewer=args.reviewer)
    elif args.command == "dashboard":
        payload = self_learning_engine.dashboard()
    elif args.command == "analytics":
        payload = self_learning_engine.analytics()
    else:
        payload = {"updates": self_learning_engine.list_updates(limit=20)}
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
