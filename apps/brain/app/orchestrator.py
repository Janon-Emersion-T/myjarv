from datetime import UTC, datetime

from app.agents.registry import get_agent_by_name
from app.routing import routing_engine
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
    route = routing_engine.route(
        message=request.message,
        requested_action=request.requested_action,
        preferred_agent=request.preferred_agent,
        metadata=request.metadata,
    )
    agent = get_agent_by_name(route["selected_agent"])
    selected_agent = _to_summary(agent)
    supporting_agents = [_to_summary(get_agent_by_name(name)) for name in route["supporting_agents"]]
    intent_category = route["intent_category"]
    priority = route["priority"]
    risk_level = route["risk_level"]
    approval_level = route["approval_level"]
    status = "waiting_approval" if approval_level != "LOW" else "routed"
    reasoning = (
        f"Selected {agent.name} as the primary agent for the {intent_category} intent category. "
        f"Supporting agents: {', '.join(agent.name for agent in supporting_agents) or 'none'}. "
        f"Task priority classified as {priority}, risk as {risk_level}, approval requirement as {approval_level}, "
        f"and routing confidence as {route['confidence']:.2f}."
    )
    now = datetime.now(UTC).isoformat()
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
        "routing": route,
        "history": [
            {
                "created_at": now,
                "status": "received",
                "actor": "api",
                "message": "Task received by Jarvis Brain.",
                "payload": {"preferred_agent": request.preferred_agent, "requested_action": request.requested_action},
            },
            {
                "created_at": now,
                "status": "routed",
                "actor": "Jarvis",
                "message": f"Task routed to {agent.name} for {intent_category}.",
                "payload": {
                    "selected_agent": agent.name,
                    "supporting_agents": [item.name for item in supporting_agents],
                    "priority": priority,
                    "risk_level": risk_level,
                    "approval_level": approval_level,
                    "trace_id": route["trace_id"],
                    "confidence": route["confidence"],
                    "strategy": route["execution_strategy"],
                },
            },
        ],
    }
