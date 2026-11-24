"""Generate → validate → trace → render, plus locked-field editing and re-rendering."""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from src import storage
from src.inference import MODEL, LabDetails, StudentProfile, build_user_prompt, extract_json
from src.renderer_docx import render_docx
from src.renderer_pdf import find_typst, render_pdf
from src.schema import LabReportSchema, validate_report
from src.validator import (
    _NUMBER_RE,
    load_universities,
    summarize_trace,
    trace_tables,
    validate_and_prepare,
)

Emit = Callable[[str, dict[str, Any]], None]

MAX_RAW_LOG_CHARS = 12_000
EDITABLE_COVER_FIELDS = {
    "department", "course_code", "course_title", "lab_number", "experiment_title",
    "student_name", "registration_no", "section", "instructor", "submission_date",
}
EDITABLE_BODY_FIELDS = {"abstract", "apparatus", "methodology", "discussion", "conclusion"}


class PipelineError(Exception):
    """A failure the student can act on; ``code`` lets the UI pick its copy."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def check_raw_log(raw_log: str) -> str:
    text = raw_log.strip()
    if not text:
        return ""
    if len(text) > MAX_RAW_LOG_CHARS:
        raise PipelineError(
            "log_too_large",
            "This log is too long for one report. Keep the rows your lab manual asks for.",
        )
    if len(_NUMBER_RE.findall(text)) < 3:
        raise PipelineError("no_numbers", "No numeric readings were found in this file.")
    return text


def _flag_details(flag: str, report: LabReportSchema) -> dict[str, Any]:
    """Locate the table row a flag talks about and pull out before/after values."""
    detail: dict[str, Any] = {"text": flag, "table": None, "row": None, "from": None, "to": None}
    for t_idx, table in enumerate(report.report_body.tables):
        for r_idx, row in enumerate(table.rows):
            key = row[0].strip()
            if not key:
                continue
            patterns = (f"'{key}'", f"={key}", f"= {key}", f'"{key}"', f" {key} ")
            if any(p in f" {flag} " for p in patterns):
                detail["table"], detail["row"] = t_idx, r_idx
                break
        if detail["row"] is not None:
            break
    recorded = re.search(r"recorded as ([-\d.]+\s?[a-zA-Zµ%]+)", flag)
    normalised = re.search(r"normali[sz]ed to ([-\d.]+\s?[a-zA-Zµ%]+)", flag)
    if recorded and normalised:
        detail["from"], detail["to"] = recorded.group(1), normalised.group(1)
    return detail


def _apply_inputs(report: LabReportSchema, profile: StudentProfile, lab: LabDetails,
                  university_id: str | None) -> LabReportSchema:
    """Cover fields come from what the student typed, never from model guesses."""
    data = report.model_dump(mode="json")
    cover = data["cover_page"]
    cover.update(
        student_name=profile.name,
        registration_no=profile.registration_no,
        section=profile.section,
        instructor=profile.instructor,
        submission_date=profile.date,
        university_raw=profile.university,
        course_code=lab.course_code,
        course_title=lab.course_title,
        lab_number=lab.lab_number,
        experiment_title=lab.experiment_title,
        department=lab.department,
    )
    if university_id:
        cover["university_id"] = university_id
    return validate_report(data)


def _render(report_id: str, report: LabReportSchema, raw_log: str) -> dict[str, Any]:
    folder = storage.report_dir(report_id)
    work = folder / "work"
    result = validate_and_prepare(report, raw_log, work_dir=work, run_plot=True)

    files: dict[str, bool] = {"docx": False, "pdf": False}
    errors: dict[str, str] = {}
    if result.plot_error:
        errors["plot"] = result.plot_error

    try:
        render_docx(result, folder / f"{report_id}.docx")
        files["docx"] = True
    except Exception as exc:  # noqa: BLE001 — reported per file
        errors["docx"] = str(exc)

    try:
        find_typst()
    except FileNotFoundError:
        errors["pdf"] = "typst_missing"
    else:
        try:
            render_pdf(result, folder / f"{report_id}.pdf", work_dir=work)
            files["pdf"] = True
        except Exception as exc:  # noqa: BLE001
            errors["pdf"] = str(exc)

    files["plot"] = bool(result.plot_path and Path(result.plot_path).exists())
    return {"files": files, "render_errors": errors}


def _analysis(report: LabReportSchema, raw_log: str) -> dict[str, Any]:
    trace = trace_tables(report, raw_log)
    return {
        "trace": trace,
        "trace_summary": summarize_trace(trace),
        "flags": [_flag_details(f, report) for f in report.anomaly_check.flags],
    }


def generate(
    profile: StudentProfile,
    lab: LabDetails,
    raw_log: str,
    university_id: str | None,
    emit: Emit,
    cancel: threading.Event,
    raw_log_name: str | None = None,
    manual_text: str | None = None,
) -> dict[str, Any]:
    emit("stage", {"stage": "reading"})
    raw_log = check_raw_log(raw_log or "")
    if university_id and university_id not in load_universities():
        raise PipelineError("bad_university", "Unknown university selected.")
    if not MODEL.available:
        raise PipelineError("model_missing", "The LabPulse model file was not found.")

    prompt = build_user_prompt(profile, lab, raw_log, manual_text or "")
    report: LabReportSchema | None = None
    stats: dict[str, Any] = {}
    last_error = ""
    for attempt in (1, 2):
        emit("stage", {"stage": "writing", "attempt": attempt})
        result = MODEL.generate(
            prompt,
            on_token=lambda n: emit("tokens", {"count": n}),
            cancel=cancel,
        )
        stats = result.stats.as_dict()
        emit("stage", {"stage": "validating", "attempt": attempt})
        try:
            report = validate_report(extract_json(result.text))
            break
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)[:400]
            emit("retry", {"attempt": attempt, "reason": "invalid_output"})
    if report is None:
        raise PipelineError(
            "invalid_output",
            f"The model's report did not pass validation twice. ({last_error})",
        )

    report = _apply_inputs(report, profile, lab, university_id)
    report_id = storage.new_report_id(lab.course_code, lab.lab_number, profile.date)

    emit("stage", {"stage": "rendering"})
    rendered = _render(report_id, report, raw_log)
    now = storage.now_iso()
    record = {
        "id": report_id,
        "created_at": now,
        "updated_at": now,
        "report": report.model_dump(mode="json"),
        "raw_log": raw_log,
        "inputs": {
            "profile": profile.__dict__,
            "lab": lab.__dict__,
            "university_id": university_id,
            "raw_log_name": raw_log_name,
        },
        "stats": stats,
        **_analysis(report, raw_log),
        **rendered,
    }
    storage.save_record(report_id, record)
    return record


def apply_edits(report_id: str, cover: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    """Apply prose/cover edits; tables, equations, plot and audit stay locked."""
    record = storage.load_record(report_id)
    data = record["report"]

    locked = set(cover) - EDITABLE_COVER_FIELDS | set(body) - EDITABLE_BODY_FIELDS
    if locked:
        raise PipelineError(
            "locked_field",
            f"These parts come from your data and can't be edited: {', '.join(sorted(locked))}",
        )
    data["cover_page"].update(cover)
    data["report_body"].update(body)
    try:
        report = validate_report(data)
    except ValidationError as exc:
        raise PipelineError("invalid_edit", _friendly_validation(exc)) from exc

    rendered = _render(report_id, report, record["raw_log"])
    record.update(
        report=report.model_dump(mode="json"),
        updated_at=storage.now_iso(),
        **_analysis(report, record["raw_log"]),
        **rendered,
    )
    storage.save_record(report_id, record)
    return record


def _friendly_validation(exc: ValidationError) -> str:
    first = exc.errors()[0]
    field = ".".join(str(p) for p in first["loc"][-1:])
    return f"{field.replace('_', ' ').capitalize()}: {first['msg']}"
