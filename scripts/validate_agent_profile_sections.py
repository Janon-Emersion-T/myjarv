import json
import re
from pathlib import Path

from agent_profile_sections import REQUIRED_SECTIONS


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "agents" / "registry.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"

START_MARKER = "<!-- canonical-profile:start -->"
END_MARKER = "<!-- canonical-profile:end -->"


def main():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["agents"]
    failures = []

    for agent in registry:
        path = PROMPTS_DIR / agent["prompt_file"]
        content = path.read_text(encoding="utf-8")

        if START_MARKER not in content or END_MARKER not in content:
            failures.append(f"{agent['name']}: missing canonical profile markers")
            continue

        missing = []
        order = []
        for section in REQUIRED_SECTIONS:
            match = re.search(rf"^## {re.escape(section)}\s*$", content, re.MULTILINE)
            if not match:
                missing.append(section)
            else:
                order.append((section, match.start()))

        if missing:
            failures.append(f"{agent['name']}: missing sections {missing}")
            continue

        starts = [position for _, position in order]
        if starts != sorted(starts):
            failures.append(f"{agent['name']}: sections are out of canonical order")

        if "## Legacy Profile" not in content:
            failures.append(f"{agent['name']}: missing legacy profile section")

    if failures:
        print("Agent profile validation failed:")
        for issue in failures:
            print(f"- {issue}")
        raise SystemExit(1)

    print(f"Validated canonical profile sections for {len(registry)} agents.")


if __name__ == "__main__":
    main()
