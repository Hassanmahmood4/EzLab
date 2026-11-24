"use client";

import { Button, ButtonLink } from "@/components/ui/Button";
import { StaleMark } from "@/components/ui/Marks";
import { useToast } from "@/components/ui/Toast";
import { fileUrl, logoUrl } from "@/lib/api";
import { universityName, useSystem } from "@/lib/system-context";
import type { Workspace } from "@/lib/useWorkspace";

export function DeliverablesPane({ ws }: { ws: Workspace }) {
  const notify = useToast();
  const record = ws.record;

  if (!record || ws.phase !== "ready") {
    return <EmptyDeliverables generating={ws.phase === "generating"} ws={ws} />;
  }

  const version = record.updated_at;
  const pdfMissing = !record.files.pdf;
  const typstMissing = record.render_errors.pdf === "typst_missing";

  const onUpdate = async () => {
    if (await ws.applyEdits()) notify("Files updated");
  };

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-5">
      {ws.isStale ? (
        <div className="rounded-md border border-navy/25 bg-sheet p-3.5 shadow-sheet" role="status">
          <p className="flex items-center gap-2 text-sm font-semibold text-ink">
            <StaleMark className="size-4 text-navy" />
            Your edits aren&apos;t in the files yet
          </p>
          <p className="mt-1 text-xs text-mute">Update the files to see them in the preview and downloads.</p>
          {ws.updateError && <p className="mt-2 text-xs font-medium text-error">{ws.updateError}</p>}
          <div className="mt-3 flex gap-2">
            <Button size="sm" onClick={onUpdate} loading={ws.updating} className="flex-1">
              Update files
            </Button>
            <Button size="sm" variant="quiet" onClick={ws.discardEdits} disabled={ws.updating}>
              Discard edits
            </Button>
          </div>
          <p className="mt-1.5 text-center text-[0.6875rem] text-mute">
            <kbd className="font-sans">Ctrl</kbd> + <kbd className="font-sans">S</kbd>
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2.5">
          <ButtonLink
            href={pdfMissing ? undefined : fileUrl(record.id, "pdf", { download: true, version })}
            aria-disabled={pdfMissing}
            onClick={() => !pdfMissing && notify("PDF downloaded")}
            className={pdfMissing ? "pointer-events-none opacity-40" : ""}
          >
            Download .pdf
          </ButtonLink>
          <ButtonLink
            variant="secondary"
            href={record.files.docx ? fileUrl(record.id, "docx", { download: true, version }) : undefined}
            aria-disabled={!record.files.docx}
            onClick={() => record.files.docx && notify("Word file downloaded")}
            className={record.files.docx ? "" : "pointer-events-none opacity-40"}
          >
            Download .docx
          </ButtonLink>
          <p className="col-span-2 text-center text-xs text-mute">Saved to History as {record.id}</p>
        </div>
      )}

      <div className="relative min-h-[28rem] flex-1">
        {pdfMissing ? (
          <div className="flex h-full flex-col items-center justify-center rounded-md border border-dashed border-rule-strong bg-sheet p-6 text-center">
            <p className="text-sm font-semibold text-ink">PDF preview unavailable</p>
            <p className="mt-1 max-w-xs text-xs text-mute">
              {typstMissing
                ? "Typst isn't installed, so only the Word file was made. Install Typst or place it in bin/typst."
                : "The PDF couldn't be rendered. Your Word file is ready to download."}
            </p>
          </div>
        ) : (
          <iframe
            key={version}
            title={`PDF preview of ${record.id}`}
            src={`${fileUrl(record.id, "pdf", { version })}#toolbar=0&navpanes=0&view=FitH`}
            className={`h-full min-h-[28rem] w-full rounded-md border border-rule bg-sheet shadow-page transition-opacity duration-300 ${
              ws.isStale ? "opacity-45" : ""
            }`}
          />
        )}
        {ws.isStale && !pdfMissing && (
          <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-ink/85 px-2.5 py-1 text-xs font-semibold text-white">
            <StaleMark className="size-3.5" /> Preview out of date
          </span>
        )}
      </div>
    </div>
  );
}

function EmptyDeliverables({ generating, ws }: { generating: boolean; ws: Workspace }) {
  const { profile, universities } = useSystem();
  const universityId = profile?.university_id || ws.profileDraft.university_id;
  const university = universityName(universities, universityId);

  return (
    <div className="flex h-full flex-col gap-4 p-5">
      <div className="grid grid-cols-2 gap-2.5" aria-hidden>
        <div className="flex h-10 items-center justify-center rounded-md bg-navy/15 text-sm font-semibold text-navy/50">Download .pdf</div>
        <div className="flex h-10 items-center justify-center rounded-md border-[1.5px] border-navy/20 text-sm font-semibold text-navy/40">
          Download .docx
        </div>
      </div>
      <div className="flex flex-1 flex-col items-center rounded-md border border-rule bg-sheet px-8 pt-12 text-center shadow-page">
        {universityId ? (
          // eslint-disable-next-line @next/next/no-img-element -- local placeholder crest from the API
          <img src={logoUrl(universityId)} alt="" className="size-16 rounded-full opacity-80" />
        ) : (
          <div className="size-16 rounded-full border-2 border-dashed border-rule-strong" />
        )}
        <p className="mt-4 text-[0.9375rem] font-semibold text-ink">{university || "Your university"}</p>
        <p className="text-xs text-mute">{ws.lab.department || "Department"}</p>
        <p className="mt-10 text-sm font-semibold text-body">{ws.lab.experiment_title || "Experiment title"}</p>
        <p className="mt-auto pb-8 text-xs text-mute">
          {generating ? "Your cover page and report are being prepared…" : "Your cover page and report will preview here."}
        </p>
      </div>
    </div>
  );
}
