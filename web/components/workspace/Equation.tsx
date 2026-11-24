"use client";

import katex from "katex";
import { useMemo } from "react";

export function Equation({ latex }: { latex: string }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(latex, { displayMode: true, throwOnError: true, output: "html" });
    } catch {
      return null;
    }
  }, [latex]);

  if (!html) {
    return <code className="block overflow-x-auto rounded bg-well px-3 py-2 font-mono text-[0.8125rem] text-body">{latex}</code>;
  }
  return <div className="overflow-x-auto text-ink" dangerouslySetInnerHTML={{ __html: html }} />;
}
