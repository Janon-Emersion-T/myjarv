from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Agent(BaseModel):
    name: str
    role: str
    department: str
    model_role: Literal["orchestrator", "coder", "fast", "research", "customer_support"]
    prompt_file: str
    profile_path: str
    description: str
    responsibility: str
    priority: int = Field(..., ge=1, le=5)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    approval_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    tools: List[str]
    authority_scope: str


class AgentRegistry(BaseModel):
    agents: List[Agent]


class AgentRunRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent: Optional[str] = None


class AgentRunResponse(BaseModel):
    selected_agent: Agent
    system_prompt: str
    user_message: str
