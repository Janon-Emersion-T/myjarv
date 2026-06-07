import { useMemo, useState } from "react";

import { Panel } from "../components/Panel";
import { Badge } from "../components/Badge";
import { InfoRow } from "../components/Rows";
import type { MemoryCreatePayload, MemoryRecord, MemoryScope, Task } from "../lib/types";

const scopes: MemoryScope[] = ["company", "client", "project", "decision", "mistake", "agent", "user_preference"];

const defaultMemoryForm = {
  scope: "decision" as MemoryScope,
  key: "",
  value: "",
  tags: "",
  source: "desktop",
  task_id: "",
};

function formatScopeLabel(scope: MemoryScope) {
  return scope.replace(/_/g, " ");
}

export function MemoryPage({
  memory,
  tasks,
  onCreateMemory,
}: {
  memory: MemoryRecord[];
  tasks: Task[];
  onCreateMemory: (payload: MemoryCreatePayload) => Promise<void>;
}) {
  const [selectedScope, setSelectedScope] = useState<MemoryScope | "all">("all");
  const [form, setForm] = useState(defaultMemoryForm);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "success" | "danger"; message: string } | null>(null);

  const filteredMemory = useMemo(
    () => (selectedScope === "all" ? memory : memory.filter((item) => item.scope === selectedScope)),
    [memory, selectedScope],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFeedback(null);
    try {
      await onCreateMemory({
        scope: form.scope,
        key: form.key.trim(),
        value: form.value.trim(),
        tags: form.tags
          .split(",")
          .map((entry) => entry.trim())
          .filter(Boolean),
        source: form.source.trim() || undefined,
        task_id: form.task_id || undefined,
      });
      setForm(defaultMemoryForm);
      setFeedback({ tone: "success", message: "Memory saved and available to future routing decisions." });
    } catch (error) {
      setFeedback({ tone: "danger", message: error instanceof Error ? error.message : "Memory creation failed." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <Panel title="Capture Memory">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Scope</span>
              <select
                value={form.scope}
                onChange={(event) => setForm((current) => ({ ...current, scope: event.target.value as MemoryScope }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
              >
                {scopes.map((scope) => (
                  <option key={scope} value={scope}>
                    {formatScopeLabel(scope)}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Key</span>
              <input
                value={form.key}
                onChange={(event) => setForm((current) => ({ ...current, key: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
                placeholder="decision-2026-06-07"
                required
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Source</span>
              <input
                value={form.source}
                onChange={(event) => setForm((current) => ({ ...current, source: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
                placeholder="desktop"
              />
            </label>
          </div>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Memory Value</span>
            <textarea
              value={form.value}
              onChange={(event) => setForm((current) => ({ ...current, value: event.target.value }))}
              className="min-h-28 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
              placeholder="Capture the outcome, rule, or lesson Jarvis should remember."
              required
            />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Tags</span>
              <input
                value={form.tags}
                onChange={(event) => setForm((current) => ({ ...current, tags: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
                placeholder="finance, approval, client-a"
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Related Task</span>
              <select
                value={form.task_id}
                onChange={(event) => setForm((current) => ({ ...current, task_id: event.target.value }))}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
              >
                <option value="">No linked task</option>
                {tasks.slice(0, 20).map((task) => (
                  <option key={task.id} value={task.id}>
                    {task.selected_agent.name}: {task.message.slice(0, 72)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" disabled={submitting} className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60">
              {submitting ? "Saving..." : "Capture Memory"}
            </button>
            {feedback ? (
              <p className={`text-sm ${feedback.tone === "success" ? "text-emerald-700" : "text-rose-700"}`}>{feedback.message}</p>
            ) : (
              <p className="text-sm text-slate-500">Use memory for decisions, client facts, mistakes, and repeatable operating rules.</p>
            )}
          </div>
        </form>
      </Panel>

      <Panel
        title="Memory Browser"
        actions={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setSelectedScope("all")}
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${selectedScope === "all" ? "border-orange-200 bg-orange-100 text-orange-900" : "border-black/10 bg-white text-slate-600"}`}
            >
              all
            </button>
            {scopes.map((scope) => (
              <button
                key={scope}
                type="button"
                onClick={() => setSelectedScope(scope)}
                className={`rounded-full border px-3 py-1 text-xs font-semibold ${selectedScope === scope ? "border-orange-200 bg-orange-100 text-orange-900" : "border-black/10 bg-white text-slate-600"}`}
              >
                {formatScopeLabel(scope)}
              </button>
            ))}
          </div>
        }
      >
        <div className="grid gap-3 xl:grid-cols-2">
          {filteredMemory.map((item) => (
            <div key={item.id} className="space-y-2 rounded-2xl border border-black/10 bg-sand/55 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="accent">{item.scope}</Badge>
                {item.tags.map((tag) => (
                  <Badge key={tag} tone="neutral">
                    {tag}
                  </Badge>
                ))}
              </div>
              <InfoRow
                title={item.key}
                subtitle={item.value}
                meta={item.source ? <Badge tone="neutral">{item.source}</Badge> : undefined}
              />
            </div>
          ))}
          {filteredMemory.length === 0 ? <p className="text-sm text-slate-500">No memory records in this scope yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}
