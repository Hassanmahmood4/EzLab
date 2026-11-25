#!/usr/bin/env python3
"""Smoke-test task report generation (stub) → .docx / .pdf."""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LABPULSE_STUB", "1")

from src.inference import LabDetails, StudentProfile  # noqa: E402
from src.pipeline import generate  # noqa: E402


def main() -> int:
    profile = StudentProfile(
        name="Hassan Ali",
        registration_no="21I-1234",
        section="BCS-2A",
        university="NUST",
        instructor="Dr. Ayesha Khan",
        date="2026-11-25",
    )
    lab = LabDetails(
        course_code="CS-100",
        course_title="Programming Fundamentals Lab",
        lab_number="Lab 01",
        experiment_title="Input, Loops and Functions",
        department="Department of Computer Science",
    )
    manual = (
        "Lab 01: Input, Loops and Functions\n\n"
        "Task 1 — Hello and sum\n"
        "Write a program that reads two integers and prints their sum.\n\n"
        "Task 2 — Factorial\n"
        "Write a function that returns n! and print factorial(5).\n"
    )

    def emit(event: str, payload: dict) -> None:
        if event == "stage":
            print("stage", payload)

    record = generate(
        profile,
        lab,
        "nust",
        emit,
        threading.Event(),
        manual_text=manual,
        semester="2",
    )
    print(json.dumps({"id": record["id"], "files": record["files"], "tasks": len(record["report"]["tasks"])}, indent=2))
    return 0 if record["files"].get("docx") else 1


if __name__ == "__main__":
    raise SystemExit(main())
