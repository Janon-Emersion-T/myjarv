from app.agents.router import select_agent
from app.agents.prompt_generator import build_system_prompt
from app.agents.schema import AgentRunResponse


def prepare_agent_response(message: str, preferred_agent: str | None = None) -> AgentRunResponse:
    agent = select_agent(message, preferred_agent)
    system_prompt = build_system_prompt(agent)

    return AgentRunResponse(
        selected_agent=agent,
        system_prompt=system_prompt,
        user_message=message,
    )