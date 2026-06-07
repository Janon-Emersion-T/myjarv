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

from app.workflow_replacement import workflow_replacement_engine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect workflow replacement state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("catalog")
    subparsers.add_parser("analytics")
    subparsers.add_parser("dashboard")
    args = parser.parse_args()
    if args.command == "catalog":
        payload = workflow_replacement_engine.cli_catalog()
    elif args.command == "analytics":
        payload = workflow_replacement_engine.analytics()
    else:
        payload = workflow_replacement_engine.dashboard()
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
