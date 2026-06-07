import { useMemo, useState } from "react";

import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { Agent, Task, TaskCreatePayload } from "../lib/types";

const defaultTaskForm = {
  message: "",
  preferred_agent: "",
  requested_action: "",
  client: "",
  project: "",
};

export function TasksPage({
  tasks,
  agents,
  onCreateTask,
  onExecute,
  onPlanCollaboration,
}: {
  tasks: Task[];
  agents: Agent[];
  onCreateTask: (payload: TaskCreatePayload) => Promise<void>;
  onExecute: (taskId: string) => Promise<void>;
  onPlanCollaboration: (taskId: string) => Promise<void>;
}) {
  const [form, setForm] = useState(defaultTaskForm);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "success" | "danger"; message: string } | null>(null);

  const agentOptions = useMemo(() => agents.map((agent) => agent.name).sort((left, right) => left.localeCompare(right)), [agents]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFeedback(null);
    try {
      await onCreateTask({
        message: form.message.trim(),
        preferred_agent: form.preferred_agent || undefined,
        requested_action: form.requested_action.trim() || undefined,
        metadata: {
          ...(form.client.trim() ? { client: form.client.trim() } : {}),
          ...(form.project.trim() ? { project: form.project.trim() } : {}),
        },
      });
      setForm(defaultTaskForm);
      setFeedback({ tone: "success", message: "Task created and routed through the brain." });
    } catch (error) {
      setFeedback({ tone: "danger", message: error instanceof Error ? error.message : "Task creation failed." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <Panel title="Create Task">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Request</span>
            <textarea
              value={form.message}
              onChange={(event) => setForm((current) => ({ ...current, message: event.target.value }))}
              className="min-h-32 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
              placeholder="Describe the work Jarvis should route and execute."
              required
            />
          </label>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Preferred Agent</span>
              <select
                value={form.preferred_agent}
                onChange={(event) => setForm((current) => ({ ...current, preferred_agent: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
              >
                <option value="">Auto-route</option>
                {agentOptions.map((agent) => (
                  <option key={agent} value={agent}>
                    {agent}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Requested Action</span>
              <input
                value={form.requested_action}
                onChange={(event) => setForm((current) => ({ ...current, requested_action: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
                placeholder="review, draft, execute"
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Client</span>
              <input
                value={form.client}
                onChange={(event) => setForm((current) => ({ ...current, client: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
                placeholder="Optional client context"
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Project</span>
              <input
                value={form.project}
                onChange={(event) => setForm((current) => ({ ...current, project: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
                placeholder="Optional project context"
              />
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" disabled={submitting} className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60">
              {submitting ? "Routing..." : "Create Task"}
            </button>
            {feedback ? (
              <p className={`text-sm ${feedback.tone === "success" ? "text-emerald-700" : "text-rose-700"}`}>{feedback.message}</p>
            ) : (
              <p className="text-sm text-slate-500">New tasks are persisted immediately and returned to the live queue after routing.</p>
            )}
          </div>
        </form>
      </Panel>

      <Panel title="Task Queue">
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
                  {task.routing?.project_context || task.routing?.execution_strategy || task.last_error ? (
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                      {task.routing?.project_context ? <InfoRow title="Project Context" subtitle={task.routing.project_context} /> : null}
                      {task.routing?.execution_strategy ? <InfoRow title="Execution Strategy" subtitle={task.routing.execution_strategy} /> : null}
                      {task.last_error ? <InfoRow title="Last Error" subtitle={task.last_error} meta={<StatusBadge status="failed" />} /> : null}
                    </div>
                  ) : null}
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
          {tasks.length === 0 ? <p className="text-sm text-slate-500">No tasks yet. Create one above to start the queue.</p> : null}
        </div>
      </Panel>
    </div>
  );
}
