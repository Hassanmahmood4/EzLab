"""Parse lab-manual tasks, ask the model for code/output, render Word/PDF."""

from __future__ import annotations

import json
import re
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from src import storage
from src.code_runner import (
    looks_like_c,
    looks_like_python,
    polish_python_solution,
    python_syntax_ok,
)
from src.inference import MODEL, LabDetails, StudentProfile, extract_json
from src.manual_parser import extract_tasks
from src.renderer_docx import render_docx
from src.renderer_pdf import find_typst, render_pdf
from src.schema import LabReportSchema, validate_report
from src.task_solutions import (
    build_fallback_solution,
    is_usable_solution,
    match_curated_solution,
)
from src.validator import load_universities, validate_and_prepare

Emit = Callable[[str, dict[str, Any]], None]

EDITABLE_COVER_FIELDS = {
    "department", "course_code", "course_title", "lab_number", "experiment_title",
    "student_name", "registration_no", "section", "instructor", "submission_date", "semester",
}


class PipelineError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _normalize_lab_number(lab_number: str) -> str:
    text = lab_number.strip()
    if text and not text.lower().startswith("lab"):
        return f"Lab {text.zfill(2)}" if text.isdigit() else f"Lab {text}"
    return text or "Lab 01"


def _build_cover(
    profile: StudentProfile,
    lab: LabDetails,
    university_id: str | None,
    semester: str = "",
) -> dict[str, Any]:
    uid = university_id or "nust"
    return {
        "university_id": uid,
        "university_raw": profile.university or uid,
        "department": lab.department,
        "course_code": lab.course_code,
        "course_title": lab.course_title,
        "lab_number": _normalize_lab_number(lab.lab_number),
        "experiment_title": lab.experiment_title,
        "student_name": profile.name,
        "registration_no": profile.registration_no,
        "section": profile.section,
        "instructor": profile.instructor,
        "submission_date": profile.date,
        "semester": semester or "",
    }


def _clean_task_title(title: str, number: int = 1) -> str:
    """Strip PDF TOC dots / page crumbs from exercise titles."""
    t = (title or "").strip()
    t = re.sub(r"[\.…]{2,}\s*\d*\s*$", "", t)
    t = re.sub(r"\s*\.{3,}\s*", " ", t)
    t = re.sub(r"\s+\d{1,3}\s*$", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" —-.:")
    if len(t) > 90:
        t = t[:87].rstrip() + "…"
    return t or f"Task {number}"


def _task_shells_from_manual(manual_text: str, lab: LabDetails) -> list[dict[str, Any]]:
    parsed = extract_tasks(manual_text or "")
    if parsed:
        return [
            {
                "number": t.number,
                "title": _clean_task_title(t.title, t.number),
                "prompt": t.prompt,
                "code": "",
                "output": "",
            }
            for t in parsed
        ]
    # Fallback: one task covering the whole experiment
    prompt = (manual_text or "").strip()
    if len(prompt) < 20:
        raise PipelineError(
            "no_tasks",
            "Upload a lab manual with Exercises/Tasks (1. 2. 3. …) or Task 1 headings.",
        )
    return [
        {
            "number": 1,
            "title": lab.experiment_title or "Lab exercise",
            "prompt": prompt[:4000],
            "code": "",
            "output": "",
        }
    ]


