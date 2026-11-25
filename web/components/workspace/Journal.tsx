"use client";

import { useState } from "react";
import { figureUrl } from "@/lib/api";
import type { EditableCoverField, LabReport, ReportRecord } from "@/lib/types";
import type { Workspace } from "@/lib/useWorkspace";

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
  { field: "semester", label: "Semester" },
];

export function Journal({ ws, record, report }: { ws: Workspace; record: ReportRecord; report: LabReport }) {
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
          <p className="mt-2 text-xs font-semibold text-mute">
            {report.tasks.length} task{report.tasks.length === 1 ? "" : "s"} · code, output
            {report.tasks.some((t) => (t.figures?.length ?? 0) > 0) ? " & graphs" : ""}
          </p>
        </div>
        <ExperimentBox id={record.id} date={report.cover_page.submission_date} />
      </header>

      <Section
        title="Cover page"
        collapsible
        defaultOpen={false}
        aside={
          Object.keys(ws.edits.cover).length > 0 ? (
            <span className="text-xs font-semibold text-navy">Edited · not in files yet</span>
          ) : (
            "Editable"
          )
        }
      >
        <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2">
          {COVER_FIELDS.map(({ field, label, wide }) => (
            <label key={field} className={wide ? "sm:col-span-2" : ""}>
              <span className="mb-1 block text-xs font-semibold text-mute">{label}</span>
              <input
                value={report.cover_page[field] ?? ""}
                onChange={(e) => ws.editCover(field, e.target.value)}
                className={`h-9 w-full rounded-md border bg-sheet px-2.5 text-sm text-ink transition-[border-color,box-shadow] focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/15 ${
                  field in ws.edits.cover ? "border-navy/60" : "border-rule-strong"
                }`}
              />
            </label>
          ))}
        </div>
      </Section>

      {report.tasks.map((task) => (
        <Section key={task.number} title={`Task ${task.number} — ${task.title}`}>
          {task.prompt.trim() && (
            <p className="mb-3 text-sm leading-relaxed text-body whitespace-pre-wrap">{task.prompt}</p>
          )}
          <MonoBlock label="Code" text={task.code} />
          <MonoBlock label="Output" text={task.output || "(none)"} />
          {(task.figures?.length ?? 0) > 0 && (
            <div className="mb-3">
              <h3 className="mb-2 text-[0.8125rem] font-semibold text-ink">Visualization Output</h3>
              <div className="space-y-3">
                {task.figures!.map((name) => (
                  <figure
                    key={name}
                    className="overflow-hidden rounded-md border border-rule bg-sheet"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={figureUrl(record.id, name, record.updated_at)}
                      alt={`Task ${task.number} figure`}
                      className="mx-auto max-h-[28rem] w-full object-contain bg-white p-2"
                    />
                    <figcaption className="border-t border-rule px-3 py-1.5 text-xs text-mute">
                      {name}
                    </figcaption>
                  </figure>
                ))}
              </div>
            </div>
          )}
        </Section>
      ))}
    </article>
  );
}

function MonoBlock({ label, text }: { label: string; text: string }) {
  return (
    <div className="mb-3">
      <h3 className="mb-1 text-[0.8125rem] font-semibold text-ink">{label}</h3>
      <pre className="overflow-x-auto rounded-md border border-rule bg-well p-3 font-mono text-[0.75rem] leading-snug text-ink whitespace-pre-wrap">
        {text}
      </pre>
    </div>
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
              <svg
                viewBox="0 0 10 10"
                className={`size-2.5 transition-transform duration-200 ${open ? "rotate-90" : ""}`}
                aria-hidden
              >
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

function ExperimentBox({ id, date }: { id: string; date: string }) {
  return (
    <dl className="grid shrink-0 grid-cols-[auto_auto] border border-navy/70 text-xs">
      <dt className="border-b border-r border-navy/30 px-2 py-1 font-semibold uppercase tracking-[0.06em] text-navy">
        Expt. No.
      </dt>
      <dd className="border-b border-navy/30 px-2.5 py-1 font-mono text-ink">{id}</dd>
      <dt className="border-r border-navy/30 px-2 py-1 font-semibold uppercase tracking-[0.06em] text-navy">Date</dt>
      <dd className="px-2.5 py-1 font-mono text-ink">{date}</dd>
    </dl>
  );
}
