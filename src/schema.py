"""Strict Pydantic schema for EzLab task / code / output lab reports."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, field_validator


class CoverPage(BaseModel):
    university_id: str = Field(..., min_length=2)
    university_raw: str = Field(..., min_length=1)
    department: str
    course_code: str
    course_title: str
    lab_number: str
    experiment_title: str
    student_name: str
    registration_no: str
    section: str = ""
    instructor: str = ""
    submission_date: str = Field(..., description="ISO date YYYY-MM-DD")
    semester: str = ""

    @field_validator("submission_date")
    @classmethod
    def _iso_date(cls, value: str) -> str:
        parts = value.split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("submission_date must be YYYY-MM-DD")
        return value


class LabTask(BaseModel):
    number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    prompt: str = ""
    code: str = Field(..., min_length=1)
    output: str = ""
    figures: list[str] = Field(default_factory=list, description="PNG filenames next to the report")


class LabReportSchema(BaseModel):
    """Canonical report: cover page + one entry per manual task."""

    cover_page: CoverPage
    tasks: list[LabTask] = Field(..., min_length=1)


SYSTEM_PROMPT = (
    "You are an offline university CS lab assistant. "
    "For each lab-manual task, write a complete student solution as JSON only: "
    '{"code": "<full source code>", "output": "<realistic terminal output>"}. '
    "Prefer Python unless the task requires another language. "
    "Code must be runnable in spirit and match the task. "
    "When the task asks for a plot/figure/histogram/pairplot, use matplotlib/seaborn and "
    "always plt.savefig('plot.png', dpi=150, bbox_inches='tight') so the graph can be "
    "embedded under Visualization Output in the report (do not rely on plt.show alone). "
    "Output should look like real console output for that code. "
    "No markdown fences, no commentary outside JSON."
)


def _coerce_report_dict(data: dict) -> dict:
    out = dict(data)
    cover = out.get("cover_page")
    if isinstance(cover, dict):
        cover = dict(cover)
        lab_no = str(cover.get("lab_number", "")).strip()
        if lab_no and not lab_no.lower().startswith("lab"):
            cover["lab_number"] = (
                f"Lab {lab_no.zfill(2)}" if lab_no.isdigit() else f"Lab {lab_no}"
            )
        out["cover_page"] = cover

    tasks = out.get("tasks")
    if isinstance(tasks, dict):
        tasks = [tasks]
    if isinstance(tasks, list):
        fixed: list[dict] = []
        for i, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                continue
            t = dict(task)
            t["number"] = int(t.get("number") or i)
            t["title"] = str(t.get("title") or f"Task {t['number']}").strip() or f"Task {t['number']}"
            t["prompt"] = str(t.get("prompt") or "")
            t["code"] = str(t.get("code") or "")
            t["output"] = str(t.get("output") or "")
            figs = t.get("figures") or []
            if isinstance(figs, str):
                figs = [figs]
            t["figures"] = [str(f) for f in figs if str(f).strip()]
            if not t["code"].strip():
                continue
            fixed.append(t)
        out["tasks"] = fixed
    return out


def validate_report(payload: dict | str) -> LabReportSchema:
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload
    if not isinstance(data, dict):
        raise ValueError("Report payload must be a JSON object")
    return LabReportSchema.model_validate(_coerce_report_dict(data))