def _merge_task_shells(
    from_manual: list[dict[str, Any]],
    from_client: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Manual parse is authoritative; client may only supply pre-written code/output."""
    if not from_manual:
        return from_client or []
    by_number: dict[int, dict[str, Any]] = {}
    for raw in from_client or []:
        if not isinstance(raw, dict):
            continue
        try:
            number = int(raw.get("number") or 0)
        except (TypeError, ValueError):
            continue
        if number:
            by_number[number] = raw
    merged: list[dict[str, Any]] = []
    for shell in from_manual:
        number = int(shell["number"])
        client = by_number.get(number, {})
        code = str(client.get("code") or "").strip()
        output = str(client.get("output") or "").strip()
        merged.append(
            {
                **shell,
                "code": code if is_usable_solution(code, output) else "",
                "output": output if is_usable_solution(code, output) else "",
            }
        )
    return merged


def _task_wants_c(task: dict[str, Any], lab: LabDetails) -> bool:
    task_blob = f"{task.get('title') or ''} {task.get('prompt') or ''}".lower()
    lab_blob = f"{lab.experiment_title or ''} {lab.course_title or ''}".lower()
    needs_c = any(
        k in task_blob
        for k in (
            "fork(",
            "fork ",
            "execl",
            "execvp",
            "execv",
            "unistd",
            "sys/wait",
            "write a c program",
            "c program that",
            "process control with fork",
            "pipe(",
            "ipc",
        )
    ) or (
        any(k in task_blob for k in ("fork", "exec", "pipe"))
        and any(k in lab_blob for k in ("operating system", "process control"))
    )
    if any(
        k in task_blob
        for k in (
            "sklearn",
            "scikit",
            "linearregression",
            "savefig",
            "pairplot",
            "learning curve",
            "lasso",
            "rmse",
            "r²",
            "r2",
            "regression",
            "matplotlib",
        )
    ):
        needs_c = False
    return needs_c


def _polish_solution(
    task: dict[str, Any],
    code: str,
    output: str,
    *,
    lang: str,
) -> dict[str, str]:
    code = (code or "").rstrip() + "\n"
    output = (output or "").rstrip() + "\n"
    if lang != "Python" or looks_like_c(code) or not looks_like_python(code):
        return {"code": code, "output": output}
    if not python_syntax_ok(code):
        return {"code": code, "output": output}
    with tempfile.TemporaryDirectory(prefix="ezlab_task_") as tmp:
        return polish_python_solution(
            code,
            output,
            Path(tmp),
            task_number=int(task.get("number") or 1),
        )


def _generate_task_solution(
    task: dict[str, Any],
    lab: LabDetails,
    emit: Emit,
    cancel: threading.Event,
) -> dict[str, str]:
    """Prefer curated templates; else model with syntax/language gate; polish Python stdout."""
    existing_code = str(task.get("code") or "").strip()
    existing_out = str(task.get("output") or "").strip()
    if is_usable_solution(existing_code, existing_out):
        lang = "C" if looks_like_c(existing_code) else "Python"
        return _polish_solution(task, existing_code, existing_out, lang=lang)

    # 1) Curated template wins when the exercise clearly matches
    curated = match_curated_solution(task, lab)
    if curated is not None and is_usable_solution(curated["code"], curated.get("output", "")):
        lang = "C" if looks_like_c(curated["code"]) else "Python"
        return _polish_solution(task, curated["code"], curated.get("output", ""), lang=lang)

    needs_c = _task_wants_c(task, lab)
    lang = "C" if needs_c else "Python"
    task_blob = f"{task.get('title') or ''} {task.get('prompt') or ''}".lower()
    label = "Exercise" if "exercise" in task_blob else "Task"
    plot_hint = (
        " If the task needs a plot/figure, use matplotlib and "
        "plt.savefig('plot.png', dpi=150, bbox_inches='tight')."
        if not needs_c
        else ""
    )
    user = (
        f"Course: {lab.course_code} — {lab.course_title}\n"
        f"Lab: {lab.lab_number} — {lab.experiment_title}\n"
        f"{label} {task['number']} — {task['title']}\n"
        f"{task.get('prompt') or ''}\n\n"
        f"Write a complete runnable {lang} solution for this single task. "
        "Return JSON only with keys code and output. "
        "No placeholders, no markdown, no invented APIs."
        f"{plot_hint}"
    )
    try:
        if cancel.is_set():
            raise RuntimeError("cancelled")
        result = MODEL.generate(
            user,
            on_token=lambda n: emit("tokens", {"count": n}),
            cancel=cancel,
        )
        obj = json.loads(extract_json(result.text))
        if isinstance(obj.get("tasks"), list) and obj["tasks"]:
            obj = obj["tasks"][0]
        code = str(obj.get("code") or "").strip()
        output = str(obj.get("output") or "").strip()
        if lang == "Python" and looks_like_c(code):
            code = ""
        if lang == "C" and (
            "import sklearn" in code
            or "import matplotlib" in code
            or (looks_like_python(code) and "def " in code[:200] and not looks_like_c(code))
        ):
            code = ""
        if lang == "Python" and code and not python_syntax_ok(code):
            code = ""
        if is_usable_solution(code, output):
            polished = _polish_solution(task, code, output, lang=lang)
            # If Python failed to run and we have a curated match, prefer curated
            if lang == "Python" and polished["code"].strip() == code.strip():
                # re-check exec: if polish kept model output but code was broken at runtime,
                # try curated again when available
                pass
            return polished
    except Exception:
        pass

    fallback = build_fallback_solution(task, lab)
    flang = "C" if looks_like_c(fallback["code"]) else "Python"
    return _polish_solution(task, fallback["code"], fallback.get("output", ""), lang=flang)


def _normalize_completed_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for i, raw in enumerate(tasks, start=1):
        code = str(raw.get("code") or "").strip()
        if not code:
            continue
        number = int(raw.get("number") or i)
        title = _clean_task_title(
            str(raw.get("title") or f"Task {number}").strip() or f"Task {number}",
            number,
        )
        cleaned.append(
            {
                "number": number,
                "title": title,
                "prompt": str(raw.get("prompt") or "").strip(),
                "code": code,
                "output": str(raw.get("output") or "").strip(),
            }
        )
    if not cleaned:
        raise PipelineError("invalid_output", "The model did not return code for any task.")
    cleaned.sort(key=lambda t: t["number"])
    return cleaned


def _render(report_id: str, report: LabReportSchema) -> dict[str, Any]:
    folder = storage.report_dir(report_id)
    work = folder / "work"
    result = validate_and_prepare(report, work_dir=work, run_plot=True)

    files: dict[str, bool] = {
        "docx": False,
        "pdf": False,
        "plot": bool(result.figure_files),
        "preview": False,
    }
    errors: dict[str, str] = {}
    if result.plot_error:
        errors["plot"] = result.plot_error

    try:
        render_docx(result, folder / f"{report_id}.docx")
        files["docx"] = True
    except Exception as exc:  # noqa: BLE001
        errors["docx"] = str(exc)

    try:
        find_typst()
    except FileNotFoundError:
        errors["pdf"] = "typst_missing"
    else:
        try:
            render_pdf(result, folder / f"{report_id}.pdf", work_dir=work)
            files["pdf"] = True
            files["preview"] = (work / "preview.png").exists()
        except Exception as exc:  # noqa: BLE001
            errors["pdf"] = str(exc)

    # Persist figure filenames on the saved report JSON
    return {
        "files": files,
        "render_errors": errors,
        "report": result.report.model_dump(mode="json"),
    }


def generate(
    profile: StudentProfile,
    lab: LabDetails,
    university_id: str | None,
    emit: Emit,
    cancel: threading.Event,
    tasks: list[dict[str, Any]] | None = None,
    semester: str = "",
    manual_text: str | None = None,
    raw_log: str = "",
    raw_log_name: str | None = None,
) -> dict[str, Any]:
    del raw_log, raw_log_name
    emit("stage", {"stage": "reading"})
    if cancel.is_set():
        raise PipelineError("cancelled", "Cancelled.")
    if university_id and university_id not in load_universities():
        raise PipelineError("bad_university", "Unknown university selected.")
    if not MODEL.available:
        raise PipelineError("model_missing", "The EzLab model file was not found.")

    shells = _merge_task_shells(
        _task_shells_from_manual(manual_text or "", lab),
        tasks,
    )

    emit("stage", {"stage": "writing", "attempt": 1})
    filled: list[dict[str, Any]] = []
    total_tokens = 0
    for task in shells:
        if cancel.is_set():
            raise PipelineError("cancelled", "Cancelled.")
        emit("stage", {"stage": "writing", "task": task["number"]})
        solution = _generate_task_solution(task, lab, emit, cancel)
        filled.append({**task, **solution})

    emit("stage", {"stage": "validating", "attempt": 1})
    try:
        report = validate_report(
            {
                "cover_page": _build_cover(profile, lab, university_id, semester),
                "tasks": _normalize_completed_tasks(filled),
            }
        )
    except (ValidationError, ValueError) as exc:
        raise PipelineError("invalid_output", str(exc)[:400]) from exc

    report_id = storage.new_report_id(lab.course_code, lab.lab_number, profile.date)
    emit("stage", {"stage": "rendering"})
    rendered = _render(report_id, report)
    now = storage.now_iso()
    record = {
        "id": report_id,
        "created_at": now,
        "updated_at": now,
        "report": report.model_dump(mode="json"),
        "raw_log": "",
        "inputs": {
            "profile": profile.__dict__,
            "lab": lab.__dict__,
            "university_id": university_id,
            "semester": semester,
            "manual_text": (manual_text or "")[:20000],
        },
        "stats": {
            "tokens": total_tokens,
            "seconds": 0.0,
            "tokens_per_second": 0.0,
            "peak_rss_gb": 0.0,
            "format_only": False,
            "tasks_generated": len(report.tasks),
        },
        "trace": [],
        "trace_summary": {"grounded": 0, "normalised": 0, "derived": 0, "ungrounded": 0, "total": 0},
        "flags": [],
        **rendered,
    }
    storage.save_record(report_id, record)
    return record


def apply_edits(
    report_id: str,
    cover: dict[str, Any],
    tasks: list[dict[str, Any]] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del body
    record = storage.load_record(report_id)
    data = record["report"]

    locked = set(cover) - EDITABLE_COVER_FIELDS
    if locked:
        raise PipelineError(
            "locked_field",
            f"These cover fields can't be edited: {', '.join(sorted(locked))}",
        )
    data["cover_page"].update(cover)

    if tasks is not None:
        data["tasks"] = _normalize_completed_tasks(tasks)

    try:
        report = validate_report(data)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"][-1:])
        raise PipelineError(
            "invalid_edit",
            f"{field.replace('_', ' ').capitalize()}: {first['msg']}",
        ) from exc

    rendered = _render(report_id, report)
    record.update(
        report=report.model_dump(mode="json"),
        updated_at=storage.now_iso(),
        **rendered,
    )
    storage.save_record(report_id, record)
    return record
