import { Badge } from "../components/Badge";
import { Panel } from "../components/Panel";
import type { ProjectDashboard } from "../lib/types";

export function ProjectsPage({ dashboard }: { dashboard: ProjectDashboard | null }) {
  if (!dashboard) {
    return <Panel title="Project Management UI">Loading projects...</Panel>;
  }

  const analytics = dashboard.analytics;

  return (
    <div className="space-y-6">
      <Panel title="Project Portfolio">
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Projects" value={String(analytics.projects_total ?? dashboard.projects.length)} />
          <MetricCard label="Open Blockers" value={String(analytics.open_blockers ?? dashboard.blockers.length)} />
          <MetricCard label="Avg Health" value={String(analytics.average_health_score ?? "-")} />
        </div>
      </Panel>

      <Panel title="Active Projects">
        <div className="grid gap-4 xl:grid-cols-2">
          {dashboard.projects.slice(0, 8).map((project) => (
            <article key={project.id} className="rounded-2xl border border-black/10 bg-white/80 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-slate-900">{project.name}</h3>
                  <p className="text-sm text-slate-500">
                    {project.client_name} · {project.category} · {project.methodology}
                  </p>
                </div>
                <Badge tone={project.health_score >= 75 ? "success" : project.health_score >= 55 ? "warning" : "danger"}>
                  Health {project.health_score}
                </Badge>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                <Badge tone="neutral">{project.owner}</Badge>
                <Badge tone="accent">Risk {project.risk_score}</Badge>
                <Badge tone="neutral">{project.status}</Badge>
                {project.deadline ? <Badge tone="warning">Due {project.deadline.slice(0, 10)}</Badge> : null}
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Milestones</h4>
                  <div className="mt-2 space-y-2">
                    {project.milestones.slice(0, 3).map((milestone) => (
                      <div key={milestone.id} className="rounded-xl border border-black/5 bg-sand/55 p-3 text-sm text-slate-700">
                        <p className="font-medium">{milestone.title}</p>
                        <p className="text-xs text-slate-500">{milestone.status}</p>
                      </div>
                    ))}
                    {project.milestones.length === 0 ? <p className="text-sm text-slate-500">No milestones yet.</p> : null}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Blockers</h4>
                  <div className="mt-2 space-y-2">
                    {project.blockers.slice(0, 3).map((blocker) => (
                      <div key={blocker.id} className="rounded-xl border border-black/5 bg-white p-3 text-sm text-slate-700">
                        <p className="font-medium">{blocker.title}</p>
                        <p className="text-xs text-slate-500">
                          {blocker.severity} · {blocker.status}
                        </p>
                      </div>
                    ))}
                    {project.blockers.length === 0 ? <p className="text-sm text-slate-500">No active blockers.</p> : null}
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Timeline And Escalations">
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="space-y-3">
            {dashboard.timeline.slice(0, 6).map((item) => (
              <div key={item.project_id} className="rounded-2xl border border-black/10 bg-sand/55 p-4">
                <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700">
                  <span>{item.project_name}</span>
                  <span>{item.deadline ? item.deadline.slice(0, 10) : "No deadline"}</span>
                </div>
                <div className="h-3 rounded-full bg-black/5">
                  <div className="h-3 rounded-full bg-ember" style={{ width: `${Math.min(100, item.health_score)}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="space-y-3">
            {dashboard.blockers.slice(0, 6).map((blocker) => (
              <div key={`${blocker.project_id}-${blocker.title}`} className="rounded-2xl border border-black/10 bg-white/80 p-4">
                <p className="text-sm font-semibold text-slate-900">{blocker.project_name}</p>
                <p className="mt-1 text-sm text-slate-700">{blocker.title}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-500">{blocker.severity}</p>
              </div>
            ))}
            {dashboard.blockers.length === 0 ? <p className="text-sm text-slate-500">No escalated blockers.</p> : null}
          </div>
        </div>
      </Panel>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-white/80 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
