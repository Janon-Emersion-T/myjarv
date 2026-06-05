from app.schemas import AgentExecutionResponse


def build_agent_response(**kwargs) -> AgentExecutionResponse:
    return AgentExecutionResponse(**kwargs)
