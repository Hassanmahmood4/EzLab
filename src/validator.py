"""University resolve and report preparation for task / code / output labs."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.figure_runner import attach_figures_to_report
from src.schema import LabReportSchema, validate_report

ROOT = Path(__file__).resolve().parents[1]
UNIVERSITIES_PATH = ROOT / "assets" / "universities.json"


@dataclass
class ValidationResult:
    report: LabReportSchema
    university: dict[str, Any]
    logo_path: Path
    work_dir: Path
    plot_path: Path | None = None
    plot_error: str | None = None
    figure_files: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True


def load_universities(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or UNIVERSITIES_PATH).read_text(encoding="utf-8"))


def resolve_university(university_id: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_universities()
    if university_id not in registry:
        raise KeyError(f"Unknown university_id: {university_id}")
    meta = dict(registry[university_id])
    logo = ROOT / meta["logo_path"]
    if not logo.exists():
        raise FileNotFoundError(f"Missing university logo: {logo}")
    meta["university_id"] = university_id
    meta["logo_abs"] = str(logo)
    return meta


def validate_and_prepare(
    payload: dict | str | LabReportSchema,
    raw_log: str = "",  # kept for call-site compatibility
    work_dir: Path | None = None,
    run_plot: bool = True,
) -> ValidationResult:
    del raw_log
    report = payload if isinstance(payload, LabReportSchema) else validate_report(payload)
    university = resolve_university(report.cover_page.university_id)
    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="labpulse_"))
    work.mkdir(parents=True, exist_ok=True)

    figure_files: list[str] = []
    plot_error: str | None = None
    plot_path: Path | None = None
    if run_plot:
        try:
            report, figure_files = attach_figures_to_report(report, work)
            if figure_files:
                plot_path = work / figure_files[0]
        except Exception as exc:  # noqa: BLE001
            plot_error = str(exc)[:300]

    return ValidationResult(
        report=report,
        university=university,
        logo_path=Path(university["logo_abs"]),
        work_dir=work,
        plot_path=plot_path,
        plot_error=plot_error,
        figure_files=figure_files,
    )


def report_to_resolved_dict(result: ValidationResult) -> dict[str, Any]:
    data = result.report.model_dump(mode="json")
    data["university_full_name"] = result.university["full_name"]
    data["university_logo_path"] = str(result.logo_path)
    data["plot_path"] = result.figure_files[0] if result.figure_files else ""
    # Ensure each task figures list uses filenames that exist beside the typst file
    for task in data.get("tasks", []):
        figs = []
        for name in task.get("figures") or []:
            path = result.work_dir / name
            if path.exists():
                figs.append(name)
        task["figures"] = figs
    return data
