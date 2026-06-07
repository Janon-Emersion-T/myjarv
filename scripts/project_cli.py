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

from app.project_manager import project_manager  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect project manager state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    subparsers.add_parser("analytics")
    dashboard = subparsers.add_parser("dashboard")
    dashboard.add_argument("--compact", action="store_true")

    args = parser.parse_args()
    if args.command == "list":
        payload = {"projects": project_manager.list_projects()}
    elif args.command == "analytics":
        payload = project_manager.analytics()
    else:
        payload = project_manager.dashboard()
        if args.compact:
            payload["projects"] = payload["projects"][:5]
            payload["blockers"] = payload["blockers"][:5]
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
