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

from app.knowledge.loader import knowledge_loader  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and verify Jarvis knowledge.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--category")
    list_parser.add_argument("--limit", type=int, default=20)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--category")
    search_parser.add_argument("--limit", type=int, default=10)

    subparsers.add_parser("analytics")
    subparsers.add_parser("validate")
    subparsers.add_parser("gaps")
    subparsers.add_parser("reindex")

    args = parser.parse_args()
    if args.command == "list":
        payload = {"knowledge": knowledge_loader.list_entries(category=args.category)[: args.limit]}
    elif args.command == "search":
        payload = {"knowledge": knowledge_loader.search(query=args.query, category=args.category, limit=args.limit, semantic=True)}
    elif args.command == "analytics":
        payload = knowledge_loader.analytics()
    elif args.command == "validate":
        payload = knowledge_loader.validate()
    elif args.command == "gaps":
        payload = knowledge_loader.missing_knowledge()
    else:
        payload = knowledge_loader.reindex()
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
