import json
import re
from pathlib import Path

from agent_profile_sections import REQUIRED_SECTIONS


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "agents" / "registry.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"

LEGACY_HINTS = {
    "Position": [r"\*\*Role:\*\*", r"## Identity", r"# Agent Name"],
    "Department": [r"\*\*Department:\*\*", r"## Identity"],
    "Reports To": [r"reports to", r"direct executive coordination", r"collaborates with:"],
    "Collaborates With": [r"works closely with:", r"collaborates closely with:", r"direct executive coordination"],
    "Mission": [r"## Mission", r"# Core Mission", r"# Purpose"],
    "Responsibilities": [r"## Responsibilities", r"# Primary Responsibilities"],
    "Skills": [r"## Skills", r"specializes in", r"understands:"],
    "Tools": [r"## Tools"],
    "Knowledge Sources": [r"knowledge", r"docs/", r"data/knowledge"],
    "Memory Access": [r"memory", r"decision memory", r"client memory"],
    "Tool Access Level": [r"approval", r"authority", r"execution"],
    "Inputs": [r"## Inputs"],
    "Input Validation Rules": [r"validation", r"before proceeding", r"check for missing"],
    "Outputs": [r"## Outputs", r"# Output Formats", r"# OUTPUT EXAMPLES"],
    "Output Quality Checklist": [r"quality", r"review", r"output examples"],
    "Review Checklist": [r"review", r"checklist", r"verify"],
    "Decision Authority": [r"## Decision Authority", r"# Executive Authority", r"# Decision Philosophy"],
    "Approval Level": [r"approval", r"ceiling", r"level"],
    "Risk Level": [r"risk", r"unsafe", r"sensitive"],
    "Escalation Rules": [r"## Escalation Rules", r"works closely with:", r"collaborates closely with:"],
    "Escalation Message Template": [r"escalate", r"blocked", r"next step"],
    "Failure Response": [r"failure", r"blocked", r"missing"],
    "Forbidden Actions": [r"## Forbidden Actions", r"must NEVER", r"You must NOT:"],
    "Common Mistakes To Avoid": [r"mistakes", r"avoid", r"do not"],
    "Performance Metrics": [r"kpis", r"performance", r"metrics"],
    "Example Tasks": [r"## Example Tasks", r"# OUTPUT EXAMPLES"],
    "Example Good Output": [r"good output", r"output examples", r"status:"],
    "Example Bad Output": [r"bad output", r"must NEVER", r"do not"],
    "Version": [r"version"],
    "Last Updated": [r"last updated", r"updated"],
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
