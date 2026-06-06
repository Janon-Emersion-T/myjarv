import { Panel } from "../components/Panel";
import { InfoRow } from "../components/Rows";
import type { SettingsRecord, ToolRecord } from "../lib/types";

export function SettingsPage({ settings, tools }: { settings: SettingsRecord | null; tools: ToolRecord[] }) {
  return (
    <div className="space-y-6">
      <Panel title="System Settings Dashboard">
        <div className="space-y-3">
          <InfoRow title="Application" subtitle={`${settings?.app_name ?? "Jarvis"} • ${settings?.app_env ?? "unknown"}`} />
          <InfoRow title="Database" subtitle={`${settings?.database_backend ?? "unknown"} • postgres configured: ${String(settings?.postgres_configured ?? false)}`} />
          <InfoRow title="Production Lock" subtitle={String(settings?.production_lock_mode ?? false)} />
        </div>
      </Panel>
      <Panel title="Plugin and Tool Management UI">
        <div className="grid gap-3 xl:grid-cols-2">
          {tools.map((tool) => (
            <InfoRow key={tool.name} title={tool.name} subtitle={`${tool.mode} • ${tool.risk_level} risk • ${tool.description}`} />
          ))}
        </div>
      </Panel>
      <Panel title="Infrastructure, API, and Database Management">
        <div className="grid gap-3 xl:grid-cols-2">
          <InfoRow title="API Management Dashboard" subtitle="FastAPI brain is reachable through the frontend abstraction layer and websocket dashboard feed." />
          <InfoRow title="Database Management UI" subtitle={`Primary backend: ${settings?.database_backend ?? "unknown"} • PostgreSQL ready: ${String(settings?.postgres_configured ?? false)}`} />
          <InfoRow title="Deployment Dashboard" subtitle="Desktop shell surfaces runtime state, logs, and collaboration health for controlled release reviews." />
          <InfoRow title="Vector Memory Management UI" subtitle="Current desktop view is SQLite-first with memory browser coverage and future vector-ready architecture." />
        </div>
      </Panel>
    </div>
  );
}
