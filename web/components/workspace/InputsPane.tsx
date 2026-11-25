"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { universityName, useSystem } from "@/lib/system-context";
import type { Workspace } from "@/lib/useWorkspace";
import { DropZone } from "./DropZone";
import { ProfileFields } from "./ProfileFields";
import { SamplePresets } from "./SamplePresets";

export function InputsPane({ ws }: { ws: Workspace }) {
  const { profile, profileLoaded, universities, connection } = useSystem();
  const busy = ws.phase === "generating";

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-5 pb-6 pt-5">
        {ws.phase === "ready" && (
          <Button variant="secondary" size="sm" className="w-full" onClick={ws.startNew}>
            Start a new report
          </Button>
        )}

        <section aria-labelledby="student-head">
          <div className="mb-2 flex items-baseline justify-between">
            <h2 id="student-head" className="text-[0.6875rem] font-bold uppercase tracking-[0.08em] text-mute">
              Student
            </h2>
            {profile && (
              <Link href="/profile" className="text-xs font-semibold text-navy hover:underline">
                Edit
              </Link>
            )}
          </div>
          {!profileLoaded ? (
            <div className="h-[62px] animate-pulse rounded-md bg-well" />
          ) : profile ? (
            <div className="rounded-md border border-rule bg-sheet px-3 py-2.5">
              <p className="text-[0.9375rem] font-semibold text-ink">{profile.name}</p>
              <p className="text-[0.8125rem] leading-snug text-mute">
                {[profile.registration_no, profile.section].filter(Boolean).join(" · ")}
                <br />
                {profile.university_label || universityName(universities, profile.university_id)}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-[0.8125rem] leading-snug text-body">
                Your details go on the cover page. They&apos;re saved on this laptop, so you enter them once.
              </p>
              <ProfileFields
                compact
                value={ws.profileDraft}
                onChange={ws.updateProfileDraft}
                universities={universities}
                errors={ws.errors}
              />
            </div>
          )}
        </section>

        <section aria-labelledby="lab-head" className="space-y-3">
          <h2 id="lab-head" className="text-[0.6875rem] font-bold uppercase tracking-[0.08em] text-mute">
            Lab
          </h2>
          {ws.manual ? (
            <div className="flex items-center justify-between gap-2 rounded-md border border-rule bg-sheet px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-[0.8125rem] font-semibold text-ink">{ws.manual.name}</p>
                <p className="text-xs text-mute">
                  {ws.tasks.length
                    ? `${ws.tasks.length} task${ws.tasks.length === 1 ? "" : "s"} detected — the model will write code & output`
                    : "Manual loaded — the model will write solutions from it"}
                </p>
              </div>
              <button
                type="button"
                onClick={ws.clearManual}
                className="shrink-0 rounded px-2 py-1 text-xs font-semibold text-navy hover:bg-navy-tint"
              >
                Remove
              </button>
            </div>
          ) : (
            <DropZone
              size="sm"
              accept=".pdf,.docx,.txt,.md"
              title="Upload lab manual"
              detail="PDF, Word, or text — only this is required"
              onFile={ws.loadManual}
              busy={ws.manualLoading}
              disabled={busy}
              error={ws.errors.manual}
            />
          )}
          <div className="grid grid-cols-[1fr_6.5rem] gap-3">
            <TextField
              label="Course code"
              placeholder="CS-100"
              value={ws.lab.course_code}
              onChange={(e) => ws.updateLab("course_code", e.target.value)}
              error={ws.errors.course_code}
              disabled={busy}
            />
            <TextField
              label="Lab no."
              placeholder="Lab 05"
              value={ws.lab.lab_number}
              onChange={(e) => ws.updateLab("lab_number", e.target.value)}
              error={ws.errors.lab_number}
              disabled={busy}
            />
          </div>
          <TextField
            label="Course title"
            placeholder="Machine Learning Lab"
            value={ws.lab.course_title}
            onChange={(e) => ws.updateLab("course_title", e.target.value)}
            error={ws.errors.course_title}
            disabled={busy}
          />
          <TextField
            label="Experiment title"
            placeholder="Data Visualization and EDA"
            value={ws.lab.experiment_title}
            onChange={(e) => ws.updateLab("experiment_title", e.target.value)}
            error={ws.errors.experiment_title}
            disabled={busy}
          />
          <TextField
            label="Department"
            placeholder={profile?.department || "Department of Computer Science"}
            value={ws.lab.department}
            onFocus={() => {
              if (!ws.lab.department && profile?.department) ws.updateLab("department", profile.department);
            }}
            onChange={(e) => ws.updateLab("department", e.target.value)}
            error={ws.errors.department}
            disabled={busy}
          />
          <TextField
            label="Semester (optional)"
            placeholder="5"
            value={ws.semester}
            onChange={(e) => ws.setSemester(e.target.value)}
            disabled={busy}
          />
          <SamplePresets presets={ws.presets} onPick={ws.loadPreset} label="Or try a sample lab:" />
        </section>

        {ws.tasks.length > 0 && (
          <section aria-labelledby="tasks-head" className="space-y-2">
            <h2 id="tasks-head" className="text-[0.6875rem] font-bold uppercase tracking-[0.08em] text-mute">
              Detected tasks
            </h2>
            <ul className="space-y-2">
              {ws.tasks.map((task, index) => (
                <li
                  key={`${task.number}-${index}`}
                  className="rounded-md border border-rule bg-sheet px-3 py-2 text-[0.8125rem]"
                >
                  <p className="font-semibold text-ink">
                    Task {task.number}
                    {task.title ? ` — ${task.title}` : ""}
                  </p>
                  {task.prompt.trim() && (
                    <p className="mt-1 line-clamp-2 text-xs text-mute">{task.prompt}</p>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <div className="border-t border-rule bg-sheet px-5 py-4">
        <Button className="w-full" onClick={ws.generate} disabled={busy || connection !== "connected"} loading={busy}>
          {busy ? "Generating…" : ws.phase === "ready" ? "Generate again" : "Generate report"}
        </Button>
        <p className="mt-1.5 text-center text-xs text-mute">
          Model writes code &amp; output from your manual → Word + PDF
        </p>
      </div>
    </div>
  );
}
