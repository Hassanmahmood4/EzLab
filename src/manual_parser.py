"""Extract text and lab fields from an uploaded lab manual (.txt, .md, .pdf, .docx).

Parsing is fully local. Extracted fields only pre-fill the lab details form; the
model prompt always uses the structured fields the student confirms.
"""

from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}
MAX_MANUAL_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 20_000


class ManualParseError(ValueError):
    pass


@dataclass
class ManualFields:
    course_code: str = ""
    course_title: str = ""
    lab_number: str = ""
    experiment_title: str = ""
    department: str = ""


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:20])


def _docx_text(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(lines)


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ManualParseError("Use a .txt, .md, .pdf or .docx lab manual.")
    if len(data) > MAX_MANUAL_BYTES:
        raise ManualParseError("This manual is larger than 10 MB.")
    try:
        if suffix == ".pdf":
            text = _pdf_text(data)
        elif suffix == ".docx":
            text = _docx_text(data)
        else:
            text = data.decode("utf-8", errors="replace")
    except ManualParseError:
        raise
    except Exception as exc:  # noqa: BLE001 — corrupt files surface as one clear error
        raise ManualParseError("This file could not be read. Try pasting the text instead.") from exc

    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 20:
        raise ManualParseError(
            "No readable text found. Scanned PDFs are not supported; paste the text instead."
        )
    return text[:MAX_TEXT_CHARS]


_COURSE_CODE = re.compile(r"\b([A-Z]{2,4})[\s-]?(\d{3,4})\b")
_LAB_NUMBER = re.compile(r"\b(?:Lab|Experiment|Practical)\s*(?:No\.?|#|Number)?\s*[:\-]?\s*(\d{1,2})\b", re.I)
_LABELLED = {
    "experiment_title": re.compile(r"^(?:Title|Experiment|Lab Title|Objective)\s*[:\-]\s*(.+)$", re.I | re.M),
    "course_title": re.compile(r"^(?:Course(?: Title| Name)?)\s*[:\-]\s*(.+)$", re.I | re.M),
    "department": re.compile(r"^(Department of [^\n]+)$", re.I | re.M),
}


def guess_fields(text: str) -> ManualFields:
    fields = ManualFields()
    head = text[:4000]

    if match := _COURSE_CODE.search(head):
        fields.course_code = f"{match.group(1)}-{match.group(2)}"
    if match := _LAB_NUMBER.search(head):
        fields.lab_number = f"Lab {int(match.group(1)):02d}"
    for name, pattern in _LABELLED.items():
        if match := pattern.search(head):
            value = match.group(1).strip()
            if name == "course_title" and fields.course_code:
                value = value.replace(fields.course_code, "").strip(" -—:")
            setattr(fields, name, value[:160])
    if not fields.department and (match := re.search(r"Department of [A-Z][\w &]+", head)):
        fields.department = match.group(0).strip()
    return fields


def parse_manual(filename: str, data: bytes) -> dict:
    text = extract_text(filename, data)
    return {"text": text, "fields": asdict(guess_fields(text))}
