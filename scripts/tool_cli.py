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

from app.tools.engine import tool_execution_engine  # noqa: E402
from app.tools.registry import tool_registry  # noqa: E402
from app.tools.store import tool_execution_store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and execute Jarvis tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")
    subparsers.add_parser("validate")
    subparsers.add_parser("capabilities")
    subparsers.add_parser("history")

    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("tool_name")
    execute_parser.add_argument("--input", default="{}")
    execute_parser.add_argument("--approved", action="store_true")

    args = parser.parse_args()
    if args.command == "list":
        payload = {"tools": tool_registry.list_tools()}
    elif args.command == "validate":
        payload = tool_registry.validate()
    elif args.command == "capabilities":
        payload = tool_registry.capabilities()
    elif args.command == "history":
        payload = {"executions": tool_execution_store.list(limit=20)}
    else:
        payload = tool_execution_engine.execute(
            tool_name=args.tool_name,
            input_payload=json.loads(args.input),
            actor="tool_cli",
            approved=args.approved,
        )
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
