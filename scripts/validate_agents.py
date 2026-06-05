import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "agents" / "registry.json"
PROMPTS = ROOT / "packages" / "agents" / "prompts"
REQUIRED_FIELDS = {
    "name",
    "role",
    "department",
    "model_role",
    "prompt_file",
    "profile_path",
    "description",
    "responsibility",
    "priority",
    "risk_level",
    "approval_level",
    "tools",
    "authority_scope",
}
VALID_MODEL_ROLES = {"orchestrator", "coder", "fast", "research", "customer_support"}
VALID_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

data = json.loads(REGISTRY.read_text(encoding="utf-8"))
agents = data.get("agents", [])

names = set()
missing_prompts = []
invalid_agents = []

for agent in agents:
    name = agent["name"]
    prompt_file = agent["prompt_file"]
    missing_fields = REQUIRED_FIELDS - set(agent.keys())

    if name.lower() in names:
        print(f"Duplicate agent name: {name}")

    names.add(name.lower())

    if not (PROMPTS / prompt_file).exists():
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

    expected_profile_path = f"packages/agents/prompts/{prompt_file}"
    if agent["profile_path"] != expected_profile_path:
        invalid_agents.append(
            f"{name}: profile_path {agent['profile_path']} does not match {expected_profile_path}"
        )

    if not isinstance(agent["tools"], list) or not agent["tools"]:
        invalid_agents.append(f"{name}: tools must be a non-empty list")

print(f"Total agents in registry: {len(agents)}")
print(f"Total prompt files found: {len(list(PROMPTS.glob('*.md')))}")

if missing_prompts:
    print("Missing prompt files:")
    for file in missing_prompts:
        print(f"- {file}")
    raise SystemExit(1)

if invalid_agents:
    print("Invalid registry entries:")
    for issue in invalid_agents:
        print(f"- {issue}")
    raise SystemExit(1)

print("Agent registry validation passed.")
