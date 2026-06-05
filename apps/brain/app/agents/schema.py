from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Agent(BaseModel):
    name: str
    slug: str
    display_name: str
    role: str
    position: str
    department: str
    company_department: str
    team: str
    team_display_name: str
    model_role: Literal["orchestrator", "coder", "fast", "research", "customer_support"]
    prompt_file: str
    profile_path: str
    description: str
    responsibility: str
    priority: int = Field(..., ge=1, le=5)
    seniority: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    approval_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    tools: List[str]
    knowledge_domains: List[str]
    memory_permissions: List[str]
    execution_permissions: List[str]
    authority_scope: str
    fallback_agent: str
    collaboration_partners: List[str]
    status: Literal["active", "inactive", "deprecated", "experimental"]
    version: str
    last_updated: str


class RegistryDepartmentGroup(BaseModel):
    slug: str
    display_name: str
    owner: str
    backup_owner: str
    executive_sponsor: str
    teams: List[str]
    agent_count: int
    agents: List[str]


class AgentRegistry(BaseModel):
    version: str
    generated_on: str
    source_company_structure: str
    departments: List[RegistryDepartmentGroup]
    agents: List[Agent]


class AgentRunRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent: Optional[str] = None


class AgentRunResponse(BaseModel):
    selected_agent: Agent
    system_prompt: str
    user_message: str
