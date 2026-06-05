import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_PATH = ROOT / "packages" / "agents" / "company-structure.json"
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"
DOC_PATH = ROOT / "docs" / "company-structure.md"

REQUIRED_TOP_LEVEL = {
    "version",
    "generated_on",
    "source_registry",
    "naming_convention",
    "seniority_levels",
    "authority_levels",
    "executive_command_structure",
    "department_ownership_map",
    "duplicate_resolution",
    "departments",
    "agent_index",
    "registry_names",
}

REQUIRED_DEPARTMENT_FIELDS = {
    "slug",
    "display_name",
    "owner",
    "backup_owner",
    "executive_sponsor",
    "mission",
    "raw_teams",
    "primary_kpis",
    "forbidden_actions",
    "output_templates",
    "responsibility_boundaries",
    "collaboration_rules",
    "escalation_chain",
    "agents",
}

REQUIRED_AGENT_FIELDS = {
    "name",
    "role",
    "company_department",
    "raw_team",
    "team_display_name",
    "reports_to",
    "department_owner",
    "backup_agents",
    "seniority_level",
    "authority_level",
    "routing_role",
    "status",
}


def fail(message: str):
    raise SystemExit(message)


def main():
    if not STRUCTURE_PATH.exists():
        fail("Missing packages/agents/company-structure.json")
    if not DOC_PATH.exists():
        fail("Missing docs/company-structure.md")

    structure = json.loads(STRUCTURE_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["agents"]
    registry_names = {agent["name"] for agent in registry}
    registry_departments = {agent["department"] for agent in registry}

    missing_top = REQUIRED_TOP_LEVEL - set(structure.keys())
    if missing_top:
        fail(f"Missing top-level keys: {sorted(missing_top)}")

    departments = structure["departments"]
    agent_index = structure["agent_index"]
    if len(agent_index) != len(registry):
        fail(f"Agent index count {len(agent_index)} does not match registry count {len(registry)}")

    listed_names = [agent["name"] for agent in agent_index]
    if len(set(listed_names)) != len(listed_names):
        fail("Duplicate agent names found in company structure agent_index")

    missing_registry = registry_names - set(listed_names)
    extra_names = set(listed_names) - registry_names
    if missing_registry:
        fail(f"Registry agents missing from company structure: {sorted(missing_registry)}")
    if extra_names:
        fail(f"Unknown agents in company structure: {sorted(extra_names)}")

    all_team_slugs = set()
    department_slugs = set()
    for department in departments:
        missing_fields = REQUIRED_DEPARTMENT_FIELDS - set(department.keys())
        if missing_fields:
            fail(f"Department {department.get('display_name', '<unknown>')} missing fields {sorted(missing_fields)}")
        department_slugs.add(department["slug"])
        for required_list in ("primary_kpis", "forbidden_actions", "output_templates", "collaboration_rules", "escalation_chain", "agents"):
            if not department[required_list]:
                fail(f"Department {department['display_name']} has empty {required_list}")
        for team in department["raw_teams"]:
            all_team_slugs.add(team["slug"])

    if registry_departments != all_team_slugs:
        fail(
            "Raw team coverage mismatch between registry and company structure: "
            f"missing={sorted(registry_departments - all_team_slugs)} extra={sorted(all_team_slugs - registry_departments)}"
        )

    valid_seniority = set(structure["seniority_levels"])
    valid_authority = set(structure["authority_levels"])

    name_to_department = {}
    design_roles = {
        "Uma": "creative_direction",
        "Figma": "design_systems",
        "Nova": "branding",
        "Mystique": "graphic_design",
        "Quicksilver": "video",
    }

    for agent in agent_index:
        missing_fields = REQUIRED_AGENT_FIELDS - set(agent.keys())
        if missing_fields:
            fail(f"Agent {agent.get('name', '<unknown>')} missing fields {sorted(missing_fields)}")
        if agent["seniority_level"] not in valid_seniority:
            fail(f"Invalid seniority level for {agent['name']}: {agent['seniority_level']}")
        if agent["authority_level"] not in valid_authority:
            fail(f"Invalid authority level for {agent['name']}: {agent['authority_level']}")
        if not agent["backup_agents"]:
            fail(f"Agent {agent['name']} must have at least one backup agent")
        if agent["reports_to"] not in registry_names and agent["reports_to"] != "Janon":
            fail(f"Agent {agent['name']} reports to unknown principal {agent['reports_to']}")
        name_to_department[agent["name"]] = agent["company_department"]

    if {name for name in design_roles if name_to_department.get(name) == "design"} != set(design_roles):
        fail("Design department coverage is incomplete for UI/UX, brand, graphic, or video roles")

    unresolved = structure["duplicate_resolution"]["unresolved_duplicates"]
    if unresolved:
        fail(f"Unresolved duplicate roles remain: {unresolved}")

    if "Department To Agent Matrix" not in DOC_PATH.read_text(encoding="utf-8"):
        fail("docs/company-structure.md is missing the department matrix section")

    print(f"Validated company structure for {len(agent_index)} agents across {len(departments)} company departments.")


if __name__ == "__main__":
    main()
