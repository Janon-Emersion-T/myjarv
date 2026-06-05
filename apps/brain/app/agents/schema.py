from pydantic import BaseModel


class AgentDefinition(BaseModel):
    name: str
    role: str
    department: str
    model_role: str
    prompt_file: str
    description: str
    responsibility: str


class AgentRunRequest(BaseModel):
    message: str
    agent: str | None = None


class AgentRunResponse(BaseModel):
    selected_agent: str
    role: str
    department: str
    prompt: str
    response: str