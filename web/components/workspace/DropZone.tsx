"use client";

import { useId, useRef, useState } from "react";

interface Props {
  accept: string;
  title: string;
  detail: string;
  onFile: (file: File) => void;
  disabled?: boolean;
  error?: string;
  busy?: boolean;
  size?: "lg" | "sm";
}

export function DropZone({ accept, title, detail, onFile, disabled, error, busy, size = "lg" }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const id = useId();

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onFile(file);
  };

  return (
    <div>
      <button
        type="button"
        disabled={disabled || busy}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          if (!disabled) handleFiles(e.dataTransfer.files);
        }}
        aria-describedby={error ? `${id}-error` : undefined}
        className={`group flex w-full flex-col items-center justify-center rounded-md border-[1.5px] border-dashed text-center transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-60 ${
          size === "lg" ? "gap-1 px-4 py-6" : "gap-0.5 px-3 py-3"
        } ${
          over
            ? "border-navy bg-navy-tint"
            : error
              ? "border-error/50 bg-error-tint/40"
              : "border-rule-strong bg-sheet hover:border-navy/60 hover:bg-navy-tint/50"
        }`}
      >
        <span className={`font-semibold text-navy ${size === "lg" ? "text-sm" : "text-[0.8125rem]"}`}>
          {busy ? "Reading file…" : title}
        </span>
        <span className="text-xs text-mute">{detail}</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        tabIndex={-1}
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1.5 text-xs font-medium text-error">
          {error}
        </p>
      )}
    </div>
  );
}
