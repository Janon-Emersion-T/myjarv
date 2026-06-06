import { Badge } from "./Badge";

export function InfoRow({
  title,
  subtitle,
  meta,
}: {
  title: string;
  subtitle: string;
  meta?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-black/10 bg-sand/55 px-4 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-slate-900">{title}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">{subtitle}</p>
        </div>
        {meta}
      </div>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "completed"
      ? "success"
      : status === "failed" || status === "rejected"
        ? "danger"
        : status === "waiting_approval"
          ? "warning"
          : "accent";
  return <Badge tone={tone}>{status.split("_").join(" ")}</Badge>;
}
