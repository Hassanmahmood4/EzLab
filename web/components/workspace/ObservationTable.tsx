"use client";

import { Fragment } from "react";
import { TraceTag, WarnMark } from "@/components/ui/Marks";
import type { AnomalyStatus, CellTrace, FlagDetail, ReportTable } from "@/lib/types";

interface Props {
  table: ReportTable;
  index: number;
  trace: CellTrace[][] | undefined;
  flags: FlagDetail[];
  status: AnomalyStatus;
  onHoverLine: (line: number | null) => void;
}

const isNumeric = (cell: string) => /^-?[\d.,]+\s*%?$/.test(cell.trim());

export function ObservationTable({ table, index, trace, flags, status, onHoverLine }: Props) {
  const rowFlags = (row: number) => flags.filter((f) => f.table === index && f.row === row);
  const firstColumnNumeric = table.rows.every((row) => isNumeric(row[0] ?? ""));
  const alignFor = (column: number) => (column === 0 && !firstColumnNumeric ? "text-left" : "text-right");

  return (
    <figure className="overflow-hidden rounded-md border border-rule bg-sheet shadow-sheet">
      <figcaption className="border-b border-rule px-4 py-2.5 text-[0.8125rem] font-semibold text-ink">
        Table {index + 1}. {table.caption}
      </figcaption>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              {table.headers.map((header, c) => (
                <th
                  key={c}
                  scope="col"
                  className={`border-b-[1.5px] border-ink px-4 py-2 font-semibold text-ink ${alignFor(c)}`}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, r) => {
              const notes = rowFlags(r);
              const tone = notes.length ? (status === "error" ? "bg-error-tint/60" : "bg-warn-tint") : "";
              return (
                <Fragment key={r}>
                  <tr className={tone}>
                    {row.map((cell, c) => {
                      const cellTrace = trace?.[r]?.[c];
                      const align = alignFor(c);
                      return (
                        <td
                          key={c}
                          onMouseEnter={() => cellTrace?.line && onHoverLine(cellTrace.line)}
                          onMouseLeave={() => onHoverLine(null)}
                          className={`whitespace-nowrap border-b border-rule px-4 py-2 text-body ${align} ${
                            cellTrace?.line ? "cursor-default hover:bg-trace-tint" : ""
                          }`}
                        >
                          {cell}
                          {cellTrace && <TraceTag status={cellTrace.status} line={cellTrace.line} />}
                        </td>
                      );
                    })}
                  </tr>
                  {notes.map((note, n) => (
                    <tr key={`note-${n}`}>
                      <td colSpan={row.length} className="border-b border-rule bg-sheet px-4 pb-2.5 pt-1.5">
                        <PencilNote flag={note} status={status} />
                      </td>
                    </tr>
                  ))}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

/** The auditor's note, written beneath the row it concerns. */
export function PencilNote({ flag, status }: { flag: FlagDetail; status: AnomalyStatus }) {
  const iconTone = status === "error" ? "text-error" : "text-warn";
  return (
    <p className="pencil flex gap-2 text-[0.8125rem] leading-relaxed">
      <WarnMark className={`mt-[3px] size-3.5 shrink-0 not-italic ${iconTone}`} />
      <span>
        {flag.from && flag.to && (
          <span className="mr-1.5 not-italic">
            <s className={status === "error" ? "text-error decoration-error/70" : "text-graphite decoration-warn"}>{flag.from}</s>
            <span className="mx-1 text-mute" aria-label="corrected to">
              →
            </span>
            <span className="font-semibold text-ink">{flag.to}</span>
          </span>
        )}
        {flag.text}
      </span>
    </p>
  );
}
