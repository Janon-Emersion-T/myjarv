import { Panel } from "../components/Panel";
import { Badge } from "../components/Badge";
import type { DashboardPipeline } from "../lib/types";

export function ProjectsPage({ pipeline }: { pipeline: DashboardPipeline | null }) {
  if (!pipeline) {
    return <Panel title="Project Management UI">Loading pipeline...</Panel>;
  }
  return (
    <div className="space-y-6">
      <Panel title="Client Pipeline">
        <div className="grid gap-4 xl:grid-cols-5">
          {Object.entries(pipeline.stages).map(([stage, tasks]) => (
            <div key={stage} className="rounded-2xl border border-black/10 bg-sand/55 p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold capitalize text-slate-900">{stage}</h3>
                <Badge tone="accent">{pipeline.counts[stage] ?? 0}</Badge>
              </div>
              <div className="mt-4 space-y-3">
                {tasks.slice(0, 6).map((task) => (
                  <div key={task.id} className="rounded-xl border border-black/10 bg-white/80 p-3 text-sm text-slate-700">
                    <p className="font-medium">{task.selected_agent.name}</p>
                    <p className="mt-1 line-clamp-3 text-xs leading-5 text-slate-500">{task.message}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Project Timeline Visualization">
        <div className="space-y-3">
          {Object.entries(pipeline.counts).map(([stage, count]) => (
            <div key={stage}>
              <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700">
                <span className="capitalize">{stage}</span>
                <span>{count}</span>
              </div>
              <div className="h-3 rounded-full bg-black/5">
                <div className="h-3 rounded-full bg-ember" style={{ width: `${Math.min(100, count * 12)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
