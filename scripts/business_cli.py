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

from app.business_automation import business_automation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect business automation outputs.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("analytics")
    subparsers.add_parser("leads")
    subparsers.add_parser("proposals")
    report = subparsers.add_parser("monthly-report")
    report.add_argument("month")

    args = parser.parse_args()
    if args.command == "analytics":
        payload = business_automation.analytics()
    elif args.command == "leads":
        payload = {"leads": business_automation.list_leads()}
    elif args.command == "proposals":
        payload = {"proposals": business_automation.list_proposals()}
    else:
        payload = business_automation.create_monthly_report(month=args.month)
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
