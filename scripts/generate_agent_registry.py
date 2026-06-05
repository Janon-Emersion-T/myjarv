import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"
STRUCTURE_PATH = ROOT / "packages" / "agents" / "company-structure.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"

VERSION = "2.0.0"
LAST_UPDATED = str(date.today())


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def extract_section(content: str, section: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(section)}\s*$\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def extract_bullets(section_body: str) -> list[str]:
    return [line[2:].strip() for line in section_body.splitlines() if line.strip().startswith("* ")]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_department_groups(structure: dict) -> list[dict]:
    groups = []
    for department in structure["departments"]:
        groups.append(
            {
                "slug": department["slug"],
                "display_name": department["display_name"],
                "owner": department["owner"],
                "backup_owner": department["backup_owner"],
                "executive_sponsor": department["executive_sponsor"],
                "teams": [team["slug"] for team in department["raw_teams"]],
                "agent_count": len(department["agents"]),
                "agents": department["agents"],
            }
        )
    return groups


def build_registry():
    current_registry = load_json(REGISTRY_PATH)
    structure = load_json(STRUCTURE_PATH)
    structure_by_name = {entry["name"]: entry for entry in structure["agent_index"]}
    department_by_slug = {entry["slug"]: entry for entry in structure["departments"]}

    enriched_agents = []
    for agent in current_registry["agents"]:
        prompt_path = PROMPTS_DIR / agent["prompt_file"]
        prompt = prompt_path.read_text(encoding="utf-8")
        structure_entry = structure_by_name[agent["name"]]
        department_entry = department_by_slug[structure_entry["company_department"]]

        knowledge_sources = extract_bullets(extract_section(prompt, "Knowledge Sources"))
        memory_access = extract_bullets(extract_section(prompt, "Memory Access"))
        tool_access_level = extract_section(prompt, "Tool Access Level")
        collaborators = extract_bullets(extract_section(prompt, "Collaborates With"))
        position = extract_section(prompt, "Position")

        execution_permissions = ["plan", "review"]
        if "execution" in tool_access_level.lower():
            execution_permissions.append("execute_with_approval")
        if agent["approval_level"] == "LOW":
            execution_permissions.append("auto_execute_low_risk")

        enriched_agents.append(
            {
                **agent,
                "slug": slugify(agent["name"]),
                "display_name": agent["name"],
                "position": position,
                "company_department": structure_entry["company_department"],
                "team": structure_entry["raw_team"],
                "team_display_name": structure_entry["team_display_name"],
                "seniority": structure_entry["seniority_level"],
                "knowledge_domains": knowledge_sources,
                "memory_permissions": memory_access,
                "execution_permissions": execution_permissions,
                "fallback_agent": structure_entry["backup_agents"][0],
                "collaboration_partners": collaborators,
                "status": structure_entry["status"],
                "version": VERSION,
                "last_updated": LAST_UPDATED,
            }
        )

    registry = {
        "version": VERSION,
        "generated_on": LAST_UPDATED,
        "source_company_structure": str(STRUCTURE_PATH.relative_to(ROOT)),
        "departments": build_department_groups(structure),
        "agents": enriched_agents,
    }
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_registry()
