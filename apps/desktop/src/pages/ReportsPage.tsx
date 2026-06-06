import { Panel } from "../components/Panel";
import type { DashboardReport } from "../lib/types";

export function ReportsPage({ reports }: { reports: DashboardReport | null }) {
  const metrics = reports?.summary;
  return (
    <div className="space-y-6">
      <Panel title="Business KPI Dashboard">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Metric title="Agents" value={String(metrics?.agents_total ?? 0)} />
          <Metric title="Tasks" value={String(metrics?.tasks_total ?? 0)} />
          <Metric title="Approvals" value={String(metrics?.tasks_waiting_approval ?? 0)} />
          <Metric title="Errors" value={String(metrics?.error_logs ?? 0)} />
        </div>
      </Panel>
      <Panel title="AI Execution Trace Viewer and Routing Visualization">
        <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(reports ?? {}, null, 2)}</pre>
      </Panel>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-sand/55 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{title}</p>
      <p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
