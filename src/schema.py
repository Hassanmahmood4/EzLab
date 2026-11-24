"""Strict Pydantic schema for LabPulse lab-report JSON output."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnomalyStatus(str, Enum):
    ok = "ok"
    warning = "warning"
    error = "error"


class CoverPage(BaseModel):
    university_id: str = Field(..., min_length=2, description="Canonical slug from assets/universities.json")
    university_raw: str = Field(..., min_length=1, description="Noisy campus shorthand from the student input")
    department: str
    course_code: str
    course_title: str
    lab_number: str
    experiment_title: str
    student_name: str
    registration_no: str
    section: str
    instructor: str
    submission_date: str = Field(..., description="ISO date YYYY-MM-DD")

    @field_validator("submission_date")
    @classmethod
    def _iso_date(cls, value: str) -> str:
        parts = value.split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("submission_date must be YYYY-MM-DD")
        return value


class AnomalyCheck(BaseModel):
    status: AnomalyStatus
    flags: list[str] = Field(default_factory=list)


class ReportTable(BaseModel):
    caption: str
    headers: list[str] = Field(..., min_length=1)
    rows: list[list[str]] = Field(..., min_length=1)

    @field_validator("rows")
    @classmethod
    def _row_width(cls, rows: list[list[str]], info) -> list[list[str]]:
        headers = info.data.get("headers") or []
        width = len(headers)
        for i, row in enumerate(rows):
            if len(row) != width:
                raise ValueError(f"row {i} has {len(row)} cells, expected {width}")
        return rows


class ReportBody(BaseModel):
    abstract: str = Field(..., min_length=40)
    apparatus: list[str] = Field(..., min_length=1)
    methodology: str = Field(..., min_length=40)
    equations_latex: list[str] = Field(default_factory=list)
    tables: list[ReportTable] = Field(..., min_length=1)
    plot_code: str = Field(..., min_length=20, description="matplotlib code that saves plot.png")
    discussion: str = Field(..., min_length=40)
    conclusion: str = Field(..., min_length=20)

    @field_validator("plot_code")
    @classmethod
    def _saves_plot(cls, value: str) -> str:
        if "savefig" not in value:
            raise ValueError("plot_code must call savefig('plot.png', ...)")
        return value


class LabReportSchema(BaseModel):
    """Canonical model output for every LabPulse generation."""

    cover_page: CoverPage
    anomaly_check: AnomalyCheck
    report_body: ReportBody


SYSTEM_PROMPT = (
    "You are an offline university lab report generator. "
    "Write a complete submission-ready lab report from the lab manual and student details. "
    "If a raw experimental log is provided, ground every table number in it and audit unit mismatches. "
    "If no log is provided, invent typical, internally consistent measurements for this experiment. "
    "Output strictly valid JSON matching the required schema. JSON only."
)


def validate_report(payload: dict | str) -> LabReportSchema:
    if isinstance(payload, str):
        return LabReportSchema.model_validate_json(payload)
    return LabReportSchema.model_validate(payload)
