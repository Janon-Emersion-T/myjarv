import { Panel } from "../components/Panel";
import { InfoRow } from "../components/Rows";
import type { MemoryRecord } from "../lib/types";

export function MemoryPage({ memory }: { memory: MemoryRecord[] }) {
  return (
    <Panel title="Memory Browser UI">
      <div className="grid gap-3 xl:grid-cols-2">
        {memory.map((item) => (
          <InfoRow key={item.id} title={`${item.scope} • ${item.key}`} subtitle={item.value} />
        ))}
      </div>
    </Panel>
  );
}
