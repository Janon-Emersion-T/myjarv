import { useCallback, useEffect, useReducer, useRef, useTransition } from "react";

import { createSocket, getJson, postJson } from "../lib/api";
import type {
  Agent,
  CollaborationSession,
  DashboardErrors,
  DashboardPipeline,
  DashboardReport,
  DashboardSummary,
  DesktopState,
  KnowledgeRecord,
  LogRecord,
  MemoryRecord,
  NotificationItem,
  SearchResults,
  SettingsRecord,
  Task,
  ToolRecord,
} from "../lib/types";

const CACHE_KEY = "jarvis-desktop-cache-v1";

type State = DesktopState & {
  loading: boolean;
  searchQuery: string;
  isPending: boolean;
};

type Action =
  | { type: "hydrate"; payload: Partial<State> }
  | { type: "sync"; payload: Partial<State> }
  | { type: "offline"; payload: boolean }
  | { type: "search"; payload: { query: string; results: SearchResults | null } }
  | { type: "socket"; payload: Partial<State> }
  | { type: "notify"; payload: NotificationItem[] }
  | { type: "pending"; payload: boolean };

const initialState: State = {
  summary: null,
  agents: [],
  tasks: [],
  approvals: [],
  memory: [],
  knowledge: [],
  logs: [],
  settings: null,
  tools: [],
  routingAnalytics: null,
  collaborationAnalytics: null,
  collaborationSessions: [],
  reports: null,
  pipeline: null,
  errors: null,
  searchResults: null,
  notifications: [],
  offline: false,
  websocketConnected: false,
  lastSync: null,
  loading: true,
  searchQuery: "",
  isPending: false,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "hydrate":
    case "sync":
    case "socket":
      return { ...state, ...action.payload, loading: false };
    case "offline":
      return { ...state, offline: action.payload };
    case "search":
      return { ...state, searchQuery: action.payload.query, searchResults: action.payload.results };
    case "notify":
      return { ...state, notifications: action.payload };
    case "pending":
      return { ...state, isPending: action.payload };
    default:
      return state;
  }
}

