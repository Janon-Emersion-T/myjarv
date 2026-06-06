import type { NavKey, SearchResults } from "../lib/types";

export function CommandPalette({
  open,
  onClose,
  query,
  onQueryChange,
  results,
  pages,
  onNavigate,
}: {
  open: boolean;
  onClose: () => void;
  query: string;
  onQueryChange: (next: string) => void;
  results: SearchResults | null;
  pages: { key: NavKey; label: string }[];
  onNavigate: (key: NavKey) => void;
}) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/50 px-4 py-10 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="w-full max-w-3xl rounded-[2rem] border border-white/10 bg-slate-950/95 p-5 text-white shadow-[0_30px_120px_rgba(0,0,0,0.45)]">
        <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
          <span className="text-xs uppercase tracking-[0.3em] text-white/60">Command</span>
          <input
            autoFocus
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            className="w-full bg-transparent text-sm outline-none placeholder:text-white/35"
            placeholder="Jump to a page or search records"
          />
          <button type="button" onClick={onClose} className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/70">
            Esc
          </button>
        </div>
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <section>
            <h3 className="text-xs uppercase tracking-[0.3em] text-white/50">Pages</h3>
            <div className="mt-3 space-y-2">
              {pages.map((page) => (
                <button
                  key={page.key}
                  type="button"
                  onClick={() => {
                    onNavigate(page.key);
                    onClose();
                  }}
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm transition hover:bg-white/10"
                >
                  {page.label}
                </button>
              ))}
            </div>
          </section>
          <section>
            <h3 className="text-xs uppercase tracking-[0.3em] text-white/50">Results</h3>
            <div className="mt-3 space-y-2">
              {results ? (
                <>
                  {results.tasks.slice(0, 4).map((task) => (
                    <ResultRow key={task.id} title={task.message} subtitle={`Task • ${task.selected_agent.name} • ${task.status}`} />
                  ))}
                  {results.agents.slice(0, 4).map((agent) => (
                    <ResultRow key={agent.name} title={agent.name} subtitle={`Agent • ${agent.department} • ${agent.role}`} />
                  ))}
                  {results.memory.slice(0, 3).map((item) => (
                    <ResultRow key={item.id} title={item.key} subtitle={`Memory • ${item.scope}`} />
                  ))}
                </>
              ) : (
                <p className="text-sm text-white/50">Type to search the workspace.</p>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function ResultRow({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-xs text-white/55">{subtitle}</p>
    </div>
  );
}
