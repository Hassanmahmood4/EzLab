import type { AnomalyStatus, TraceStatus } from "@/lib/types";

/** Each state has its own shape, never colour alone. */

export function CheckMark({ className = "size-3" }: { className?: string }) {
  return (
    <svg viewBox="0 0 12 12" className={className} aria-hidden>
      <path d="M2.5 6.4 5 8.8l4.5-5.6" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CrossMark({ className = "size-3" }: { className?: string }) {
  return (
    <svg viewBox="0 0 12 12" className={className} aria-hidden>
      <path d="M3 3l6 6M9 3 3 9" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export function WarnMark({ className = "size-3.5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 14 14" className={className} aria-hidden>
      <path d="M7 1.8 13 12H1z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M7 5.6v3M7 10.2v.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function StaleMark({ className = "size-3.5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 14 14" className={className} aria-hidden>
      <circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2.4 2" />
      <path d="M7 4.2V7l1.8 1.2" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function LockMark({ className = "size-3" }: { className?: string }) {
  return (
    <svg viewBox="0 0 12 12" className={className} aria-hidden>
      <rect x="2.5" y="5.2" width="7" height="5" rx="1" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <path d="M4 5.2V3.8a2 2 0 0 1 4 0v1.4" fill="none" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

const TRACE_LABEL: Record<Exclude<TraceStatus, "text">, string> = {
  grounded: "Found in your log",
  normalised: "Unit normalised from your log",
  derived: "Calculated from this row",
  ungrounded: "Not found in your log",
};

/** Small tag that sits after a table value and says where it came from. */
export function TraceTag({ status, line }: { status: TraceStatus; line: number | null }) {
  if (status === "text") return null;
  const label = `${TRACE_LABEL[status]}${line ? `, line ${line}` : ""}`;

  if (status === "ungrounded") {
    return (
      <span title={label} className="ml-1.5 inline-flex items-center gap-0.5 rounded-sm bg-error-tint px-1 align-[1px] text-[0.625rem] font-semibold text-error">
        <CrossMark className="size-2.5" />
        <span className="sr-only">{label}</span>
        <span aria-hidden>not in log</span>
      </span>
    );
  }
  if (status === "derived") {
    return (
      <span title={label} className="ml-1.5 inline-flex items-center rounded-sm border border-rule-strong px-1 align-[1px] text-[0.625rem] font-semibold text-mute">
        <span className="sr-only">{label}</span>
        <span aria-hidden>calc</span>
      </span>
    );
  }
  const tone = status === "normalised" ? "text-warn" : "text-trace";
  return (
    <span title={label} className={`ml-1 inline-flex items-center gap-px align-[1px] font-mono text-[0.625rem] font-medium ${tone}`}>
      <CheckMark className="size-2.5" />
      <span className="sr-only">{label}</span>
      <span aria-hidden>{line ? `L${line}` : ""}</span>
    </span>
  );
}

const STATUS_COPY: Record<AnomalyStatus, string> = {
  ok: "No anomalies",
  warning: "Anomaly corrected",
  error: "Needs checking",
};

export function AuditBadge({ status }: { status: AnomalyStatus }) {
  const tone =
    status === "ok"
      ? "border-rule-strong text-graphite"
      : status === "warning"
        ? "border-warn-rule bg-warn-tint text-warn"
        : "border-error/30 bg-error-tint text-error";
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-semibold ${tone}`}>
      {status === "ok" ? <CheckMark /> : status === "warning" ? <WarnMark className="size-3" /> : <CrossMark />}
      {STATUS_COPY[status]}
    </span>
  );
}
