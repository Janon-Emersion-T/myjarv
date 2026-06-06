import { Card } from "../components/Card";
import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { DesktopState } from "../lib/types";

export function DashboardPage({ state }: { state: DesktopState & { loading: boolean; isPending: boolean } }) {
  const summary = state.summary;
  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Brain Health" value={summary?.health ?? "loading"} note={summary?.generated_at ?? "Waiting for sync"} accent="bg-moss" />
        <Card title="Active Agents" value={String(summary?.agents_total ?? 0)} note="Registry-backed company roles" accent="bg-ember" />
        <Card title="Task Queue" value={String(summary?.tasks_total ?? 0)} note={`${summary?.tasks_waiting_approval ?? 0} waiting approval`} accent="bg-ink" />
        <Card title="Error Signals" value={String(summary?.error_logs ?? 0)} note={`${summary?.tasks_failed ?? 0} failed tasks`} accent="bg-rose-500" />
      </section>
      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <Panel title="Activity Feed">
          <div className="space-y-3">
            {state.logs.slice(0, 8).map((log) => (
              <InfoRow
                key={`${log.timestamp}-${log.event}`}
                title={log.event}
                subtitle={log.message}
                meta={<StatusBadge status={log.level.toLowerCase()} />}
              />
            ))}
          </div>
        </Panel>
        <Panel title="Notifications">
          <div className="space-y-3">
            {state.notifications.map((note) => (
              <InfoRow key={note.id} title={note.title} subtitle={note.body} meta={<StatusBadge status={note.severity} />} />
            ))}
          </div>
        </Panel>
      </section>
      <section className="grid gap-6 xl:grid-cols-2">
        <Panel title="Routing Snapshot">
          <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">
            {JSON.stringify(state.routingAnalytics ?? {}, null, 2)}
          </pre>
        </Panel>
        <Panel title="Collaboration Snapshot">
          <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">
            {JSON.stringify(state.collaborationAnalytics ?? {}, null, 2)}
          </pre>
        </Panel>
      </section>
    </div>
  );
}
