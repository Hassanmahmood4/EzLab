"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { STAGES, type Progress } from "@/lib/useWorkspace";

/** Generation record: each stage's bar is as wide as the time it actually took. */
export function StageTrack({ progress, onCancel }: { progress: Progress; onCancel: () => void }) {
  const [now, setNow] = useState(() => performance.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(performance.now()), 250);
    return () => clearInterval(timer);
  }, []);

  const activeIndex = STAGES.findIndex((s) => s.id === progress.stage);
  const durations = STAGES.map((stage, i) => {
    const start = progress.stageStarts[stage.id];
    if (start == null) return 0;
    const next = STAGES.slice(i + 1).map((s) => progress.stageStarts[s.id]).find((t) => t != null);
    return ((next ?? now) - start) / 1000;
  });
  const total = Math.max((now - progress.startedAt) / 1000, 0.1);
  const active = STAGES[activeIndex];

  return (
    <div className="rounded-md border border-rule bg-sheet p-5 shadow-sheet">
      <div className="mb-4 flex items-baseline justify-between gap-4">
        <div>
          <p className="text-[0.9375rem] font-semibold text-ink" aria-live="polite">
            {active.label}
            {progress.stage === "writing" && progress.tokens > 0 ? ` · ${progress.tokens} tokens` : "…"}
          </p>
          <p className="mt-0.5 text-[0.8125rem] text-mute">
            {progress.retried
              ? "The first draft didn't pass validation, so the model is writing it again."
              : "The model is running on this laptop. This usually takes 30–90 seconds."}
          </p>
        </div>
        <span className="shrink-0 font-mono text-sm tabular-nums text-body">{total.toFixed(0)} s</span>
      </div>

      <div className="flex h-2 gap-0.5 overflow-hidden rounded-full bg-well" aria-hidden>
        {STAGES.map((stage, i) =>
          durations[i] > 0 ? (
            <div
              key={stage.id}
              className={`h-full transition-[width] duration-300 ease-out ${i < activeIndex ? "bg-navy" : "bg-navy/55"}`}
              style={{ width: `${(durations[i] / total) * 100}%` }}
            />
          ) : null,
        )}
      </div>

      <ol className="mt-3 grid grid-cols-4 gap-2 text-xs">
        {STAGES.map((stage, i) => (
          <li
            key={stage.id}
            className={i < activeIndex ? "text-navy" : i === activeIndex ? "font-semibold text-ink" : "text-mute/70"}
          >
            {stage.label}
            {durations[i] > 0 && i < activeIndex && (
              <span className="ml-1 font-mono text-mute">{durations[i].toFixed(1)}s</span>
            )}
          </li>
        ))}
      </ol>

      <div className="mt-4 flex justify-end">
        <Button variant="quiet" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
