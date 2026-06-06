import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { CollaborationSession } from "../lib/types";

export function CollaborationPage({ sessions }: { sessions: CollaborationSession[] }) {
  return (
    <div className="space-y-6">
      <Panel title="Agent Collaboration UI">
        <div className="space-y-4">
          {sessions.map((session) => (
            <div key={session.id} className="rounded-2xl border border-black/10 bg-sand/55 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-slate-900">{session.primary_agent}</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    {session.strategy} • {session.participants.join(", ")} • reviewers: {session.reviewers.join(", ")}
                  </p>
                </div>
                <StatusBadge status={session.status} />
              </div>
              <div className="mt-4 grid gap-3 xl:grid-cols-2">
                {session.contributions.slice(0, 8).map((contribution) => (
                  <InfoRow
                    key={contribution.id}
                    title={`${contribution.agent} • ${contribution.stage}`}
                    subtitle={`${contribution.summary} • score ${contribution.quality_score}`}
                    meta={<StatusBadge status={contribution.status} />}
                  />
                ))}
              </div>
              <div className="mt-4 rounded-2xl bg-white/80 p-4">
                <h4 className="text-sm font-semibold text-slate-900">Timeline</h4>
                <div className="mt-3 space-y-2">
                  {session.events.slice(0, 10).map((event) => (
                    <InfoRow key={event.id} title={`${event.actor} • ${event.stage}`} subtitle={event.message} meta={<StatusBadge status={event.event_type} />} />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
