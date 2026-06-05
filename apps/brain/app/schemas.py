from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
TaskStatus = Literal["queued", "planned", "pending_approval", "approved", "rejected", "blocked"]
IntentCategory = Literal[
    "development",
    "marketing",
    "finance",
    "legal",
    "operations",
    "support",
    "research",
    "creative",
    "infrastructure",
    "general",
]


class AgentSummary(BaseModel):
    name: str
    role: str
    department: str
    priority: int
    risk_level: RiskLevel
    approval_level: RiskLevel
    tools: list[str]
    authority_scope: str
    description: str
    responsibility: str


class TaskCreateRequest(BaseModel):
    message: str = Field(..., min_length=1)
    preferred_agent: str | None = None
    requested_action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskRecord(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    message: str
    intent_category: IntentCategory
    preferred_agent: str | None = None
    selected_agent: AgentSummary
    supporting_agents: list[AgentSummary] = Field(default_factory=list)
    requested_action: str | None = None
    priority: int = Field(..., ge=1, le=5)
    risk_level: RiskLevel
    approval_level: RiskLevel
    status: TaskStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    reasoning: str


class ApprovalDecisionRequest(BaseModel):
    reviewer: str = Field(..., min_length=1)
    notes: str | None = None


class ApprovalRecord(BaseModel):
    id: str
    task_id: str
    decision: Literal["approved", "rejected"]
    reviewer: str
    notes: str | None = None
    created_at: datetime


class MemoryCreateRequest(BaseModel):
    scope: Literal[
        "company",
        "client",
        "project",
        "decision",
        "mistake",
        "agent",
        "user_preference",
    ]
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    task_id: str | None = None


class MemoryRecord(BaseModel):
    id: str
    scope: str
    key: str
    value: str
    tags: list[str]
    source: str | None = None
    task_id: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeRecord(BaseModel):
    path: str
    category: str
    content: str


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    risk_level: RiskLevel
    approval_requirement: RiskLevel
    mode: Literal["plan", "read", "write"]


class LogRecord(BaseModel):
    timestamp: datetime
    level: str
    event: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
