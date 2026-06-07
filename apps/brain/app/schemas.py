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


class DeveloperFixPlanRequest(BaseModel):
    goal: str = Field(..., min_length=1)
    path: str | None = None
    constraints: list[str] = Field(default_factory=list)
    preferred_files: list[str] = Field(default_factory=list)


class DeveloperChangelogRequest(BaseModel):
    title: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    changes: list[str] = Field(default_factory=list)
    version: str | None = None


class BusinessLeadCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    service_interest: str = Field(..., min_length=1)
    budget: float | None = Field(default=None, ge=0)
    channel: str = Field(default="website", min_length=1)
    notes: str | None = None


class BusinessProposalCreateRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    scope: str = Field(..., min_length=1)
    timeline_weeks: int = Field(..., ge=1)
    budget_estimate: float = Field(..., ge=0)
    lead_id: str | None = None


class BusinessQuotationCreateRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    labor_hours: float = Field(..., ge=0)
    hourly_rate: float = Field(..., ge=0)
    expenses: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)


class BusinessFollowupCreateRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    context: str = Field(..., min_length=1)
    days_since_last_touch: int = Field(default=0, ge=0)


class BusinessInvoiceReminderRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    invoice_number: str = Field(..., min_length=1)
    amount_due: float = Field(..., ge=0)
    days_overdue: int = Field(..., ge=0)


class BusinessOnboardingRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    service_line: str = Field(..., min_length=1)


class BusinessCompetitorAnalysisRequest(BaseModel):
    competitor_name: str = Field(..., min_length=1)
    website: str = Field(..., min_length=1)
    focus: str = Field(..., min_length=1)


class BusinessBlogDraftRequest(BaseModel):
    title: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    call_to_action: str = Field(..., min_length=1)


class BusinessMonthlyReportRequest(BaseModel):
    month: str = Field(..., min_length=1)


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


class CollaborationMessage(BaseModel):
    id: str
    session_id: str
    task_id: str
    sender: str
    recipient: str
    kind: Literal["instruction", "handoff", "review", "approval", "escalation", "memory_ref", "knowledge_ref"]
    content: str
    related_stage: str | None = None
    created_at: datetime


class CollaborationEvent(BaseModel):
    id: str
    session_id: str
    task_id: str
    event_type: str
    actor: str
    stage: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentContribution(BaseModel):
    id: str
    session_id: str
    task_id: str
    agent: str
    role: str
    stage: str
    status: Literal["planned", "in_progress", "completed", "blocked", "failed", "reviewed"]
    summary: str
    deliverables: list[str] = Field(default_factory=list)
    quality_score: int = Field(..., ge=0, le=100)
    references: list[str] = Field(default_factory=list)
    fallback_used: str | None = None
    created_at: datetime
    updated_at: datetime


class CollaborationSession(BaseModel):
    id: str
    task_id: str
    mode: Literal["simulation", "execution", "replay"]
    strategy: Literal["single", "sequential", "parallel"]
    coordinator: str
    primary_agent: str
    participants: list[str] = Field(default_factory=list)
    reviewers: list[str] = Field(default_factory=list)
    fallback_agents: list[str] = Field(default_factory=list)
    approval_required: RiskLevel
    status: Literal["planned", "running", "completed", "blocked", "failed"]
    shared_workspace: dict[str, Any] = Field(default_factory=dict)
    analytics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AgentExecutionResponse(BaseModel):
    primary_agent: str
    collaborators: list[str] = Field(default_factory=list)
    collaboration_session_id: str | None = None
    collaboration_strategy: Literal["single", "sequential", "parallel"] | None = None
    contributions: list[AgentContribution] = Field(default_factory=list)
    contribution_count: int = 0
    collaboration_timeline: list[CollaborationEvent] = Field(default_factory=list)
    review_chain_results: list[str] = Field(default_factory=list)
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
    channel: Literal["dashboard", "api", "cli", "mobile", "email", "whatsapp", "voice"] = "dashboard"
    reviewer_role: Literal["operator", "manager", "director", "executive"] = "manager"
    department: str | None = None
    approval_token: str | None = None
    signature: str | None = None
    delegated_by: str | None = None
    emergency_override: bool = False
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    written_document: dict[str, Any] | None = None


class ApprovalRevokeRequest(BaseModel):
    actor: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ApprovalRollbackRequest(BaseModel):
    actor: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ApprovalSimulationRequest(ApprovalDecisionRequest):
    decision: Literal["approved", "rejected"] = "approved"


