"use client";

import { useSystem } from "@/lib/system-context";

export function StatusFooter() {
  const { health, lastStats } = useSystem();
  if (!health) return null;

  const model = health.model.stub ? "Sample mode (no model)" : health.model.file.replace(/\.gguf$/, "");
  const items = [
    model,
    health.model.loaded ? "Model loaded" : health.model.found || health.model.stub ? "Model idle" : "Model not found",
    `RAM ${(lastStats?.peakRssGb ?? health.memory.rss_gb).toFixed(1)} GB`,
    lastStats ? `${lastStats.tokensPerSecond.toFixed(0)} tok/s` : null,
    lastStats ? `Last run ${Math.round(lastStats.seconds)} s` : null,
  ].filter(Boolean);

  return (
    <footer className="hidden h-8 shrink-0 items-center gap-5 border-t border-rule bg-sheet px-6 text-xs text-mute lg:flex">
      {items.map((item) => (
        <span key={item as string}>{item}</span>
      ))}
    </footer>
  );
}
