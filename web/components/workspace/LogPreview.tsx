"use client";

import { useEffect, useRef } from "react";

interface Props {
  name: string;
  text: string;
  size: number;
  highlightLine: number | null;
  flaggedLines: Set<number>;
  onClear?: () => void;
}

const formatSize = (bytes: number) => (bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB`);

/** Numbered raw-log preview; lines light up when their values are hovered in the report. */
export function LogPreview({ name, text, size, highlightLine, flaggedLines, onClear }: Props) {
  const lines = text.replace(/\s+$/, "").split(/\r?\n/);
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    if (highlightLine == null) return;
    listRef.current
      ?.querySelector<HTMLElement>(`[data-line="${highlightLine}"]`)
      ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [highlightLine]);

  return (
    <div className="overflow-hidden rounded-md border border-rule-strong bg-sheet">
      <div className="flex items-center justify-between gap-2 border-b border-rule bg-ground px-3 py-2">
        <div className="min-w-0">
          <p className="truncate text-[0.8125rem] font-semibold text-ink">{name}</p>
          <p className="text-xs text-mute">
            {lines.length} lines · {formatSize(size)}
          </p>
        </div>
        {onClear && (
          <button
            type="button"
            onClick={onClear}
            className="shrink-0 rounded px-2 py-1 text-xs font-semibold text-navy hover:bg-navy-tint"
          >
            Replace
          </button>
        )}
      </div>
      <ol ref={listRef} className="max-h-56 overflow-auto py-1 font-mono text-[0.75rem] leading-[1.7]" aria-label="Raw data lines">
        {lines.map((line, index) => {
          const n = index + 1;
          const lit = n === highlightLine;
          const flagged = flaggedLines.has(n);
          return (
            <li
              key={n}
              data-line={n}
              className={`grid grid-cols-[2.5rem_1fr] transition-colors duration-150 ${
                lit ? "bg-trace-tint" : flagged ? "bg-warn-tint" : ""
              }`}
            >
              <span
                className={`select-none pr-2 text-right ${lit ? "font-medium text-trace-strong" : "text-mute/70"}`}
                aria-hidden
              >
                {n}
              </span>
              <span className={`whitespace-pre pr-3 ${line.startsWith("#") ? "text-mute" : "text-body"}`}>{line || " "}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
