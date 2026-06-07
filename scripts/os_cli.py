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

from app.jarvis_os import jarvis_os  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Jarvis operating-system state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("dashboard")
    subparsers.add_parser("modules")
    subparsers.add_parser("assistants")
    report = subparsers.add_parser("report")
    report.add_argument("report_type", choices=["daily_ceo", "weekly_strategy", "monthly_business"])

    args = parser.parse_args()
    if args.command == "dashboard":
        payload = jarvis_os.dashboard()
    elif args.command == "modules":
        payload = {"modules": jarvis_os.modules()}
    elif args.command == "assistants":
        payload = {"assistants": jarvis_os.assistants()}
    else:
        payload = jarvis_os.report(args.report_type)
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
