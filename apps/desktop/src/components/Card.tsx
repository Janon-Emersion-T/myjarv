export function Card({
  title,
  value,
  note,
  accent,
}: {
  title: string;
  value: string;
  note?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-[2rem] border border-black/10 bg-white/80 p-5 shadow-[0_20px_60px_rgba(16,24,32,0.08)] backdrop-blur">
      <div className={`h-1.5 w-20 rounded-full ${accent ?? "bg-ink"}`} />
      <p className="mt-4 text-xs uppercase tracking-[0.3em] text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-900">{value}</p>
      {note ? <p className="mt-2 text-sm text-slate-600">{note}</p> : null}
    </div>
  );
}
