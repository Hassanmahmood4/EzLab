#!/usr/bin/env python3
"""Multi-subject production readiness suite for EzLab.

Runs end-to-end generate() across CS labs, scores PDF/DOCX/code quality,
and exits non-zero if the pass rate is below the bar.

Usage:
  .venv/bin/python scripts/prod_ready_suite.py
  LABPULSE_SUITE_SKIP_MODEL=1 .venv/bin/python scripts/prod_ready_suite.py  # templates only
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Prefer real model; stub only if explicitly requested
if os.environ.get("LABPULSE_SUITE_STUB") == "1":
    os.environ["LABPULSE_STUB"] = "1"

from src.code_runner import looks_like_c, looks_like_python, python_syntax_ok  # noqa: E402
from src.inference import LabDetails, StudentProfile  # noqa: E402
from src.pipeline import generate  # noqa: E402
from src.task_solutions import is_usable_solution  # noqa: E402
from src.validator import load_universities  # noqa: E402


@dataclass
class CaseResult:
    id: str
    ok: bool
    seconds: float
    report_id: str = ""
    files: dict[str, bool] = field(default_factory=dict)
    tasks: int = 0
    stub_tasks: int = 0
    bad_syntax: int = 0
    logo_ok: bool = False
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


FIXTURES: list[dict[str, Any]] = [
    {
        "id": "pf_basics",
        "university_id": "fast_nuces",
        "profile": StudentProfile(
            name="Hassan Ali",
            registration_no="21L-5042",
            section="BCS-2A",
            university="FAST-NUCES",
            instructor="Dr. Sana Malik",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-100",
            course_title="Programming Fundamentals Lab",
            lab_number="Lab 01",
            experiment_title="Input, Loops and Functions",
            department="Department of Computer Science",
        ),
        "manual": (
            "Lab 01: Input, Loops and Functions\n\n"
            "Task 1 — Hello and sum\n"
            "Write a program that reads two integers and prints their sum.\n\n"
            "Task 2 — Factorial\n"
            "Write a function that returns n! for n >= 0 and print factorial(5).\n\n"
            "Task 3 — Primality sieve\n"
            "Print the list of prime numbers less than or equal to 30.\n"
        ),
        "semester": "2",
    },
    {
        "id": "oop_inheritance",
        "university_id": "comsats",
        "profile": StudentProfile(
            name="Ayesha Khan",
            registration_no="FA21-BCS-012",
            section="BCS-3B",
            university="COMSATS",
            instructor="Mr. Usman Tariq",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-217",
            course_title="Object Oriented Programming Lab",
            lab_number="Lab 04",
            experiment_title="Inheritance and Polymorphism",
            department="Department of Computer Science",
        ),
        "manual": (
            "Lab 04 — Inheritance and Polymorphism\n\n"
            "Task 1 — Student inheritance\n"
            "Create a base Person class and a derived Student class. "
            "Demonstrate polymorphism via a describe() method.\n\n"
            "Task 2 — Encapsulation with getters\n"
            "Implement a BankAccount with private balance, deposit and withdraw.\n"
        ),
        "semester": "3",
    },
    {
        "id": "dsa_sorting",
        "university_id": "nust",
        "profile": StudentProfile(
            name="Bilal Ahmed",
            registration_no="21I-1101",
            section="BCS-4A",
            university="NUST",
            instructor="Dr. Farah Naz",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-218",
            course_title="Data Structures and Algorithms Lab",
            lab_number="Lab 05",
            experiment_title="MergeSort vs QuickSort Runtime",
            department="School of Electrical Engineering and Computer Science",
        ),
        "manual": (
            "Lab 05 — Sorting Benchmarks\n\n"
            "Task 1 — Compare MergeSort and QuickSort\n"
            "Implement MergeSort and QuickSort and benchmark runtime for N=1000,5000,10000.\n\n"
            "Task 2 — Binary search\n"
            "Implement binary search on a sorted array and report indices for several targets.\n"
        ),
        "semester": "4",
    },
    {
        "id": "os_pipes",
        "university_id": "giki",
        "profile": StudentProfile(
            name="Omar Siddiqui",
            registration_no="2021-CS-44",
            section="CS-5A",
            university="GIKI",
            instructor="Dr. Imran Qureshi",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-342",
            course_title="Operating Systems Lab",
            lab_number="Lab 09",
            experiment_title="Pipes and Inter-Process Communication",
            department="Faculty of Computer Science and Engineering",
        ),
        "manual": (
            "Lab 09 — Pipes and IPC\n\n"
            "Task 1 — What is IPC / What is a pipe?\n"
            "Write a short C program demonstrating a pipe between parent and child.\n\n"
            "Task 2 — Pipe in C: parent creates pipe, child writes, parent reads\n"
            "Implement fork + pipe IPC in C.\n\n"
            "Task 3 — fork and exec\n"
            "Write a C program that forks and uses execvp to run ls -l.\n"
        ),
        "semester": "5",
    },
    {
        "id": "db_joins",
        "university_id": "itu",
        "profile": StudentProfile(
            name="Fatima Noor",
            registration_no="21I-TU-332",
            section="BSE-4A",
            university="ITU",
            instructor="Ms. Rabia Shah",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-310",
            course_title="Database Systems Lab",
            lab_number="Lab 03",
            experiment_title="SQL Joins and Aggregation",
            department="Department of Computer Science",
        ),
        "manual": (
            "Lab 03 — SQL Joins\n\n"
            "Task 1 — Student/grades join query\n"
            "Using SQLite, create students and grades tables and SELECT names with marks >= 90 via JOIN.\n\n"
            "Task 2 — Index vs query time\n"
            "Measure query time on a logs table before and after creating an index on user_id.\n"
        ),
        "semester": "4",
    },
    {
        "id": "net_latency",
        "university_id": "bahria",
        "profile": StudentProfile(
            name="Zainab Rizvi",
            registration_no="01-134221-088",
            section="BCS-6A",
            university="Bahria University",
            instructor="Mr. Kamran Ali",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-401",
            course_title="Computer Networks Lab",
            lab_number="Lab 07",
            experiment_title="Latency, Throughput and Packet Loss",
            department="Department of Computer Science",
        ),
        "manual": (
            "Lab 07 — Latency Simulation\n\n"
            "Task 1 — Simulate RTT / latency / packet loss\n"
            "Simulate round-trip times and report mean, stdev and approximate loss rate.\n\n"
            "Task 2 — HTTP status and page-load timings\n"
            "From a small API response log, count status codes and average latency.\n"
        ),
        "semester": "6",
    },
    {
        "id": "discrete_logic",
        "university_id": "lums",
        "profile": StudentProfile(
            name="Saad Mir",
            registration_no="24100123",
            section="CS-200",
            university="LUMS",
            instructor="Dr. Mehreen Ahmed",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-210",
            course_title="Discrete Structures Lab",
            lab_number="Lab 02",
            experiment_title="Propositional Logic Truth Tables",
            department="Syed Babar Ali School of Science and Engineering",
        ),
        "manual": (
            "Lab 02 — Truth Tables\n\n"
            "Task 1 — Implication truth table\n"
            "Build a truth table for P→Q and show it equals ¬P∨Q.\n\n"
            "Task 2 — DFA accept/reject\n"
            "Implement a DFA that accepts binary strings with an even number of 0s.\n"
        ),
        "semester": "2",
    },
    {
        "id": "ml_regression_smoke",
        "university_id": "pieas",
        "profile": StudentProfile(
            name="Hira Sheikh",
            registration_no="PIEAS-21-77",
            section="CS-6A",
            university="PIEAS",
            instructor="Dr. Naveed Anjum",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-212",
            course_title="Machine Learning Lab",
            lab_number="Lab 06",
            experiment_title="Regression with Scikit-learn",
            department="Department of Computer and Information Sciences",
        ),
        "manual": (
            "Lab 06 — Regression\n\n"
            "Exercises / Tasks\n"
            "1. By hand: For the points (1, 2), (2, 3), (3, 5), (4, 4), (5, 6), "
            "compute the slope, intercept, SSE and R². Check with LinearRegression.\n\n"
            "2. Other single features: Fit a simple regression of price on each feature. "
            "Tabulate test R² and RMSE and rank the features.\n"
        ),
        "semester": "6",
    },
]


def _ml_full_manual() -> str:
    presets = json.loads((ROOT / "assets" / "presets.json").read_text(encoding="utf-8"))
    for item in presets:
        if item.get("id") == "ml_regression_exercises":
            return str(item["manual_text"])
    raise RuntimeError("ml_regression_exercises preset missing")


FIXTURES.append(
    {
        "id": "ml_full_nine",
        "university_id": "riphah",
        "profile": StudentProfile(
            name="Areeba Malik",
            registration_no="19F-9222",
            section="BIT-6A",
            university="Riphah",
            instructor="Ms. Hira Sheikh",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-212",
            course_title="Machine Learning",
            lab_number="Lab 06",
            experiment_title="Regression Algorithms with Scikit-learn",
            department="Faculty of Computing",
        ),
        "manual": _ml_full_manual(),
        "semester": "6",
    }
)

FIXTURES.append(
    {
        "id": "pf_wordfreq_edge",
        "university_id": "iba",
        "profile": StudentProfile(
            name="Noor Fatima",
            registration_no="20241-1234",
            section="BCS-1A",
            university="IBA",
            instructor="Ms. Sana Rauf",
            date="2026-11-26",
        ),
        "lab": LabDetails(
            course_code="CS-101",
            course_title="Introduction to Programming",
            lab_number="Lab 03",
            experiment_title="String Processing Utilities",
            department="School of Mathematics and Computer Science",
        ),
        "manual": (
            "Lab 03 — Strings\n\n"
            "Task 1 — Word frequency counter\n"
            "Write a Python program that counts word frequencies in the sentence "
            '"the cat sat on the mat and the cat ran" and prints words sorted by count descending.\n\n'
            "Task 2 — Reverse a string\n"
            "Implement reverse_string and demo on hello / EzLab / 12345.\n"
        ),
        "semester": "1",
    }
)


def _is_stub_code(code: str) -> bool:
    low = code.lower()
    return (
        "completed the steps required by this exercise" in low
        or "solution placeholder" in low
        or "see accompanying figures" in low
        or "replace after reviewing" in low
    )


def _score_record(case_id: str, record: dict[str, Any], university_id: str) -> CaseResult:
    result = CaseResult(
        id=case_id,
        ok=False,
        seconds=0.0,
        report_id=str(record.get("id") or ""),
        files=dict(record.get("files") or {}),
    )
    report = record.get("report") or {}
    cover = report.get("cover_page") or {}
    tasks = report.get("tasks") or []
    result.tasks = len(tasks)

    registry = load_universities()
    logo_rel = registry.get(university_id, {}).get("logo_path", "")
    logo_path = ROOT / logo_rel if logo_rel else None
    result.logo_ok = bool(logo_path and logo_path.exists() and logo_path.stat().st_size > 20_000)

    if not result.files.get("docx"):
        result.errors.append("docx_missing")
    if not result.files.get("pdf"):
        result.errors.append("pdf_missing:" + str((record.get("render_errors") or {}).get("pdf", "")))
    if cover.get("university_id") != university_id:
        result.errors.append("university_mismatch")
    if not result.logo_ok:
        result.notes.append("logo_small_or_missing")

    for t in tasks:
        code = str(t.get("code") or "")
        output = str(t.get("output") or "")
        if not is_usable_solution(code, output):
            result.errors.append(f"task_{t.get('number')}_unusable")
        if _is_stub_code(code):
            result.stub_tasks += 1
            result.errors.append(f"task_{t.get('number')}_generic_stub")
        if looks_like_python(code) and not looks_like_c(code) and not python_syntax_ok(code):
            result.bad_syntax += 1
            result.errors.append(f"task_{t.get('number')}_syntax")
        title = str(t.get("title") or "")
        if "...." in title or title.endswith(".."):
            result.errors.append(f"task_{t.get('number')}_noisy_title")

    result.ok = (
        result.files.get("docx") is True
        and result.files.get("pdf") is True
        and result.tasks >= 1
        and result.stub_tasks == 0
        and result.bad_syntax == 0
        and not any(e.startswith("task_") and e.endswith("_unusable") for e in result.errors)
        and "university_mismatch" not in result.errors
    )
    return result


def run_case(fx: dict[str, Any]) -> CaseResult:
    events: list[str] = []

    def emit(event: str, payload: dict) -> None:
        if event == "stage":
            events.append(str(payload.get("stage")))

    t0 = time.perf_counter()
    try:
        record = generate(
            fx["profile"],
            fx["lab"],
            fx["university_id"],
            emit,
            threading.Event(),
            manual_text=fx["manual"],
            semester=fx.get("semester", ""),
        )
        result = _score_record(fx["id"], record, fx["university_id"])
        result.seconds = time.perf_counter() - t0
        result.notes.append("stages=" + ">".join(events[-6:]))
        return result
    except Exception as exc:  # noqa: BLE001
        result = CaseResult(
            id=fx["id"],
            ok=False,
            seconds=time.perf_counter() - t0,
            errors=[f"exception:{exc}"],
            notes=[traceback.format_exc(limit=3)],
        )
        return result


def main() -> int:
    print("EzLab production suite")
    print(f"fixtures={len(FIXTURES)} cwd={ROOT}")
    results: list[CaseResult] = []
    for fx in FIXTURES:
        print(f"\n=== {fx['id']} ({fx['university_id']}) ===")
        result = run_case(fx)
        results.append(result)
        status = "PASS" if result.ok else "FAIL"
        print(
            f"{status}  {result.seconds:.1f}s  tasks={result.tasks}  "
            f"docx={result.files.get('docx')} pdf={result.files.get('pdf')}  "
            f"stubs={result.stub_tasks} logo_ok={result.logo_ok}"
        )
        if result.errors:
            print("  errors:", "; ".join(result.errors[:8]))
        if result.report_id:
            print("  report:", result.report_id)

    passed = sum(1 for r in results if r.ok)
    total = len(results)
    summary = {
        "passed": passed,
        "total": total,
        "pass_rate": round(100.0 * passed / total, 1) if total else 0.0,
        "cases": [
            {
                "id": r.id,
                "ok": r.ok,
                "seconds": round(r.seconds, 2),
                "report_id": r.report_id,
                "files": r.files,
                "tasks": r.tasks,
                "stub_tasks": r.stub_tasks,
                "logo_ok": r.logo_ok,
                "errors": r.errors,
            }
            for r in results
        ],
    }
    out = ROOT / "outputs" / "prod_suite_last.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSUMMARY  {passed}/{total} passed ({summary['pass_rate']}%)")
    print(f"wrote {out}")

    # Bar for Friday submit: all curated fixtures must pass
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
