import argparse
import json
from pathlib import Path

from validate_agents import validate_registry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def cmd_list(_: argparse.Namespace) -> int:
    registry = load_registry()
    for agent in registry["agents"]:
        print(
            f"{agent['name']:12} "
            f"{agent['company_department']:14} "
            f"{agent['team']:18} "
            f"{agent['role']:30} "
            f"{agent['status']}"
        )
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    validate_registry()
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    registry = load_registry()
    lookup = args.agent.lower()
    for agent in registry["agents"]:
        if agent["name"].lower() == lookup or agent["slug"] == lookup:
            print(json.dumps(agent, indent=2))
            print()
            prompt_path = PROMPTS_DIR / agent["prompt_file"]
            print(prompt_path)
            return 0
    raise SystemExit(f"Agent not found: {args.agent}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jarvis agent registry CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List agents in the registry")
    list_parser.set_defaults(func=cmd_list)

    validate_parser = sub.add_parser("validate", help="Validate the registry")
    validate_parser.set_defaults(func=cmd_validate)

    show_parser = sub.add_parser("show", help="Show one registry entry")
    show_parser.add_argument("agent", help="Agent name or slug")
    show_parser.set_defaults(func=cmd_show)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
