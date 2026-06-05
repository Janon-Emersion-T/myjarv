from app.agents.schema import Agent
from app.agents.loader import load_agent_prompt
from app.personality import apply_personality


def build_system_prompt(agent: Agent) -> str:
    base_prompt = load_agent_prompt(agent)
    if agent.name == "Jarvis":
        base_prompt = apply_personality(base_prompt)

    return f"""
{base_prompt}

## Jarvis Agent Runtime Rules

Agent Name: {agent.name}
Role: {agent.role}
Department: {agent.department}
Model Role: {agent.model_role}

Core responsibility:
{agent.responsibility}

Rules:
- Stay inside your role unless Jarvis asks for cross-agent support.
- Be practical, direct, and production-focused.
- Do not hallucinate.
- Ask for missing critical information only when execution would be unsafe or impossible.
- For code tasks, provide exact files, exact paths, and complete code.
""".strip()
