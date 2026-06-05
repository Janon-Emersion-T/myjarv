from pydantic import BaseModel, Field
from typing import List, Optional


class Agent(BaseModel):
    name: str
    role: str
    department: str
    model_role: str
    prompt_file: str
    description: str
    responsibility: str


class AgentRegistry(BaseModel):
    agents: List[Agent]


class AgentRunRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent: Optional[str] = None


class AgentRunResponse(BaseModel):
    selected_agent: Agent
    system_prompt: str
    user_message: str