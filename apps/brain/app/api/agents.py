from fastapi import APIRouter, HTTPException
from app.agents.registry import list_agents, get_agent_by_name
from app.agents.loader import load_agent_prompt
from app.agents.schema import AgentRunRequest
from app.services.agent_service import prepare_agent_response


router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("")
def get_agents():
    return {"agents": list_agents()}


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