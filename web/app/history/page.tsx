"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, ButtonLink } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { api, fileUrl } from "@/lib/api";
import type { ReportSummary } from "@/lib/types";

type SortKey = "created_at" | "course_code";

const dateFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });
const timeFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

export default function HistoryPage() {
  const notify = useToast();
  const [reports, setReports] = useState<ReportSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: "created_at", desc: true });
  const [confirming, setConfirming] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const [attempt, setAttempt] = useState(0);
  const load = useCallback(() => {
    setError(null);
    setReports(null);
    setAttempt((n) => n + 1);
  }, []);

  useEffect(() => {
    let active = true;
    api
      .reports()
      .then((list) => active && setReports(list))
      .catch((e: unknown) => active && setError(e instanceof Error ? e.message : "Couldn't load your reports."));
    return () => {
      active = false;
    };
  }, [attempt]);

  const sorted = useMemo(() => {
    if (!reports) return null;
    const dir = sort.desc ? -1 : 1;
    return [...reports].sort((a, b) => (a[sort.key] < b[sort.key] ? -dir : a[sort.key] > b[sort.key] ? dir : 0));
  }, [reports, sort]);

  const toggleSort = (key: SortKey) =>
    setSort((current) => ({ key, desc: current.key === key ? !current.desc : key === "created_at" }));

  const remove = async (id: string) => {
    setDeleting(id);
    try {
      await api.deleteReport(id);
      setReports((current) => current?.filter((r) => r.id !== id) ?? null);
      notify(`Deleted ${id}`);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Couldn't delete that report.");
    } finally {
      setDeleting(null);
      setConfirming(null);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-[1.375rem] font-bold tracking-tight text-ink">History</h1>
            <p className="mt-1 text-sm text-mute">
              Every report you generate is kept on this laptop. Reopen one to edit it or download the files again.
            </p>
          </div>
          {reports && reports.length > 0 && (
            <p className="text-sm text-mute">
              {reports.length} report{reports.length === 1 ? "" : "s"}
            </p>
          )}
        </div>

        <div className="mt-6">
          {error ? (
            <div role="alert" className="rounded-md border border-error/30 bg-sheet p-5">
              <p className="font-semibold text-error">Couldn&apos;t load your history</p>
              <p className="mt-1 text-sm text-body">{error}</p>
              <Button size="sm" className="mt-3" onClick={load}>
                Try again
              </Button>
            </div>
          ) : sorted === null ? (
            <div className="space-y-2" aria-label="Loading reports">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-14 animate-pulse rounded-md bg-well" />
              ))}
            </div>
          ) : sorted.length === 0 ? (
            <div className="rounded-md border border-dashed border-rule-strong bg-sheet px-6 py-14 text-center">
              <p className="text-[0.9375rem] font-semibold text-ink">No reports yet</p>
              <p className="mt-1 text-sm text-mute">Reports you generate in the workspace will be listed here.</p>
              <Link href="/" className="mt-4 inline-block text-sm font-semibold text-navy hover:underline">
                Go to the workspace
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border border-rule bg-sheet shadow-sheet">
              <table className="w-full min-w-[60rem] table-fixed border-collapse text-sm">
                <colgroup>
                  <col className="w-[12rem]" />
                  <col />
                  <col className="w-[10.5rem]" />
                  <col className="w-[8.5rem]" />
                  <col className="w-[17rem]" />
                </colgroup>
                <thead>
                  <tr className="border-b-[1.5px] border-navy text-left">
                    <SortHeader label="Course" active={sort.key === "course_code"} desc={sort.desc} onClick={() => toggleSort("course_code")} />
                    <th scope="col" className="px-4 py-2.5 text-xs font-bold uppercase tracking-[0.08em] text-navy">
                      Experiment
                    </th>
                    <th scope="col" className="px-4 py-2.5 text-xs font-bold uppercase tracking-[0.08em] text-navy">
                      Tasks
                    </th>
                    <SortHeader label="Generated" active={sort.key === "created_at"} desc={sort.desc} onClick={() => toggleSort("created_at")} />
                    <th scope="col" className="px-4 py-2.5">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((r) => {
                    const created = new Date(r.created_at);
                    return (
                      <tr key={r.id} className="border-b border-rule last:border-0 hover:bg-ground/70">
                        <td className="px-4 py-3 align-top">
                          <p className="font-semibold text-ink">{r.course_code}</p>
                          <p className="whitespace-nowrap font-mono text-xs text-mute">{r.id}</p>
                        </td>
                        <td className="px-4 py-3 align-top">
                          <p className="text-ink">
                            <span className="text-mute">{r.lab_number} · </span>
                            {r.experiment_title}
                          </p>
                          <p className="text-xs text-mute">{r.course_title}</p>
                        </td>
                        <td className="px-4 py-3 align-top text-sm text-body">
                          {r.task_count} task{r.task_count === 1 ? "" : "s"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 align-top text-body">
                          {dateFormat.format(created)}
                          <span className="block text-xs text-mute">{timeFormat.format(created)}</span>
                        </td>
                        <td className="px-4 py-3 align-top">
                          {confirming === r.id ? (
                            <div className="flex items-center justify-end gap-2">
                              <span className="whitespace-nowrap text-xs text-body">Delete report and files?</span>
                              <Button size="sm" variant="danger" loading={deleting === r.id} onClick={() => remove(r.id)}>
                                Delete
                              </Button>
                              <Button size="sm" variant="quiet" onClick={() => setConfirming(null)}>
                                Keep
                              </Button>
                            </div>
                          ) : (
                            <div className="flex items-center justify-end gap-1.5">
                              <ButtonLink size="sm" variant="secondary" href={`/?report=${encodeURIComponent(r.id)}`}>
                                Open
                              </ButtonLink>
                              {r.files.pdf && (
                                <ButtonLink size="sm" variant="quiet" href={fileUrl(r.id, "pdf", { download: true, version: r.updated_at })}>
                                  .pdf
                                </ButtonLink>
                              )}
                              {r.files.docx && (
                                <ButtonLink size="sm" variant="quiet" href={fileUrl(r.id, "docx", { download: true, version: r.updated_at })}>
                                  .docx
                                </ButtonLink>
                              )}
                              <Button size="sm" variant="quiet" className="text-error hover:bg-error-tint" onClick={() => setConfirming(r.id)}>
                                Delete
                              </Button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SortHeader({ label, active, desc, onClick }: { label: string; active: boolean; desc: boolean; onClick: () => void }) {
  return (
    <th scope="col" aria-sort={active ? (desc ? "descending" : "ascending") : "none"} className="px-4 py-2.5">
      <button
        type="button"
        onClick={onClick}
        className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-[0.08em] text-navy hover:text-navy-soft"
      >
        {label}
        <svg viewBox="0 0 10 10" className={`size-2.5 transition-transform ${active ? "" : "opacity-30"} ${active && !desc ? "rotate-180" : ""}`} aria-hidden>
          <path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      </button>
    </th>
  );
}
