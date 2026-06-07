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

from app.memory import memory_store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Jarvis memory records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--scope")
    list_parser.add_argument("--limit", type=int, default=20)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--scope")
    search_parser.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("analytics")

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("--label", default="cli")

    args = parser.parse_args()
    if args.command == "list":
        payload = {"memory": memory_store.list(scope=args.scope, limit=args.limit)}
    elif args.command == "search":
        payload = {"memory": memory_store.search(query=args.query, scope=args.scope, limit=args.limit, semantic=True)}
    elif args.command == "analytics":
        payload = memory_store.analytics()
    else:
        payload = memory_store.create_snapshot(args.label)
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
