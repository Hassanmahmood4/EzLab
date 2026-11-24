"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSystem } from "@/lib/system-context";

const NAV = [
  { href: "/", label: "Workspace" },
  { href: "/history", label: "History" },
  { href: "/profile", label: "Profile" },
] as const;

export function TopBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-6 bg-navy px-4 text-white sm:gap-8 sm:px-6">
      <Link href="/" className="flex items-center gap-2 text-[1.0625rem] font-bold tracking-tight">
        <LogoMark />
        LabPulse
      </Link>
      <nav aria-label="Main" className="flex gap-1">
        {NAV.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`rounded px-2.5 py-1.5 text-sm font-medium transition-colors sm:px-3.5 ${
                active ? "bg-navy-soft text-white" : "text-navy-mist hover:bg-navy-deep hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <LocalStatus />
    </header>
  );
}

function LocalStatus() {
  const { connection } = useSystem();
  const label =
    connection === "connected"
      ? "Offline · running on this laptop"
      : connection === "connecting"
        ? "Connecting to local server…"
        : "Local server not running";
  const dot =
    connection === "connected" ? "bg-white" : connection === "connecting" ? "bg-navy-mist/60" : "bg-[#f4a49c]";

  return (
    <Link
      href="/profile#system"
      className="ml-auto hidden items-center gap-2 rounded-full border border-white/15 px-3 py-1 text-[0.8125rem] font-medium text-white/90 transition-colors hover:border-white/30 md:flex"
      title="Nothing you upload leaves this computer"
    >
      <span className={`size-2 rounded-full ${dot}`} aria-hidden />
      <span role="status">{label}</span>
    </Link>
  );
}

function LogoMark() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden className="text-white">
      <rect x="1.5" y="1.5" width="17" height="17" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M4 12.5h3l1.6-4.5 2.4 7 1.6-4H16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
