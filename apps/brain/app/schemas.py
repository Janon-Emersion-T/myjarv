from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
TaskStatus = Literal[
    "received",
    "routed",
    "waiting_approval",
    "approved",
    "rejected",
    "executing",
    "completed",
    "failed",
    "blocked",
]
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


class TaskExecutionRequest(BaseModel):
    executor: str = Field(default="Jarvis", min_length=1)
    force_retry: bool = False


class RoutingSimulationRequest(BaseModel):
    message: str = Field(..., min_length=1)
    preferred_agent: str | None = None
    requested_action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskReassignmentRequest(BaseModel):
    reviewer: str = Field(..., min_length=1)
    agent: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class RouteSubtask(BaseModel):
    title: str
    assigned_agent: str
    strategy: Literal["single", "sequential", "parallel"]
    depends_on: list[str] = Field(default_factory=list)
    status: Literal["planned", "blocked", "optional"] = "planned"


class RouteStage(BaseModel):
    stage: str
    assigned_agents: list[str] = Field(default_factory=list)
    strategy: Literal["single", "sequential", "parallel"]
    purpose: str


class RouteCandidate(BaseModel):
    agent: str
    score: float
    reasons: list[str] = Field(default_factory=list)


class RouteDecision(BaseModel):
    trace_id: str
    mode: Literal["live", "simulation", "replay"] = "live"
    intent_category: IntentCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_ambiguous: bool = False
    ambiguity_reason: str | None = None
    selected_agent: str
    supporting_agents: list[str] = Field(default_factory=list)
    fallback_agent: str
    review_chain: list[str] = Field(default_factory=list)
    escalation_chain: list[str] = Field(default_factory=list)
    execution_strategy: Literal["single", "sequential", "parallel"]
    stages: list[RouteStage] = Field(default_factory=list)
    subtasks: list[RouteSubtask] = Field(default_factory=list)
    priority: int = Field(..., ge=1, le=5)
    risk_level: RiskLevel
    approval_level: RiskLevel
    client_context: str | None = None
    project_context: str | None = None
    knowledge_matches: list[str] = Field(default_factory=list)
    memory_scopes: list[str] = Field(default_factory=list)
    tool_matches: list[str] = Field(default_factory=list)
    framework_hints: list[str] = Field(default_factory=list)
    language_hints: list[str] = Field(default_factory=list)
    reviewers_required: list[str] = Field(default_factory=list)
    duplicate_of_task_id: str | None = None
    retry_recommendation: str | None = None
    timeout_seconds: int = 0
    route_map: dict[str, list[str]] = Field(default_factory=dict)
    candidates: list[RouteCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reasoning: str


class TaskHistoryEntry(BaseModel):
    id: str
    task_id: str
    status: TaskStatus
    message: str
    actor: str
    created_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResponse(BaseModel):
    primary_agent: str
    collaborators: list[str] = Field(default_factory=list)
    summary: str
    deliverables: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    escalations: list[str] = Field(default_factory=list)
    tool_plans: list[str] = Field(default_factory=list)
    knowledge_used: list[str] = Field(default_factory=list)
    context_notes: list[str] = Field(default_factory=list)
    status: Literal["completed", "needs_approval", "blocked", "failed"]


class ReviewResult(BaseModel):
    reviewer: str
    score: int = Field(..., ge=0, le=100)
    verdict: Literal["approved", "needs_revision", "blocked"]
    findings: list[str] = Field(default_factory=list)
    recommended_status: TaskStatus
    created_at: datetime


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
    routing: RouteDecision | None = None
    history: list[TaskHistoryEntry] = Field(default_factory=list)
    execution_result: AgentExecutionResponse | None = None
    review_result: ReviewResult | None = None
    retry_count: int = 0
    last_error: str | None = None


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
