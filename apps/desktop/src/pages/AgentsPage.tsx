import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";
import type { Agent } from "../lib/types";

export function AgentsPage({ agents }: { agents: Agent[] }) {
  return (
    <Panel title="Agent Directory">
      <div className="grid gap-3 xl:grid-cols-2">
        {agents.map((agent) => (
          <InfoRow
            key={agent.name}
            title={agent.name}
            subtitle={`${agent.department} • ${agent.role}${agent.description ? ` • ${agent.description}` : ""}`}
            meta={<StatusBadge status={(agent.approval_level ?? "low").toLowerCase()} />}
          />
        ))}
      </div>
    </Panel>
  );
}
