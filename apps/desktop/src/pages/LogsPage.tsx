import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { DashboardErrors, LogRecord } from "../lib/types";

export function LogsPage({ logs, errors }: { logs: LogRecord[]; errors: DashboardErrors | null }) {
  return (
    <div className="space-y-6">
      <Panel title="Realtime Logs Viewer">
        <div className="space-y-3">
          {logs.slice(0, 40).map((log) => (
            <InfoRow key={`${log.timestamp}-${log.event}`} title={log.event} subtitle={log.message} meta={<StatusBadge status={log.level.toLowerCase()} />} />
          ))}
        </div>
      </Panel>
      <Panel title="Error Analytics Dashboard">
        <div className="space-y-3">
          {errors?.failed_tasks.map((task) => (
            <InfoRow key={task.id} title={task.message} subtitle={task.last_error ?? "Task failed without a stored error message."} meta={<StatusBadge status="failed" />} />
          ))}
          {errors?.failed_tasks.length === 0 ? <p className="text-sm text-slate-500">No failed tasks right now.</p> : null}
        </div>
      </Panel>
    </div>
  );
}
