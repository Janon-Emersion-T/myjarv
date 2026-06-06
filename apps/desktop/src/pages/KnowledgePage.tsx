import { Panel } from "../components/Panel";
import { InfoRow } from "../components/Rows";
import type { KnowledgeRecord } from "../lib/types";

export function KnowledgePage({ knowledge }: { knowledge: KnowledgeRecord[] }) {
  return (
    <Panel title="Knowledge Browser UI">
      <div className="space-y-3">
        {knowledge.slice(0, 40).map((item) => (
          <InfoRow key={item.path} title={item.path} subtitle={`${item.category} • ${item.content.slice(0, 180)}...`} />
        ))}
      </div>
    </Panel>
  );
}
