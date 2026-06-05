from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.agents.prompt_generator import AgentPromptGenerator
from app.services.agent_service import AgentService


router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentAskRequest(BaseModel):
    agent: str
    message: str


@router.get("")
async def get_agents(department: str | None = Query(default=None)):
    service = AgentService()

    if department:
        return {
            "agents": service.list_agents_by_department(department)
        }

    return {
        "agents": service.list_available_agents()
    }


@router.post("/generate-prompts")
async def generate_missing_prompts():
    generator = AgentPromptGenerator()
    return generator.generate_missing_prompts()


@router.post("/ask")
async def ask_agent(request: AgentAskRequest):
    service = AgentService()

    result = await service.ask_agent(
        agent_name=request.agent,
        message=request.message
    )

    return result