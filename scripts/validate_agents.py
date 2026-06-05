import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "agents" / "registry.json"
PROMPTS = ROOT / "packages" / "agents" / "prompts"
README = ROOT / "packages" / "agents" / "README.md"

REQUIRED_TOP_LEVEL = {
    "version",
    "generated_on",
    "source_company_structure",
    "departments",
    "agents",
}

REQUIRED_FIELDS = {
    "name",
    "slug",
    "display_name",
    "role",
    "position",
    "department",
    "company_department",
    "team",
    "team_display_name",
    "model_role",
    "prompt_file",
    "profile_path",
    "description",
    "responsibility",
    "priority",
    "seniority",
    "risk_level",
    "approval_level",
    "tools",
    "knowledge_domains",
    "memory_permissions",
    "execution_permissions",
    "authority_scope",
    "fallback_agent",
    "collaboration_partners",
    "status",
    "version",
    "last_updated",
}

VALID_MODEL_ROLES = {"orchestrator", "coder", "fast", "research", "customer_support"}
VALID_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_STATUSES = {"active", "inactive", "deprecated", "experimental"}


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def validate_registry() -> None:
    data = load_registry()
    agents = data.get("agents", [])
    departments = data.get("departments", [])

    missing_top_level = REQUIRED_TOP_LEVEL - set(data.keys())
    if missing_top_level:
        raise SystemExit(f"Missing top-level registry keys: {sorted(missing_top_level)}")

    names = set()
    slugs = set()
    roles = Counter()
    missing_prompts = []
    invalid_agents = []
    prompt_files = {path.name for path in PROMPTS.glob("*.md")}
    registry_prompt_files = set()

    department_map = {department["slug"]: set(department["agents"]) for department in departments}

    for agent in agents:
        name = agent["name"]
        slug = agent["slug"]
        prompt_file = agent["prompt_file"]
        registry_prompt_files.add(prompt_file)
        missing_fields = REQUIRED_FIELDS - set(agent.keys())

        if name.lower() in names:
            invalid_agents.append(f"{name}: duplicate agent name")
        names.add(name.lower())

        if slug in slugs:
            invalid_agents.append(f"{name}: duplicate slug {slug}")
        slugs.add(slug)

        roles[agent["role"]] += 1

        if prompt_file not in prompt_files:
            missing_prompts.append(prompt_file)

        if missing_fields:
            invalid_agents.append(f"{name}: missing fields {sorted(missing_fields)}")
            continue

        if agent["model_role"] not in VALID_MODEL_ROLES:
            invalid_agents.append(f"{name}: invalid model_role {agent['model_role']}")
        if agent["risk_level"] not in VALID_LEVELS:
            invalid_agents.append(f"{name}: invalid risk_level {agent['risk_level']}")
        if agent["approval_level"] not in VALID_LEVELS:
            invalid_agents.append(f"{name}: invalid approval_level {agent['approval_level']}")
        if agent["status"] not in VALID_STATUSES:
            invalid_agents.append(f"{name}: invalid status {agent['status']}")
        if not isinstance(agent["tools"], list) or not agent["tools"]:
            invalid_agents.append(f"{name}: tools must be a non-empty list")
        if not isinstance(agent["knowledge_domains"], list) or not agent["knowledge_domains"]:
            invalid_agents.append(f"{name}: knowledge_domains must be a non-empty list")
        if not isinstance(agent["memory_permissions"], list) or not agent["memory_permissions"]:
            invalid_agents.append(f"{name}: memory_permissions must be a non-empty list")
        if not isinstance(agent["execution_permissions"], list) or not agent["execution_permissions"]:
            invalid_agents.append(f"{name}: execution_permissions must be a non-empty list")
        if not isinstance(agent["collaboration_partners"], list) or not agent["collaboration_partners"]:
            invalid_agents.append(f"{name}: collaboration_partners must be a non-empty list")

        expected_profile_path = f"packages/agents/prompts/{prompt_file}"
        if agent["profile_path"] != expected_profile_path:
            invalid_agents.append(
                f"{name}: profile_path {agent['profile_path']} does not match {expected_profile_path}"
            )

        if agent["fallback_agent"] == name:
            invalid_agents.append(f"{name}: fallback_agent cannot point to itself")

        if agent["company_department"] not in department_map:
            invalid_agents.append(f"{name}: company_department {agent['company_department']} not found in groups")
        elif name not in department_map[agent["company_department"]]:
            invalid_agents.append(f"{name}: missing from department group {agent['company_department']}")

    orphan_prompts = sorted(prompt_files - registry_prompt_files)
    duplicate_roles = {role: count for role, count in roles.items() if count > 1}

    if not README.exists():
        invalid_agents.append("packages/agents/README.md is missing")

    print(f"Total agents in registry: {len(agents)}")
    print(f"Total prompt files found: {len(prompt_files)}")
    print(f"Department groups: {len(departments)}")

    if missing_prompts:
        print("Missing prompt files:")
        for file in missing_prompts:
            print(f"- {file}")
    if orphan_prompts:
        print("Orphan prompt files:")
        for file in orphan_prompts:
            print(f"- {file}")
    if duplicate_roles:
        print("Duplicate roles:")
        for role, count in sorted(duplicate_roles.items()):
            print(f"- {role}: {count}")
    if invalid_agents:
        print("Invalid registry entries:")
        for issue in invalid_agents:
            print(f"- {issue}")

    if missing_prompts or orphan_prompts or duplicate_roles or invalid_agents:
        raise SystemExit(1)

    print("Agent registry validation passed.")


if __name__ == "__main__":
    validate_registry()
