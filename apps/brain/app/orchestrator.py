from app.agents.router import select_agent
from app.approval_gate import approval_gate
from app.schemas import AgentSummary, TaskCreateRequest


def orchestrate_task(request: TaskCreateRequest) -> dict:
    agent = select_agent(request.message, request.preferred_agent)
    selected_agent = AgentSummary(
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
    risk_level, approval_level = approval_gate.classify(
        request.message,
        agent.approval_level,
        request.requested_action,
    )
    status = "pending_approval" if approval_level != "LOW" else "queued"
    reasoning = (
        f"Selected {agent.name} based on the request content and registry metadata. "
        f"Task classified as risk {risk_level} with approval requirement {approval_level}."
    )
    return {
        "message": request.message,
        "preferred_agent": request.preferred_agent,
        "selected_agent": selected_agent.model_dump(),
        "requested_action": request.requested_action,
        "risk_level": risk_level,
        "approval_level": approval_level,
        "status": status,
        "metadata": request.metadata,
        "reasoning": reasoning,
    }
