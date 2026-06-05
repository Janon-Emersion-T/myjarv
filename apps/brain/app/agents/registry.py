import json
from pathlib import Path
from app.agents.schema import Agent, AgentRegistry, RegistryDepartmentGroup


ROOT_DIR = Path(__file__).resolve().parents[4]
REGISTRY_PATH = ROOT_DIR / "packages" / "agents" / "registry.json"
LEGACY_AGENT_ALIASES = {
    "policy": "Hill",
    "docu": "Lois",
    "happy": "Cisco",
    "api": "Fury",
    "scheduler": "Tempus",
    "data": "Cypher",
    "prompt": "Wanda",
    "model": "Strange",
    "pos": "Gambit",
    "erp": "Forge",
    "crm": "Mantis",
    "email": "Raven",
    "voice": "Canary",
    "domain": "Constantine",
    "git": "Bishop",
    "image": "Mystique",
    "video": "Quicksilver",
    "recruiter": "Moira",
    "admin": "Coulson",
}


def load_registry() -> AgentRegistry:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Agent registry not found: {REGISTRY_PATH}")

    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return AgentRegistry(**data)


def list_agents() -> list[Agent]:
    return load_registry().agents


def list_department_groups() -> list[RegistryDepartmentGroup]:
    return load_registry().departments


def get_registry_snapshot() -> dict:
    registry = load_registry()
    return registry.model_dump()


def get_agent_by_name(name: str) -> Agent:
    lowered = name.lower()
    resolved = LEGACY_AGENT_ALIASES.get(lowered, name)
    resolved_lowered = resolved.lower()

    for agent in list_agents():
        if (
            agent.name.lower() == resolved_lowered
            or agent.role.lower() == resolved_lowered
            or agent.slug == resolved_lowered
        ):
            return agent

    raise ValueError(f"Agent not found: {name}")
