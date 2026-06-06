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

export type MemoryRecord = {
  id: string;
  scope: string;
  key: string;
  value: string;
  tags: string[];
  source?: string | null;
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
  errors: DashboardErrors | null;
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
  | "settings";
