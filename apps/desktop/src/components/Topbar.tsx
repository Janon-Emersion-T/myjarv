import { Badge } from "./Badge";

export function Topbar({
  query,
  onQueryChange,
  onOpenPalette,
  onToggleTheme,
  onToggleLocale,
  onSwitchOperator,
  onRequestNotifications,
  websocketConnected,
  offline,
  operator,
}: {
  query: string;
  onQueryChange: (next: string) => void;
  onOpenPalette: () => void;
  onToggleTheme: () => void;
  onToggleLocale: () => void;
  onSwitchOperator: () => void;
  onRequestNotifications: () => void;
  websocketConnected: boolean;
  offline: boolean;
  operator: string;
}) {
  return (
    <header className="flex flex-col gap-4 rounded-[2rem] border border-black/10 bg-white/70 p-5 shadow-[0_20px_60px_rgba(16,24,32,0.08)] backdrop-blur xl:flex-row xl:items-center xl:justify-between">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={offline ? "warning" : "success"}>{offline ? "Offline cache" : "Live sync"}</Badge>
        <Badge tone={websocketConnected ? "accent" : "neutral"}>{websocketConnected ? "Realtime feed" : "Polling only"}</Badge>
        <Badge tone="neutral">{operator}</Badge>
      </div>
      <div className="flex flex-1 flex-col gap-3 xl:flex-row xl:items-center xl:justify-end">
        <label className="flex min-w-[18rem] flex-1 items-center gap-3 rounded-2xl border border-black/10 bg-slate-950/5 px-4 py-3">
          <span className="text-xs uppercase tracking-[0.3em] text-slate-500">Search</span>
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
            placeholder="Search workspace"
            aria-label="Global search"
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <ActionButton onClick={onOpenPalette}>Command</ActionButton>
          <ActionButton onClick={onSwitchOperator}>Operator</ActionButton>
          <ActionButton onClick={onToggleTheme}>Theme</ActionButton>
          <ActionButton onClick={onToggleLocale}>Locale</ActionButton>
          <ActionButton onClick={onRequestNotifications}>Notify</ActionButton>
        </div>
      </div>
    </header>
  );
}

function ActionButton({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm font-medium text-slate-700 transition hover:-translate-y-0.5 hover:border-black/20"
    >
      {children}
    </button>
  );
}
