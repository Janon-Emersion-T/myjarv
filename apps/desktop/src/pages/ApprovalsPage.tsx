import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { Task } from "../lib/types";

export function ApprovalsPage({
  approvals,
  onApprove,
  onReject,
}: {
  approvals: Task[];
  onApprove: (taskId: string) => Promise<void>;
  onReject: (taskId: string) => Promise<void>;
}) {
  return (
    <Panel title="Approval Management UI">
      <div className="space-y-3">
        {approvals.length === 0 ? <p className="text-sm text-slate-500">No approvals are waiting right now.</p> : null}
        {approvals.map((task) => (
          <div key={task.id} className="rounded-2xl border border-black/10 bg-sand/55 p-4">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <InfoRow
                title={task.message}
                subtitle={`${task.selected_agent.name} • ${task.risk_level} risk • ${task.approval_level} approval`}
                meta={<StatusBadge status={task.status} />}
              />
              <div className="flex gap-2">
                <button type="button" onClick={() => void onApprove(task.id)} className="rounded-2xl bg-moss px-4 py-3 text-sm font-medium text-white">
                  Approve
                </button>
                <button type="button" onClick={() => void onReject(task.id)} className="rounded-2xl bg-rose-600 px-4 py-3 text-sm font-medium text-white">
                  Reject
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
