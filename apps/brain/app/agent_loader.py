from app.agents.loader import load_agent_prompt
from app.agents.registry import get_agent_by_name, get_registry_snapshot, list_agents, list_department_groups


def get_all_agents():
    return list_agents()


def get_registry_data():
    return get_registry_snapshot()


def get_department_groups():
    return list_department_groups()


def get_agent_detail(name: str) -> dict:
    agent = get_agent_by_name(name)
    return {
        "agent": agent,
        "prompt": load_agent_prompt(agent),
    }
