from app.agents.router import classify_intent, classify_priority, select_agent, supporting_agents_for_intent
from app.approval_gate import approval_gate
from app.schemas import AgentSummary, TaskCreateRequest


def _to_summary(agent) -> AgentSummary:
    return AgentSummary(
        name=agent.name,
        role=agent.role,
        department=agent.department,
        priority=agent.priority,
        risk_level=agent.risk_level,
        approval_level=agent.approval_level,
        tools=agent.tools,
        authority_scope=agent.authority_scope,
        description=agent.description,
        responsibility=agent.responsibility,
    )


def orchestrate_task(request: TaskCreateRequest) -> dict:
    agent = select_agent(request.message, request.preferred_agent)
    intent_category = classify_intent(request.message)
    selected_agent = _to_summary(agent)
    supporting_agents = [_to_summary(item) for item in supporting_agents_for_intent(intent_category, agent)]
    priority = classify_priority(request.message, agent)
    risk_level, approval_level = approval_gate.classify(
        request.message,
        agent.approval_level,
        request.requested_action,
    )
    status = "pending_approval" if approval_level != "LOW" else "planned"
    reasoning = (
        f"Selected {agent.name} as the primary agent for the {intent_category} intent category. "
        f"Supporting agents: {', '.join(agent.name for agent in supporting_agents) or 'none'}. "
        f"Task priority classified as {priority}, risk as {risk_level}, and approval requirement as {approval_level}."
    )
    return {
        "message": request.message,
        "intent_category": intent_category,
        "preferred_agent": request.preferred_agent,
        "selected_agent": selected_agent.model_dump(),
        "supporting_agents": [agent.model_dump() for agent in supporting_agents],
        "requested_action": request.requested_action,
        "priority": priority,
        "risk_level": risk_level,
        "approval_level": approval_level,
        "status": status,
        "metadata": request.metadata,
        "reasoning": reasoning,
    }
