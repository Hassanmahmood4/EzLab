"""Local, on-disk storage for the student profile and report history.

Everything lives under ``outputs/`` on the student's machine; nothing syncs.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "outputs"
PROFILE_PATH = DATA_DIR / "profile.json"
REPORTS_DIR = DATA_DIR / "reports"

_REPORT_ID = re.compile(r"^[A-Za-z0-9-]{3,64}$")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_profile() -> dict[str, Any] | None:
    if not PROFILE_PATH.exists():
        return None
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def save_profile(profile: dict[str, Any]) -> dict[str, Any]:
    _write_json(PROFILE_PATH, profile)
    return profile


def report_dir(report_id: str) -> Path:
    if not _REPORT_ID.match(report_id):
        raise ValueError("Invalid report id")
    return REPORTS_DIR / report_id


def new_report_id(course_code: str, lab_number: str, date: str) -> str:
    """Human-readable reference like LP-CS218-05-2026, unique on disk."""
    course = re.sub(r"[^A-Za-z0-9]", "", course_code).upper() or "LAB"
    lab_digits = re.sub(r"\D", "", lab_number) or "0"
    year = date[:4] if re.match(r"^\d{4}", date) else str(datetime.now().year)
    base = f"LP-{course}-{int(lab_digits):02d}-{year}"
    candidate, n = base, 2
    while (REPORTS_DIR / candidate).exists():
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def save_record(report_id: str, record: dict[str, Any]) -> None:
    _write_json(report_dir(report_id) / "record.json", record)


def load_record(report_id: str) -> dict[str, Any]:
    path = report_dir(report_id) / "record.json"
    if not path.exists():
        raise FileNotFoundError(report_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_records() -> list[dict[str, Any]]:
    if not REPORTS_DIR.exists():
        return []
    summaries = []
    for path in REPORTS_DIR.glob("*/record.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cover = record["report"]["cover_page"]
        summaries.append(
            {
                "id": record["id"],
                "created_at": record["created_at"],
                "updated_at": record.get("updated_at", record["created_at"]),
                "course_code": cover["course_code"],
                "course_title": cover["course_title"],
                "lab_number": cover["lab_number"],
                "experiment_title": cover["experiment_title"],
                "anomaly_status": record["report"]["anomaly_check"]["status"],
                "files": record.get("files", {}),
            }
        )
    return sorted(summaries, key=lambda s: s["created_at"], reverse=True)


def delete_record(report_id: str) -> None:
    path = report_dir(report_id)
    if not path.exists():
        raise FileNotFoundError(report_id)
    shutil.rmtree(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
