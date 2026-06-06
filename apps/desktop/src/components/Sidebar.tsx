import type { NavKey } from "../lib/types";

export function Sidebar({
  sections,
  current,
  onNavigate,
  title,
  subtitle,
}: {
  sections: { key: NavKey; label: string }[];
  current: NavKey;
  onNavigate: (key: NavKey) => void;
  title: string;
  subtitle: string;
}) {
  return (
    <aside className="w-full rounded-[2rem] border border-black/10 bg-white/70 p-6 shadow-[0_20px_60px_rgba(16,24,32,0.08)] backdrop-blur lg:sticky lg:top-6 lg:w-80 lg:self-start">
      <p className="text-xs uppercase tracking-[0.35em] text-ember">Jarvis Desktop</p>
      <h1 className="mt-4 text-3xl font-semibold text-slate-900">{title}</h1>
      <p className="mt-2 text-sm leading-6 text-slate-600">{subtitle}</p>
      <nav className="mt-8 space-y-2" aria-label="Primary">
        {sections.map((section) => (
          <button
            key={section.key}
            type="button"
            onClick={() => onNavigate(section.key)}
            className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
              current === section.key
                ? "border-ember/30 bg-ember text-white shadow-[0_16px_30px_rgba(195,79,45,0.25)]"
                : "border-black/5 bg-sand/60 text-slate-700 hover:border-black/10 hover:bg-white"
            }`}
          >
            <span>{section.label}</span>
            <span className="text-xs uppercase tracking-[0.2em]">{section.key.slice(0, 3)}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
