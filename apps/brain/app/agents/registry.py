import json
from pathlib import Path
from app.agents.schema import Agent, AgentRegistry


ROOT_DIR = Path(__file__).resolve().parents[5]
REGISTRY_PATH = ROOT_DIR / "packages" / "agents" / "registry.json"


def load_registry() -> AgentRegistry:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Agent registry not found: {REGISTRY_PATH}")

    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return AgentRegistry(**data)


def list_agents() -> list[Agent]:
    return load_registry().agents


def get_agent_by_name(name: str) -> Agent:
    lowered = name.lower()

    for agent in list_agents():
        if agent.name.lower() == lowered or agent.role.lower() == lowered:
            return agent

    raise ValueError(f"Agent not found: {name}")