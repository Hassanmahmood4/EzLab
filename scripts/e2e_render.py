#!/usr/bin/env python3
"""End-to-end: load one test.jsonl sample → validate → plot → docx + pdf."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.renderer_docx import ensure_docx_template, render_docx
from src.renderer_pdf import render_pdf
from src.validator import validate_and_prepare


def extract_raw_log(user_content: str) -> str:
    marker = "RAW DATA LOG:\n"
    idx = user_content.find(marker)
    if idx < 0:
        return user_content
    return user_content[idx + len(marker) :]


def main() -> None:
    test_path = ROOT / "data" / "test.jsonl"
    out_dir = ROOT / "outputs" / "e2e"
    out_dir.mkdir(parents=True, exist_ok=True)

    line = test_path.read_text(encoding="utf-8").splitlines()[0]
    example = json.loads(line)
    user = example["messages"][1]["content"]
    assistant = example["messages"][2]["content"]
    raw_log = extract_raw_log(user)

    ensure_docx_template()
    result = validate_and_prepare(assistant, raw_log, work_dir=out_dir, run_plot=True)

    print(f"university: {result.university['full_name']}")
    print(f"grounding: {result.grounding.grounded}/{result.grounding.total_numbers} ({result.grounding.accuracy:.1%})")
    if result.plot_error:
        raise SystemExit(f"plot failed: {result.plot_error}")
    print(f"plot: {result.plot_path}")

    docx_path = render_docx(result, out_dir / "report.docx")
    pdf_path = render_pdf(result, out_dir / "report.pdf", work_dir=out_dir)

    print(f"docx: {docx_path} ({docx_path.stat().st_size} bytes)")
    print(f"pdf:  {pdf_path} ({pdf_path.stat().st_size} bytes)")
    print("e2e_render: OK")


if __name__ == "__main__":
    main()
