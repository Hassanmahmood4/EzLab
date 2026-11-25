"use client";

import { Button } from "@/components/ui/Button";
import { useSystem } from "@/lib/system-context";
import type { Workspace } from "@/lib/useWorkspace";
import { Journal } from "./Journal";
import { SamplePresets } from "./SamplePresets";
import { StageTrack } from "./StageTrack";

const JOURNAL_OUTLINE = [
  { title: "Cover page", detail: "University, course, student and instructor details." },
  { title: "Tasks", detail: "Each manual task with model-written code, terminal output, and graphs." },
];

const FAILURE_COPY: Record<string, { title: string; hint: string }> = {
  no_tasks: {
    title: "Couldn't find tasks in the manual",
    hint: "Use a manual with Exercises / Tasks (1. 2. 3. …) or Task 1 headings, or try a sample lab.",
  },
  model_missing: {
    title: "The EzLab model isn't installed",
    hint: "Put labpulse-1.5b-q4_k_m.gguf in models/, or run with LABPULSE_STUB=1.",
  },
  invalid_output: {
    title: "The model's solutions didn't pass validation",
    hint: "Generate again. Short manuals with clear Task headings work best.",
  },
  backend_unreachable: {
    title: "The local server isn't running",
    hint: "Start it from the project folder with uvicorn on port 8080.",
  },
  busy: { title: "Another report is still generating", hint: "Wait for it to finish, then try again." },
};

export function ReviewPane({ ws }: { ws: Workspace }) {
  const { connection, health } = useSystem();
  const modelMissing = health && !health.model.found && !health.model.stub;

  return (
    <div className="h-full overflow-y-auto px-5 py-6 sm:px-8 lg:px-10">
      {connection === "unreachable" ? (
        <SetupNotice
          title="The local EzLab server isn't running"
          body="The workspace needs the backend on this computer. Open a terminal in the project folder and run:"
          command=".venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8080"
        />
      ) : modelMissing && ws.phase !== "ready" ? (
        <SetupNotice
          title="The EzLab model file is missing"
          body="Place labpulse-1.5b-q4_k_m.gguf in models/ (or run with LABPULSE_STUB=1 for placeholders)."
          command={health.model.path}
        />
      ) : null}

      {ws.phase === "generating" && ws.progress && (
        <div className="mx-auto max-w-[52rem] space-y-9">
          <StageTrack progress={ws.progress} onCancel={ws.cancel} />
          <OutlineSkeleton />
        </div>
      )}

      {ws.phase === "failed" && ws.failure && (
        <div className="mx-auto max-w-[52rem] space-y-9">
          <div role="alert" className="rounded-md border border-error/30 bg-sheet p-5 shadow-sheet">
            <p className="text-[0.9375rem] font-semibold text-error">
              {FAILURE_COPY[ws.failure.code]?.title ?? "The report couldn't be generated"}
            </p>
            <p className="mt-1 text-sm text-body">
              {FAILURE_COPY[ws.failure.code]?.hint ?? ws.failure.message}
            </p>
            {FAILURE_COPY[ws.failure.code] && ws.failure.message && (
              <details className="mt-2 text-xs text-mute">
                <summary className="cursor-pointer">Technical detail</summary>
                <p className="mt-1 font-mono">{ws.failure.message}</p>
              </details>
            )}
            <div className="mt-4 flex gap-2">
              <Button size="sm" onClick={ws.generate}>
                Try again
              </Button>
              <Button size="sm" variant="quiet" onClick={ws.startNew}>
                Start over
              </Button>
            </div>
          </div>
          <OutlineSkeleton />
        </div>
      )}

      {ws.phase === "ready" && ws.record && ws.viewReport && (
        <Journal ws={ws} record={ws.record} report={ws.viewReport} />
      )}

      {ws.phase === "idle" && <EmptyJournal ws={ws} />}
    </div>
  );
}

function EmptyJournal({ ws }: { ws: Workspace }) {
  return (
    <div className="mx-auto max-w-[52rem]">
      <h1 className="text-[1.375rem] font-bold tracking-tight text-ink">Task · Code · Output</h1>
      <p className="mt-1 max-w-prose text-[0.9375rem] text-body">
        Upload the lab manual and your student details. EzLab writes code, terminal output, and
        visualization graphs for each task, then builds Word and PDF like a practical journal.
      </p>
      <div className="mt-4">
        <SamplePresets
          presets={ws.presets}
          onPick={ws.loadPreset}
          label="Want to see it first? Try a sample lab:"
        />
      </div>
      <ol className="mt-8 space-y-6">
        {JOURNAL_OUTLINE.map((item) => (
          <li key={item.title}>
            <div className="journal-head mb-2">
              <h2>{item.title}</h2>
            </div>
            <p className="text-sm text-mute">{item.detail}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

function OutlineSkeleton() {
  return (
    <div className="space-y-9" aria-hidden>
      {["Cover page", "Task 1", "Task 2"].map((title) => (
        <div key={title}>
          <div className="journal-head opacity-50">
            <h2>{title}</h2>
          </div>
          <div className="space-y-2">
            <div className="h-3 w-11/12 animate-pulse rounded bg-well" />
            <div className="h-3 w-4/5 animate-pulse rounded bg-well" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-well" />
          </div>
        </div>
      ))}
    </div>
  );
}

function SetupNotice({
  title,
  body,
  command,
  action,
}: {
  title: string;
  body: string;
  command: string;
  action?: React.ReactNode;
}) {
  return (
    <div role="alert" className="mx-auto mb-8 max-w-[52rem] rounded-md border border-warn-rule bg-warn-tint p-5">
      <p className="text-[0.9375rem] font-semibold text-ink">{title}</p>
      <p className="mt-1 text-sm text-body">{body}</p>
      <code className="mt-3 block overflow-x-auto rounded bg-sheet px-3 py-2 font-mono text-[0.8125rem] text-ink">
        {command}
      </code>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
