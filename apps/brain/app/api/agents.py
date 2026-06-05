from fastapi import APIRouter, HTTPException
from app.agents.registry import get_agent_by_name, get_registry_snapshot, list_agents
from app.agents.loader import load_agent_prompt
from app.agents.schema import AgentRunRequest
from app.services.agent_service import prepare_agent_response


router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("")
def get_agents():
    snapshot = get_registry_snapshot()
    return {
        "version": snapshot["version"],
        "generated_on": snapshot["generated_on"],
        "departments": snapshot["departments"],
        "agents": list_agents(),
    }


@router.get("/registry")
def get_registry():
    return get_registry_snapshot()


@router.get("/{name}")
def get_agent(name: str):
    try:
        agent = get_agent_by_name(name)
        return {
            "agent": agent,
            "prompt": load_agent_prompt(agent),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/run")
def run_agent(request: AgentRunRequest):
    try:
        return prepare_agent_response(request.message, request.agent)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
