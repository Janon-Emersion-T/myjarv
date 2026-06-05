import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "agents" / "registry.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"

REQUIRED_SECTIONS = [
    "Position",
    "Department",
    "Mission",
    "Responsibilities",
    "Skills",
    "Tools",
    "Inputs",
    "Outputs",
    "Decision Authority",
    "Escalation Rules",
    "Forbidden Actions",
    "Example Tasks",
]

LEGACY_HINTS = {
    "Position": [r"\*\*Role:\*\*", r"## Identity", r"# Agent Name"],
    "Department": [r"\*\*Department:\*\*", r"## Identity"],
    "Mission": [r"## Mission", r"# Core Mission", r"# Purpose"],
    "Responsibilities": [r"## Responsibilities", r"# Primary Responsibilities"],
    "Skills": [r"## Skills", r"specializes in", r"understands:"],
    "Tools": [r"## Tools"],
    "Inputs": [r"## Inputs"],
    "Outputs": [r"## Outputs", r"# Output Formats", r"# OUTPUT EXAMPLES"],
    "Decision Authority": [r"## Decision Authority", r"# Executive Authority", r"# Decision Philosophy"],
    "Escalation Rules": [r"## Escalation Rules", r"works closely with:", r"collaborates closely with:"],
    "Forbidden Actions": [r"## Forbidden Actions", r"must NEVER", r"You must NOT:"],
    "Example Tasks": [r"## Example Tasks", r"# OUTPUT EXAMPLES"],
}


def has_canonical_section(content: str, section: str) -> bool:
    return re.search(rf"^## {re.escape(section)}\s*$", content, re.MULTILINE) is not None


def has_legacy_hint(content: str, section: str) -> bool:
    hints = LEGACY_HINTS.get(section, [])
    return any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in hints)


def audit_prompt(prompt_path: Path) -> dict[str, list[str]]:
    content = prompt_path.read_text(encoding="utf-8")

    missing_canonical = [section for section in REQUIRED_SECTIONS if not has_canonical_section(content, section)]
    legacy_coverage = [section for section in REQUIRED_SECTIONS if has_legacy_hint(content, section)]

    return {
        "missing_canonical": missing_canonical,
        "legacy_coverage": legacy_coverage,
    }


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    agents = registry.get("agents", [])

    fully_canonical = 0
    partial_coverage = 0

    for agent in agents:
        prompt_path = PROMPTS_DIR / agent["prompt_file"]
        result = audit_prompt(prompt_path)

        if not result["missing_canonical"]:
            fully_canonical += 1

        if len(result["legacy_coverage"]) >= 8:
            partial_coverage += 1

        print(f"{agent['name']} [{agent['prompt_file']}]")
        print(f"  missing canonical: {', '.join(result['missing_canonical']) or 'none'}")
        print(f"  legacy coverage: {len(result['legacy_coverage'])}/{len(REQUIRED_SECTIONS)}")

    print()
    print(f"Total agents audited: {len(agents)}")
    print(f"Fully canonical profiles: {fully_canonical}")
    print(f"Profiles with broad legacy coverage: {partial_coverage}")


if __name__ == "__main__":
    main()