class ApprovalEmergencyShutdownRequest(BaseModel):
    active: bool
    actor: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ApprovalRecord(BaseModel):
    id: str
    task_id: str
    decision: Literal["approved", "rejected"]
    reviewer: str
    notes: str | None = None
    channel: str = "dashboard"
    reviewer_role: str = "manager"
    department: str | None = None
    delegated_by: str | None = None
    written_document: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    signature: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    suspicious_flags: list[str] = Field(default_factory=list)
    chain_step: int = 1
    stage_label: str = "stage_1_of_1"
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    revoked_reason: str | None = None
    created_at: datetime


class MemoryCreateRequest(BaseModel):
    scope: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    task_id: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    access_level: Literal["private", "team", "department", "executive"] = "team"
    sensitivity: Literal["normal", "restricted", "secret"] = "normal"
    department: str | None = None
    expires_at: str | None = None
    encrypted: bool | None = None
    status: Literal["active", "archived", "draft"] = "active"


class MemoryRecord(BaseModel):
    id: str
    scope: str
    key: str
    value: str
    tags: list[str]
    source: str | None = None
    task_id: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    access_level: str = "team"
    sensitivity: str = "normal"
    department: str | None = None
    status: str = "active"
    expires_at: str | None = None
    encrypted: bool = False
    created_at: datetime
    updated_at: datetime


class MemoryImportRequest(BaseModel):
    records: list[MemoryCreateRequest] = Field(default_factory=list)
    merge: bool = True


class MemorySnapshotRequest(BaseModel):
    label: str = Field(default="manual", min_length=1)


class KnowledgeRecord(BaseModel):
    path: str
    category: str
    title: str | None = None
    summary: str | None = None
    content: str
    tags: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    trusted: bool = False
    verified: bool = False
    version: str | None = None
    last_reviewed: str | None = None
    approval_status: str | None = None
    domain: str | None = None
    department: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    status: str | None = None
    outdated: bool = False
    source_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="Jarvis", min_length=1)
    agent_name: str | None = None
    task_id: str | None = None
    approved: bool = False
    async_mode: bool = False


class ToolWorkflowStep(BaseModel):
    tool_name: str = Field(..., min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    agent_name: str | None = None
    task_id: str | None = None
    approved: bool = False
    async_mode: bool = False


class ToolWorkflowRequest(BaseModel):
    actor: str = Field(default="Jarvis", min_length=1)
    approved: bool = False
    steps: list[ToolWorkflowStep] = Field(default_factory=list)


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


class VoiceSessionCreateRequest(BaseModel):
    mode: Literal["command", "conversation", "desktop_assistant", "emergency"]
    text: str | None = None
    locale: str = "en"
    speaker_id: str = "janon"
    device_input: str | None = None
    device_output: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VoiceCommandRequest(BaseModel):
    text: str = Field(..., min_length=1)
    requested_action: str | None = None
    locale: str = "en"
    speaker_id: str = "janon"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VoiceDeviceRecord(BaseModel):
    id: str
    kind: Literal["microphone", "speaker"]
    label: str
    is_default: bool = False
    is_available: bool = True


class VoiceInteractionRecord(BaseModel):
    id: str
    session_id: str
    speaker_id: str
    input_text: str
    normalized_text: str
    detected_mode: str
    intent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    approval_level: RiskLevel
    response_text: str
    interruption_handled: bool = False
    created_at: datetime


class VoiceSessionRecord(BaseModel):
    id: str
    mode: Literal["command", "conversation", "desktop_assistant", "emergency"]
    locale: str
    speaker_id: str
    speaker_authorized: bool
    wake_word_detected: bool
    wake_word: str
    transport: str
    stt_provider: str
    tts_provider: str
    noise_reduction: str
    input_device: str | None = None
    output_device: str | None = None
    status: Literal["planned", "listening", "responding", "interrupted", "completed", "blocked"]
    current_task_id: str | None = None
    last_transcript: str | None = None
    last_response_text: str | None = None
    conversation_memory: list[str] = Field(default_factory=list)
    analytics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AuthLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    mfa_code: str | None = None


class AuthLogoutRequest(BaseModel):
    token: str = Field(..., min_length=1)


class AuthMfaVerifyRequest(BaseModel):
    username: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=12)


class ApiKeyCreateRequest(BaseModel):
    owner: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    role_scope: str = Field(default="viewer", min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)


class SecretCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    provider: str = Field(default="local_vault", min_length=1)


class BackupCreateRequest(BaseModel):
    label: str = Field(default="manual", min_length=1)


class BackupRestoreRequest(BaseModel):
    backup_id: str = Field(..., min_length=1)


class ScanRunRequest(BaseModel):
    scan_type: str = Field(default="full", min_length=1)


class IncidentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    details: str = Field(..., min_length=1)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"


class LockdownRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class OfflineModeRequest(BaseModel):
    enabled: bool
    reason: str = Field(..., min_length=1)