export function useDesktopState() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [, startTransition] = useTransition();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    hydrate();
    void syncAll();
    const interval = window.setInterval(() => void syncAll(), 15000);
    const onOnline = () => {
      dispatch({ type: "offline", payload: false });
      void syncAll();
    };
    const onOffline = () => dispatch({ type: "offline", payload: true });
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    connectSocket();
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
      socketRef.current?.close();
    };
  }, []);

  function hydrate() {
    const cached = window.localStorage.getItem(CACHE_KEY);
    if (!cached) {
      return;
    }
    try {
      dispatch({ type: "hydrate", payload: JSON.parse(cached) as Partial<State> });
    } catch {
      window.localStorage.removeItem(CACHE_KEY);
    }
  }

  const syncAll = useCallback(async () => {
    dispatch({ type: "pending", payload: true });
    try {
      const [
        summary,
        agentsPayload,
        tasksPayload,
        memoryPayload,
        knowledgePayload,
        logsPayload,
        settings,
        toolsPayload,
        routingAnalytics,
        collaborationAnalytics,
        collaborationSessionsPayload,
        reports,
        pipeline,
        errors,
      ] = await Promise.all([
        getJson<DashboardSummary>("/dashboard/summary"),
        getJson<{ agents: Agent[] }>("/agents"),
        getJson<{ tasks: Task[] }>("/tasks"),
        getJson<{ memory: MemoryRecord[] }>("/memory?limit=120"),
        getJson<{ knowledge: KnowledgeRecord[] }>("/knowledge"),
        getJson<{ logs: LogRecord[] }>("/logs?limit=150"),
        getJson<SettingsRecord>("/settings"),
        getJson<{ tools: ToolRecord[] }>("/tools"),
        getJson<Record<string, unknown>>("/routing/analytics"),
        getJson<Record<string, unknown>>("/collaboration/analytics"),
        getJson<{ sessions: CollaborationSession[] }>("/collaboration/sessions?limit=60"),
        getJson<DashboardReport>("/dashboard/reports"),
        getJson<DashboardPipeline>("/dashboard/pipeline"),
        getJson<DashboardErrors>("/dashboard/errors"),
      ]);
      const tasks = tasksPayload.tasks;
      const nextState: Partial<State> = {
        summary,
        agents: agentsPayload.agents,
        tasks,
        approvals: tasks.filter((task) => task.status === "waiting_approval"),
        memory: memoryPayload.memory,
        knowledge: knowledgePayload.knowledge,
        logs: logsPayload.logs,
        settings,
        tools: toolsPayload.tools,
        routingAnalytics,
        collaborationAnalytics,
        collaborationSessions: collaborationSessionsPayload.sessions,
        reports,
        pipeline,
        errors,
        lastSync: new Date().toISOString(),
        offline: false,
      };
      const notifications = deriveNotifications(nextState);
      nextState.notifications = notifications;
      dispatch({ type: "sync", payload: nextState });
      window.localStorage.setItem(CACHE_KEY, JSON.stringify(nextState));
      if ("Notification" in window && Notification.permission === "granted" && notifications[0]) {
        new Notification(notifications[0].title, { body: notifications[0].body });
      }
    } catch {
      dispatch({ type: "offline", payload: true });
    } finally {
      dispatch({ type: "pending", payload: false });
    }
  }, []);

  const connectSocket = useCallback(() => {
    const socket = createSocket("/ws/dashboard");
    socketRef.current = socket;
    socket.addEventListener("open", () => dispatch({ type: "socket", payload: { websocketConnected: true } }));
    socket.addEventListener("close", () => dispatch({ type: "socket", payload: { websocketConnected: false } }));
    socket.addEventListener("message", (event) => {
      const packet = JSON.parse(event.data) as {
        type: string;
        payload: {
          summary: DashboardSummary;
          activity: { logs: LogRecord[] };
          errors: DashboardErrors;
          kpis: Record<string, unknown>;
        };
      };
      if (packet.type !== "dashboard_snapshot") {
        return;
      }
      startTransition(() => {
        dispatch({
          type: "socket",
          payload: {
            summary: packet.payload.summary,
            logs: packet.payload.activity.logs,
            errors: packet.payload.errors,
            websocketConnected: true,
          },
        });
      });
    });
  }, [startTransition]);

  const runSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      dispatch({ type: "search", payload: { query, results: null } });
      return;
    }
    const results = await getJson<SearchResults>(`/dashboard/search?query=${encodeURIComponent(query)}`);
    dispatch({ type: "search", payload: { query, results } });
  }, []);

  const approveTask = useCallback(async (taskId: string, reviewer: string, notes: string) => {
    await postJson(`/tasks/${taskId}/approve`, { reviewer, notes });
    await syncAll();
  }, [syncAll]);

  const rejectTask = useCallback(async (taskId: string, reviewer: string, notes: string) => {
    await postJson(`/tasks/${taskId}/reject`, { reviewer, notes });
    await syncAll();
  }, [syncAll]);

  const executeTask = useCallback(async (taskId: string) => {
    await postJson(`/tasks/${taskId}/execute`, { executor: "Desktop", force_retry: false });
    await syncAll();
  }, [syncAll]);

  const planCollaboration = useCallback(async (taskId: string) => {
    await postJson(`/tasks/${taskId}/collaboration/plan`);
    await syncAll();
  }, [syncAll]);

  const requestDesktopNotifications = useCallback(async () => {
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  }, []);

  return {
    state,
    runSearch,
    syncAll,
    approveTask,
    rejectTask,
    executeTask,
    planCollaboration,
    requestDesktopNotifications,
  };
}

function deriveNotifications(state: Partial<State>): NotificationItem[] {
  const notifications: NotificationItem[] = [];
  const approvals = state.approvals ?? [];
  const errors = state.errors?.failed_tasks ?? [];
  if (approvals.length) {
    notifications.push({
      id: "approval-backlog",
      title: "Approval queue active",
      body: `${approvals.length} task${approvals.length === 1 ? "" : "s"} waiting for review.`,
      severity: "warning",
    });
  }
  if (errors.length) {
    notifications.push({
      id: "task-errors",
      title: "Task failures detected",
      body: `${errors.length} failed task${errors.length === 1 ? "" : "s"} need attention.`,
      severity: "critical",
    });
  }
  if ((state.summary?.tasks_total ?? 0) > 0) {
    notifications.push({
      id: "ops-summary",
      title: "Operations sync ready",
      body: `${state.summary?.tasks_total ?? 0} tasks and ${state.summary?.agents_total ?? 0} agents loaded.`,
      severity: "info",
    });
  }
  return notifications;
}
