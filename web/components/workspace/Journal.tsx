"use client";

import { useState } from "react";
import { fileUrl } from "@/lib/api";
import { AuditBadge, CheckMark, CrossMark, LockMark } from "@/components/ui/Marks";
import type { EditableCoverField, LabReport, ReportRecord } from "@/lib/types";
import type { Workspace } from "@/lib/useWorkspace";
import { Equation } from "./Equation";
import { ObservationTable, PencilNote } from "./ObservationTable";
import { ProseField } from "./ProseField";

const COVER_FIELDS: { field: EditableCoverField; label: string; wide?: boolean }[] = [
  { field: "experiment_title", label: "Experiment title", wide: true },
  { field: "course_code", label: "Course code" },
  { field: "lab_number", label: "Lab no." },
  { field: "course_title", label: "Course title", wide: true },
  { field: "department", label: "Department", wide: true },
  { field: "student_name", label: "Student" },
  { field: "registration_no", label: "Registration no." },
  { field: "section", label: "Section" },
  { field: "instructor", label: "Instructor" },
  { field: "submission_date", label: "Submission date" },
];

export function Journal({ ws, record, report }: { ws: Workspace; record: ReportRecord; report: LabReport }) {
  const body = report.report_body;
  const summary = record.trace_summary;
  const unplacedFlags = record.flags.filter((f) => f.row == null);
  const traced = summary.grounded + summary.normalised;
  const hasLog = Boolean(record.raw_log?.trim());
  const source = record.inputs.raw_log_name || "your log";
  const hasEdits = (fields: readonly string[]) => fields.some((f) => f in ws.edits.body);
  const editAside = (edited: boolean) =>
    edited ? <span className="text-xs font-semibold text-navy">Edited · not in files yet</span> : "Editable";

  return (
    <article className="journal mx-auto max-w-[52rem] space-y-9" aria-label="Report review">
      <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
        <div className="min-w-0 flex-1">
          <h1 className="text-[1.375rem] font-bold leading-tight tracking-tight text-ink text-balance">
            {report.cover_page.lab_number} · {report.cover_page.experiment_title}
          </h1>
          <p className="mt-1 text-sm text-mute">
            {report.cover_page.course_code} · {report.cover_page.course_title}
          </p>
          <div className="mt-2.5">
            <AuditBadge status={report.anomaly_check.status} />
          </div>
        </div>
        <ExperimentBox id={record.id} date={report.cover_page.submission_date} />
      </header>

      <Section title="Cover page" collapsible defaultOpen={false} aside={editAside(Object.keys(ws.edits.cover).length > 0)}>
        <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2">
          {COVER_FIELDS.map(({ field, label, wide }) => (
            <label key={field} className={wide ? "sm:col-span-2" : ""}>
              <span className="mb-1 block text-xs font-semibold text-mute">{label}</span>
              <input
                value={report.cover_page[field]}
                onChange={(e) => ws.editCover(field, e.target.value)}
                className={`h-9 w-full rounded-md border bg-sheet px-2.5 text-sm text-ink transition-[border-color,box-shadow] focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/15 ${
                  field in ws.edits.cover ? "border-navy/60" : "border-rule-strong"
                }`}
              />
            </label>
          ))}
        </div>
      </Section>

      <Section
        title="Procedure"
        collapsible
        defaultOpen={false}
        aside={editAside(hasEdits(["apparatus", "methodology"]))}
      >
        <h3 className="mb-1 text-[0.8125rem] font-semibold text-ink">Apparatus</h3>
        <ProseField
          label="Apparatus, one item per line"
          value={body.apparatus.join("\n")}
          edited={"apparatus" in ws.edits.body}
          onChange={(v) => ws.editBody("apparatus", v.split("\n"))}
        />
        <h3 className="mb-1 mt-4 text-[0.8125rem] font-semibold text-ink">Methodology</h3>
        <ProseField
          label="Methodology"
          value={body.methodology}
          edited={"methodology" in ws.edits.body}
          onChange={(v) => ws.editBody("methodology", v)}
        />
      </Section>

      <Section
        title="Observations"
        aside={
          hasLog ? (
            <span className={`inline-flex items-center gap-1 text-xs font-semibold ${summary.ungrounded ? "text-error" : "text-trace"}`}>
              {summary.ungrounded ? <CrossMark /> : <CheckMark />}
              {summary.ungrounded
                ? `${summary.ungrounded} of ${summary.total} values not found in ${source}`
                : `${traced} of ${summary.total - summary.derived} values traced to ${source}`}
              {summary.derived > 0 && <span className="font-normal text-mute">· {summary.derived} calculated</span>}
            </span>
          ) : (
            <span className="text-xs text-mute">From the lab manual</span>
          )
        }
      >
        <div className="space-y-4">
          {unplacedFlags.map((flag, i) => (
            <PencilNote key={i} flag={flag} status={report.anomaly_check.status} />
          ))}
          {hasLog && report.anomaly_check.status === "ok" && (
            <p className="pencil text-[0.8125rem]">No unit mismatches or outliers found in this log.</p>
          )}
          {body.tables.map((table, i) => (
            <ObservationTable
              key={i}
              table={table}
              index={i}
              trace={hasLog ? record.trace[i] : undefined}
              flags={hasLog ? record.flags : []}
              status={report.anomaly_check.status}
              onHoverLine={ws.setHoveredLine}
            />
          ))}
          <LockedNote>
            {hasLog
              ? "Tables come from your data. To change a number, fix your file and generate again."
              : "Tables are written for this lab. Generate again to rewrite them."}
          </LockedNote>
        </div>
      </Section>

      <Section title="Graph" aside={<LockedAside fromManual={!hasLog} />}>
        {record.files.plot ? (
          <figure className="graph-sheet rounded-md border border-grid p-3 sm:p-5">
            {/* eslint-disable-next-line @next/next/no-img-element -- local API image, versioned by updated_at */}
            <img
              src={fileUrl(record.id, "plot", { version: record.updated_at })}
              alt={`Plot of ${body.tables[0]?.caption ?? "the observations"}`}
              className="mx-auto max-h-[22rem] w-auto rounded-sm bg-sheet shadow-sheet"
            />
          </figure>
        ) : (
          <p className="rounded-md border border-dashed border-rule-strong px-4 py-6 text-center text-sm text-mute">
            The plot couldn&apos;t be drawn for this report. The tables and text are unaffected.
          </p>
        )}
      </Section>

      {body.equations_latex.length > 0 && (
        <Section title="Calculations" aside={<LockedAside fromManual={!hasLog} />}>
          <div className="space-y-1 rounded-md border border-rule bg-sheet px-4 py-2 shadow-sheet">
            {body.equations_latex.map((latex, i) => (
              <Equation key={i} latex={latex} />
            ))}
          </div>
        </Section>
      )}

      <Section title="Result" aside={editAside(hasEdits(["abstract", "discussion", "conclusion"]))}>
        <div className="space-y-5">
          {(
            [
              ["abstract", "Abstract"],
              ["discussion", "Discussion"],
              ["conclusion", "Conclusion"],
            ] as const
          ).map(([field, label]) => (
            <div key={field}>
              <h3 className="mb-1 text-[0.8125rem] font-semibold text-ink">{label}</h3>
              <ProseField
                label={label}
                value={body[field]}
                edited={field in ws.edits.body}
                onChange={(v) => ws.editBody(field, v)}
              />
            </div>
          ))}
        </div>
      </Section>
    </article>
  );
}

