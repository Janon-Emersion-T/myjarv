from app.agents.loader import load_agent_prompt
from app.agents.registry import get_agent_by_name, list_agents


def get_all_agents():
    return list_agents()


def get_agent_detail(name: str) -> dict:
    agent = get_agent_by_name(name)
    return {
        "agent": agent,
        "prompt": load_agent_prompt(agent),
    }
