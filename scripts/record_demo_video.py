#!/usr/bin/env python3
"""Record a short EzLab UI demo (Playwright) → WebM/MP4 for LinkedIn / form upload."""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "demo"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    dest = OUT_DIR / "ezlab_demo.webm"
    raw: Path | None = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(OUT_DIR),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()
        try:
            page.goto("http://localhost:3000", wait_until="networkidle", timeout=60_000)
            page.get_by_text("Offline · running on this laptop").wait_for(timeout=30_000)
            time.sleep(1.5)

            page.get_by_role("button", name="OS — Pipes / IPC (C)").first.click()
            time.sleep(2.0)

            page.get_by_role("button", name="Generate report").click()
            page.get_by_role("button", name="Generate again").wait_for(timeout=180_000)
            time.sleep(2.5)

            # Linger on the finished workspace / preview
            page.mouse.wheel(0, 600)
            time.sleep(2.0)
            page.mouse.wheel(0, -400)
            time.sleep(1.5)

            # Quick second sample for breadth
            new_btn = page.get_by_role("button", name="Start a new report")
            if new_btn.count():
                new_btn.first.click()
                time.sleep(1.0)
            page.get_by_role("button", name="DSA — MergeSort vs QuickSort").first.click()
            time.sleep(1.5)
            page.get_by_role("button", name="Generate report").click()
            page.get_by_role("button", name="Generate again").wait_for(timeout=180_000)
            time.sleep(3.0)
            page.mouse.wheel(0, 500)
            time.sleep(2.0)
        finally:
            video = page.video
            context.close()
            browser.close()
            if video is not None:
                raw = Path(video.path())

    if not raw or not raw.exists():
        print("ERROR: no video recorded")
        return 1
    if dest.exists():
        dest.unlink()
    raw.replace(dest)
    # Remove other recorder leftovers
    for extra in OUT_DIR.glob("*.webm"):
        if extra.resolve() != dest.resolve():
            extra.unlink(missing_ok=True)
    print(f"Wrote {dest} ({dest.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
