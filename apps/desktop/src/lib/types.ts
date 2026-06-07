export type Agent = {
  name: string;
  department: string;
  company_department?: string;
  role: string;
  approval_level?: string;
  risk_level?: string;
  tools?: string[];
  description?: string;
};

export type Task = {
  id: string;
  message: string;
  status: string;
  priority: number;
  risk_level: string;
  approval_level: string;
  selected_agent: { name: string; role?: string };
  routing?: { project_context?: string; trace_id?: string; execution_strategy?: string };
  collaboration?: CollaborationSession;
  last_error?: string | null;
};

export type TaskCreatePayload = {
  message: string;
  preferred_agent?: string;
  requested_action?: string;
  metadata?: Record<string, unknown>;
};

export type MemoryRecord = {
  id: string;
  scope: string;
  key: string;
  value: string;
  tags: string[];
  source?: string | null;
};

export type MemoryScope = "company" | "client" | "project" | "decision" | "mistake" | "agent" | "user_preference";

export type MemoryCreatePayload = {
  scope: MemoryScope;
  key: string;
  value: string;
  tags: string[];
  source?: string;
  task_id?: string;
};

export type KnowledgeRecord = {
  path: string;
  category: string;
  content: string;
};

export type LogRecord = {
  timestamp: string;
  level: string;
  event: string;
  message: string;
  payload: Record<string, unknown>;
};

export type DashboardSummary = {
  generated_at: string;
  health: string;
  agents_total: number;
  tasks_total: number;
  tasks_waiting_approval: number;
  tasks_failed: number;
  logs_total: number;
  error_logs: number;
  memory_total: number;
  status_counts: Record<string, number>;
  department_counts: Record<string, number>;
  routing: Record<string, unknown>;
  collaboration: Record<string, unknown>;
};

export type DashboardReport = {
  summary: DashboardSummary;
  task_reports: Record<string, Record<string, number>>;
  collaboration_report: Record<string, unknown>;
  routing_report: Record<string, unknown>;
};

export type DashboardPipeline = {
  stages: Record<string, Task[]>;
  counts: Record<string, number>;
};

export type ProjectRecord = {
  id: string;
  name: string;
  client_name: string;
  category: string;
  methodology: string;
  owner: string;
  status: string;
  deadline?: string | null;
  health_score: number;
  risk_score: number;
  blockers: Array<{ id: string; title: string; severity: string; status: string }>;
  milestones: Array<{ id: string; title: string; status: string; due_date?: string | null }>;
};

export type ProjectDashboard = {
  projects: ProjectRecord[];
  analytics: Record<string, unknown> & {
    projects_total?: number;
    open_blockers?: number;
    average_health_score?: number;
  };
  blockers: Array<{ project_id: string; project_name: string; title: string; severity: string; status: string }>;
  timeline: Array<{ project_id: string; project_name: string; deadline?: string | null; health_score: number }>;
};

export type DashboardErrors = {
  failed_tasks: Task[];
  error_logs: LogRecord[];
  warning_logs: LogRecord[];
};

export type SearchResults = {
  agents: Agent[];
  tasks: Task[];
  memory: MemoryRecord[];
  logs: LogRecord[];
};

export type CollaborationEvent = {
  id: string;
  event_type: string;
  actor: string;
  stage: string;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type CollaborationMessage = {
  id: string;
  sender: string;
  recipient: string;
  kind: string;
  content: string;
  related_stage?: string | null;
  created_at: string;
};

export type AgentContribution = {
  id: string;
  agent: string;
  role: string;
  stage: string;
  status: string;
  summary: string;
  deliverables: string[];
  quality_score: number;
  references: string[];
  fallback_used?: string | null;
};

export type CollaborationSession = {
  id: string;
  task_id: string;
  mode: string;
  strategy: string;
  coordinator: string;
  primary_agent: string;
  participants: string[];
  reviewers: string[];
  fallback_agents: string[];
  approval_required: string;
  status: string;
  shared_workspace: Record<string, unknown>;
  analytics: Record<string, unknown>;
  messages: CollaborationMessage[];
  events: CollaborationEvent[];
  contributions: AgentContribution[];
};

export type SettingsRecord = {
  app_name: string;
  app_env: string;
  database_backend: string;
  postgres_configured: boolean;
  production_lock_mode: boolean;
};

export type ToolRecord = {
  name: string;
  description: string;
  risk_level: string;
  approval_requirement: string;
  mode: string;
};

export type VoiceSession = {
  id: string;
  mode: string;
  locale: string;
  speaker_id: string;
  speaker_authorized: boolean;
  wake_word_detected: boolean;
  wake_word: string;
  transport: string;
  stt_provider: string;
  tts_provider: string;
  noise_reduction: string;
  input_device?: string | null;
  output_device?: string | null;
  status: string;
  last_transcript?: string | null;
  last_response_text?: string | null;
  analytics: Record<string, unknown>;
  interactions?: VoiceInteraction[];
  events?: VoiceEvent[];
};

export type VoiceInteraction = {
  id: string;
  input_text: string;
  intent: string;
  confidence: number;
  risk_level: string;
  approval_level: string;
  response_text: string;
  interruption_handled: boolean;
  created_at: string;
};

export type VoiceEvent = {
  id: string;
  event_type: string;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type VoiceDeviceGroup = {
  inputs: Array<Record<string, unknown>>;
  outputs: Array<Record<string, unknown>>;
};

export type VoiceDashboard = {
  config: Record<string, unknown>;
  devices: VoiceDeviceGroup;
  analytics: Record<string, unknown>;
  sessions: VoiceSession[];
  modes: string[];
};

export type NotificationItem = {
  id: string;
  title: string;
  body: string;
  severity: "info" | "warning" | "critical";
};

export type DesktopState = {
  summary: DashboardSummary | null;
  agents: Agent[];
  tasks: Task[];
  approvals: Task[];
  memory: MemoryRecord[];
  knowledge: KnowledgeRecord[];
  logs: LogRecord[];
  settings: SettingsRecord | null;
  tools: ToolRecord[];
  routingAnalytics: Record<string, unknown> | null;
  collaborationAnalytics: Record<string, unknown> | null;
  collaborationSessions: CollaborationSession[];
  reports: DashboardReport | null;
  pipeline: DashboardPipeline | null;
  projectDashboard: ProjectDashboard | null;
  errors: DashboardErrors | null;
  voiceDashboard: VoiceDashboard | null;
  voiceSessions: VoiceSession[];
  searchResults: SearchResults | null;
  notifications: NotificationItem[];
  offline: boolean;
  websocketConnected: boolean;
  lastSync: string | null;
};

export type NavKey =
  | "dashboard"
  | "agents"
  | "tasks"
  | "approvals"
  | "projects"
  | "memory"
  | "knowledge"
  | "logs"
  | "reports"
  | "collaboration"
  | "voice"
  | "settings";
