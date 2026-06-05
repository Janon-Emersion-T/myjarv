import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "agents" / "registry.json"
PROMPTS = ROOT / "packages" / "agents" / "prompts"

data = json.loads(REGISTRY.read_text(encoding="utf-8"))
agents = data.get("agents", [])

names = set()
missing_prompts = []

for agent in agents:
    name = agent["name"]
    prompt_file = agent["prompt_file"]

    if name.lower() in names:
        print(f"Duplicate agent name: {name}")

    names.add(name.lower())

    if not (PROMPTS / prompt_file).exists():
        missing_prompts.append(prompt_file)

print(f"Total agents in registry: {len(agents)}")
print(f"Total prompt files found: {len(list(PROMPTS.glob('*.md')))}")

if missing_prompts:
    print("Missing prompt files:")
    for file in missing_prompts:
        print(f"- {file}")
    raise SystemExit(1)

print("Agent registry validation passed.")