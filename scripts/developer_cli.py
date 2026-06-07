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

from app.developer_mode import developer_mode  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect developer mode outputs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan")
    scan.add_argument("--path", default=".")

    health = subparsers.add_parser("health")
    health.add_argument("--path", default=".")

    errors = subparsers.add_parser("errors")
    errors.add_argument("--path", default=".")

    checklist = subparsers.add_parser("checklist")
    checklist.add_argument("--path", default=".")

    plan = subparsers.add_parser("plan")
    plan.add_argument("goal")
    plan.add_argument("--path", default=".")

    args = parser.parse_args()
    if args.command == "scan":
        payload = developer_mode.analyze_repository(args.path)
    elif args.command == "health":
        payload = developer_mode.repository_health(args.path)
    elif args.command == "errors":
        payload = developer_mode.detect_errors(args.path)
    elif args.command == "checklist":
        payload = developer_mode.deployment_checklist(args.path)
    else:
        payload = developer_mode.fix_plan(goal=args.goal, path=args.path)
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
