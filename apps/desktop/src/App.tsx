import { useEffect, useMemo, useState } from "react";

import { CommandPalette } from "./components/CommandPalette";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { useDesktopState } from "./hooks/useDesktopState";
import { useHashRoute } from "./hooks/useHashRoute";
import { t, type Locale } from "./lib/i18n";
import type { NavKey } from "./lib/types";
import { AgentsPage } from "./pages/AgentsPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { CollaborationPage } from "./pages/CollaborationPage";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { LogsPage } from "./pages/LogsPage";
import { MemoryPage } from "./pages/MemoryPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TasksPage } from "./pages/TasksPage";
import { VoicePage } from "./pages/VoicePage";

type ThemeMode = "light" | "dark";
type Operator = {
  label: string;
  routes: NavKey[];
};

const operators: Operator[] = [
  { label: "CEO", routes: ["dashboard", "approvals", "projects", "reports", "collaboration", "voice", "settings"] },
  { label: "Operations", routes: ["dashboard", "tasks", "approvals", "projects", "logs", "collaboration", "voice", "settings"] },
  { label: "Developer", routes: ["dashboard", "agents", "tasks", "knowledge", "logs", "collaboration", "voice", "settings"] },
  { label: "Finance", routes: ["dashboard", "approvals", "projects", "reports", "memory", "voice", "settings"] },
];

export default function App() {
  const [route, navigate] = useHashRoute();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(() => (window.localStorage.getItem("jarvis-theme") as ThemeMode) || "light");
  const [locale, setLocale] = useState<Locale>(() => (window.localStorage.getItem("jarvis-locale") as Locale) || "en");
  const [operatorIndex, setOperatorIndex] = useState<number>(() => Number(window.localStorage.getItem("jarvis-operator-index") ?? "0"));
  const [query, setQuery] = useState("");
  const {
    state,
    runSearch,
    approveTask,
    rejectTask,
    executeTask,
    planCollaboration,
    requestDesktopNotifications,
    createVoiceSession,
    sendVoiceCommand,
    interruptVoiceSession,
    resumeVoiceSession,
    replayVoiceSession,
  } = useDesktopState();
  const copy = t(locale);
  const operator = operators[operatorIndex % operators.length];

  const sections = useMemo(
    () => {
      const allRoutes = [
        "dashboard",
        "agents",
        "tasks",
        "approvals",
        "projects",
        "memory",
        "knowledge",
        "logs",
        "reports",
        "collaboration",
        "voice",
        "settings",
      ] as NavKey[];
      return allRoutes
        .filter((key) => operator.routes.includes(key))
        .map((key) => ({ key, label: copy.pages[key] }));
    },
    [copy, operator],
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("jarvis-theme", theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem("jarvis-locale", locale);
  }, [locale]);

  useEffect(() => {
    window.localStorage.setItem("jarvis-operator-index", String(operatorIndex));
    if (!operator.routes.includes(route)) {
      navigate(operator.routes[0]);
    }
  }, [operatorIndex, operator, route, navigate]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen(true);
      }
      if (event.key === "Escape") {
        setPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void runSearch(query), 220);
    return () => window.clearTimeout(timeout);
  }, [query, runSearch]);

  return (
    <div className="min-h-screen text-slate-900">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:rounded-xl focus:bg-white focus:px-4 focus:py-3">
        Skip to content
      </a>
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6 px-4 py-6 lg:flex-row lg:px-6">
        <Sidebar sections={sections} current={route} onNavigate={navigate} title={copy.appTitle} subtitle={copy.appSubtitle} />
        <main id="main-content" className="flex-1 space-y-6">
          <Topbar
            query={query}
            onQueryChange={setQuery}
            onOpenPalette={() => setPaletteOpen(true)}
            onToggleTheme={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
            onToggleLocale={() => setLocale((current) => (current === "en" ? "si" : "en"))}
            onSwitchOperator={() => setOperatorIndex((current) => (current + 1) % operators.length)}
            onRequestNotifications={() => void requestDesktopNotifications()}
            websocketConnected={state.websocketConnected}
            offline={state.offline}
            operator={operator.label}
          />
          {renderPage(route, state, {
            approveTask: (taskId: string) => approveTask(taskId, "Desktop", "Approved from Jarvis desktop."),
            rejectTask: (taskId: string) => rejectTask(taskId, "Desktop", "Rejected from Jarvis desktop."),
            executeTask,
            planCollaboration,
            createVoiceSession,
            sendVoiceCommand,
            interruptVoiceSession,
            resumeVoiceSession,
            replayVoiceSession,
          })}
        </main>
      </div>
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        query={query}
        onQueryChange={setQuery}
        results={state.searchResults}
        pages={sections}
        onNavigate={navigate}
      />
    </div>
  );
}

function renderPage(
  route: NavKey,
  state: ReturnType<typeof useDesktopState>["state"],
  actions: {
    approveTask?: (taskId: string) => Promise<void>;
    rejectTask?: (taskId: string) => Promise<void>;
    executeTask?: (taskId: string) => Promise<void>;
    planCollaboration?: (taskId: string) => Promise<void>;
    createVoiceSession?: (payload: { mode: string; text?: string; locale?: string; speaker_id?: string }) => Promise<any>;
    sendVoiceCommand?: (sessionId: string, payload: { text: string; requested_action?: string; locale?: string; speaker_id?: string }) => Promise<unknown>;
    interruptVoiceSession?: (sessionId: string) => Promise<void>;
    resumeVoiceSession?: (sessionId: string) => Promise<void>;
    replayVoiceSession?: (sessionId: string) => Promise<void>;
  },
) {
  switch (route) {
    case "dashboard":
      return <DashboardPage state={state} />;
    case "agents":
      return <AgentsPage agents={state.agents} />;
    case "tasks":
      return <TasksPage tasks={state.tasks} onExecute={actions.executeTask ?? (async () => undefined)} onPlanCollaboration={actions.planCollaboration ?? (async () => undefined)} />;
    case "approvals":
      return <ApprovalsPage approvals={state.approvals} onApprove={actions.approveTask ?? (async () => undefined)} onReject={actions.rejectTask ?? (async () => undefined)} />;
    case "projects":
      return <ProjectsPage pipeline={state.pipeline} />;
    case "memory":
      return <MemoryPage memory={state.memory} />;
    case "knowledge":
      return <KnowledgePage knowledge={state.knowledge} />;
    case "logs":
      return <LogsPage logs={state.logs} errors={state.errors} />;
    case "reports":
      return <ReportsPage reports={state.reports} />;
    case "collaboration":
      return <CollaborationPage sessions={state.collaborationSessions} />;
    case "voice":
      return (
        <VoicePage
          dashboard={state.voiceDashboard}
          sessions={state.voiceSessions}
          onCreateSession={actions.createVoiceSession ?? (async () => ({ id: "" }))}
          onSendCommand={actions.sendVoiceCommand ?? (async () => undefined)}
          onInterrupt={actions.interruptVoiceSession ?? (async () => undefined)}
          onResume={actions.resumeVoiceSession ?? (async () => undefined)}
          onReplay={actions.replayVoiceSession ?? (async () => undefined)}
        />
      );
    case "settings":
      return <SettingsPage settings={state.settings} tools={state.tools} />;
    default:
      return <DashboardPage state={state} />;
  }
}
