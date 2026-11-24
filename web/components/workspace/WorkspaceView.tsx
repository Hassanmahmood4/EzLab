"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useToast } from "@/components/ui/Toast";
import { api, ApiRequestError } from "@/lib/api";
import { useWorkspace } from "@/lib/useWorkspace";
import { DeliverablesPane } from "./DeliverablesPane";
import { InputsPane } from "./InputsPane";
import { ReviewPane } from "./ReviewPane";

type Pane = "inputs" | "review" | "files";

const TABS: { id: Pane; label: string }[] = [
  { id: "inputs", label: "Inputs" },
  { id: "review", label: "Review" },
  { id: "files", label: "Files" },
];

export function WorkspaceView() {
  const ws = useWorkspace();
  const notify = useToast();
  const params = useSearchParams();
  // A tab choice holds until the generation phase changes; then the review pane follows the work.
  const [choice, setChoice] = useState<{ pane: Pane; phase: string }>({ pane: "inputs", phase: ws.phase });
  const pane: Pane = choice.phase !== ws.phase && ws.phase !== "idle" ? "review" : choice.pane;
  const setPane = (next: Pane) => setChoice({ pane: next, phase: ws.phase });
  const openedRef = useRef<string | null>(null);

  const reportId = params.get("report");
  useEffect(() => {
    if (ws.record) openedRef.current = ws.record.id;
  }, [ws.record]);

  useEffect(() => {
    if (reportId && openedRef.current !== reportId && ws.record?.id !== reportId) {
      openedRef.current = reportId;
      ws.openReport(reportId);
    }
  }, [reportId, ws]);

  // Effects re-run when Next restores this route from its cache, so a report deleted
  // from History while this view was hidden is dropped instead of lingering.
  const recordId = ws.record?.id;
  const { startNew } = ws;
  useEffect(() => {
    if (!recordId) return;
    api.report(recordId).catch((error) => {
      if (error instanceof ApiRequestError && error.status === 404) {
        startNew();
        notify("That report was deleted from History");
      }
    });
  }, [recordId, startNew, notify]);

  const previousPhase = useRef(ws.phase);
  useEffect(() => {
    if (previousPhase.current === "generating" && ws.phase === "ready") notify("Report ready · saved to History");
    previousPhase.current = ws.phase;
  }, [ws.phase, notify]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const mod = event.metaKey || event.ctrlKey;
      if (mod && event.key === "Enter" && ws.phase !== "generating") {
        event.preventDefault();
        ws.generate();
      } else if (mod && event.key.toLowerCase() === "s" && ws.isStale) {
        event.preventDefault();
        ws.applyEdits().then((ok) => ok && notify("Files updated"));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [ws, notify]);

  const paneClass = (id: Pane) => (pane === id ? "flex" : "hidden");

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div role="tablist" aria-label="Workspace panes" className="flex border-b border-rule bg-sheet xl:hidden">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={pane === tab.id}
            onClick={() => setPane(tab.id)}
            className={`flex-1 py-2.5 text-sm font-semibold transition-colors ${
              pane === tab.id ? "text-navy shadow-[inset_0_-2px_0_var(--color-navy)]" : "text-mute hover:text-body"
            }`}
          >
            {tab.label}
            {tab.id === "files" && ws.isStale && <span className="ml-1.5 inline-block size-1.5 rounded-full bg-navy align-middle" aria-label="out of date" />}
          </button>
        ))}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)] xl:grid-cols-[320px_minmax(0,1fr)_400px]">
        <aside aria-label="Inputs" className={`${paneClass("inputs")} min-h-0 flex-col border-r border-rule bg-sheet xl:flex`}>
          <InputsPane ws={ws} />
        </aside>
        <main className={`${paneClass("review")} min-h-0 flex-col xl:flex`}>
          <ReviewPane ws={ws} />
        </main>
        <aside aria-label="Report files" className={`${paneClass("files")} min-h-0 flex-col border-l border-rule bg-well xl:flex`}>
          <DeliverablesPane ws={ws} />
        </aside>
      </div>
    </div>
  );
}
