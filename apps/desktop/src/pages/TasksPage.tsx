import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { Task } from "../lib/types";

export function TasksPage({
  tasks,
  onExecute,
  onPlanCollaboration,
}: {
  tasks: Task[];
  onExecute: (taskId: string) => Promise<void>;
  onPlanCollaboration: (taskId: string) => Promise<void>;
}) {
  return (
    <Panel title="Task Management UI">
      <div className="space-y-3">
        {tasks.map((task) => (
          <div key={task.id} className="rounded-2xl border border-black/10 bg-sand/55 p-4">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="space-y-2">
                <InfoRow
                  title={task.message}
                  subtitle={`${task.selected_agent.name} • priority ${task.priority} • ${task.risk_level} risk • ${task.approval_level} approval`}
                  meta={<StatusBadge status={task.status} />}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => void onExecute(task.id)} className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-white">
                  Execute
                </button>
                <button
                  type="button"
                  onClick={() => void onPlanCollaboration(task.id)}
                  className="rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm font-medium text-slate-700"
                >
                  Plan Collaboration
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
