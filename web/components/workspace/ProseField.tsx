"use client";

import { useLayoutEffect, useRef } from "react";

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
  edited?: boolean;
  className?: string;
  placeholder?: string;
}

/** Reads like report text; becomes an editor on hover/focus. Grows with its content. */
export function ProseField({ label, value, onChange, edited, className = "", placeholder }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  return (
    <div className="relative">
      <textarea
        ref={ref}
        aria-label={label}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        rows={1}
        spellCheck
        className={`prose-field block w-full resize-none overflow-hidden rounded-md border px-2.5 py-1.5 -mx-2.5 text-[0.9375rem] leading-[1.65] text-body transition-[border-color,background-color,box-shadow] duration-150 hover:border-rule-strong hover:bg-sheet focus:border-navy focus:bg-sheet focus:outline-none focus:ring-2 focus:ring-navy/15 ${
          edited ? "border-navy/35 bg-navy-tint/40" : "border-transparent bg-transparent"
        } ${className}`}
      />
    </div>
  );
}
