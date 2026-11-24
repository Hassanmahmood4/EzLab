"""Render LabPulse reports to PDF via the Typst CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from src.validator import ValidationResult, report_to_resolved_dict

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "report_template.typ"
LOCAL_TYPST = ROOT / "bin" / "typst"


def find_typst() -> str:
    if LOCAL_TYPST.exists():
        return str(LOCAL_TYPST)
    found = shutil.which("typst")
    if found:
        return found
    raise FileNotFoundError(
        "Typst CLI not found. Install from https://github.com/typst/typst/releases "
        "or place the binary at bin/typst"
    )


def render_pdf(
    result: ValidationResult,
    output_path: Path,
    template_path: Path = TEMPLATE_PATH,
    work_dir: Path | None = None,
) -> Path:
    if not template_path.exists():
        raise FileNotFoundError(f"Missing Typst template: {template_path}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    work = Path(work_dir) if work_dir else output_path.parent
    work.mkdir(parents=True, exist_ok=True)

    resolved = report_to_resolved_dict(result)

    # Copy images into work dir — Typst resolves paths relative to the .typ file
    logo_src = Path(resolved["university_logo_path"])
    logo_dst = work / "university_logo.png"
    shutil.copy2(logo_src, logo_dst)
    resolved["university_logo_path"] = "university_logo.png"

    if resolved.get("plot_path"):
        plot_src = Path(resolved["plot_path"])
        plot_dst = work / "plot.png"
        if plot_src.resolve() != plot_dst.resolve():
            shutil.copy2(plot_src, plot_dst)
        resolved["plot_path"] = "plot.png"

    json_path = work / "resolved_report.json"
    json_path.write_text(json.dumps(resolved, ensure_ascii=False, indent=2), encoding="utf-8")

    # Copy template next to JSON so relative json("resolved_report.json") resolves
    local_template = work / "report_template.typ"
    shutil.copy2(template_path, local_template)

    typst = find_typst()
    cmd = [typst, "compile", str(local_template), str(output_path.resolve())]
    proc = subprocess.run(
        cmd,
        cwd=str(work),
        capture_output=True,
        text=True,
        env={**os.environ},
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"typst compile failed ({proc.returncode}):\n{proc.stderr or proc.stdout}"
        )
    if not output_path.exists():
        raise FileNotFoundError(f"Typst reported success but missing {output_path}")
    return output_path