function Section({
  title,
  aside,
  children,
  collapsible = false,
  defaultOpen = true,
}: {
  title: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
  collapsible?: boolean;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const asideNode = typeof aside === "string" ? <span className="text-xs text-mute">{aside}</span> : aside;

  return (
    <section className="journal-section">
      <div className="journal-head">
        {collapsible ? (
          <h2>
            <button
              type="button"
              aria-expanded={open}
              onClick={() => setOpen((o) => !o)}
              className="inline-flex items-center gap-1.5 uppercase tracking-[0.08em] hover:text-navy-soft"
            >
              <svg viewBox="0 0 10 10" className={`size-2.5 transition-transform duration-200 ${open ? "rotate-90" : ""}`} aria-hidden>
                <path d="M3 1.5 7 5 3 8.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
              </svg>
              {title}
            </button>
          </h2>
        ) : (
          <h2>{title}</h2>
        )}
        {asideNode}
      </div>
      {(!collapsible || open) && children}
    </section>
  );
}

/** The ruled "Expt. No. / Date" box at the head of a practical-journal page. */
function ExperimentBox({ id, date }: { id: string; date: string }) {
  return (
    <dl className="grid shrink-0 grid-cols-[auto_auto] border border-navy/70 text-xs">
      <dt className="border-b border-r border-navy/30 px-2 py-1 font-semibold uppercase tracking-[0.06em] text-navy">Expt. No.</dt>
      <dd className="border-b border-navy/30 px-2.5 py-1 font-mono text-ink">{id}</dd>
      <dt className="border-r border-navy/30 px-2 py-1 font-semibold uppercase tracking-[0.06em] text-navy">Date</dt>
      <dd className="px-2.5 py-1 font-mono text-ink">{date}</dd>
    </dl>
  );
}

function LockedAside({ fromManual = false }: { fromManual?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-mute">
      <LockMark /> {fromManual ? "From the lab" : "From your data"}
    </span>
  );
}

function LockedNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex items-center gap-1.5 text-xs text-mute">
      <LockMark /> {children}
    </p>
  );
}
