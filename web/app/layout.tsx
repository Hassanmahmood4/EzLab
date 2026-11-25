import type { Metadata } from "next";
import localFont from "next/font/local";
import { TopBar } from "@/components/shell/TopBar";
import { StatusFooter } from "@/components/shell/StatusFooter";
import { ToastProvider } from "@/components/ui/Toast";
import { SystemProvider } from "@/lib/system-context";
import "katex/dist/katex.min.css";
import "./globals.css";

const franklin = localFont({
  src: [
    { path: "./fonts/libre-franklin-latin-wght-normal.woff2", style: "normal", weight: "100 900" },
    { path: "./fonts/libre-franklin-latin-wght-italic.woff2", style: "italic", weight: "100 900" },
  ],
  variable: "--font-franklin",
  display: "swap",
});

const jetbrains = localFont({
  src: [
    { path: "./fonts/jetbrains-mono-latin-400-normal.woff2", weight: "400" },
    { path: "./fonts/jetbrains-mono-latin-500-normal.woff2", weight: "500" },
  ],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "EzLab",
  description: "Offline lab report auditor and generator. Your data never leaves this computer.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${franklin.variable} ${jetbrains.variable} h-full antialiased`}>
      <body className="flex h-full flex-col">
        <SystemProvider>
          <ToastProvider>
            <TopBar />
            <div className="flex min-h-0 flex-1 flex-col">{children}</div>
            <StatusFooter />
          </ToastProvider>
        </SystemProvider>
      </body>
    </html>
  );
}
