#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.routing import routing_engine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Jarvis task routing.")
    parser.add_argument("message", help="Task message to route.")
    parser.add_argument("--requested-action", dest="requested_action")
    parser.add_argument("--preferred-agent", dest="preferred_agent")
    parser.add_argument("--metadata", default="{}", help="JSON metadata for routing context.")
    parser.add_argument("--mode", default="simulation", choices=["simulation", "live", "replay"])
    args = parser.parse_args()

    metadata = json.loads(args.metadata)
    decision = routing_engine.route(
        message=args.message,
        requested_action=args.requested_action,
        preferred_agent=args.preferred_agent,
        metadata=metadata,
        mode=args.mode,
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
