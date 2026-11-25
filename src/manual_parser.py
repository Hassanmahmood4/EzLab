"""Extract text, lab fields, and Task 1..N sections from an uploaded lab manual."""

from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass
from pathlib import Path


SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}
MAX_MANUAL_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 80_000

# Explicit headings: "Task 1 — …", "Exercise 2:", "Question 3)"
_TASK_HEAD = re.compile(
    r"(?im)^(?:#{1,3}\s*)?(?:task|exercise|question|problem)\s*(\d{1,2})\s*[—\-.:)]*\s*(.*)$"
)

# Walkthrough parts in many ML manuals (instructional, not the graded exercises)
_PART_HEAD = re.compile(
    r"(?im)^(?:#{1,3}\s*)?part\s*([A-G]|[0-9]{1,2})"
    r"(?:\s*\(([^)]*)\))?"
    r"(?:\s*[—\-.:)]+\s*(.*))?$"
)

# Graded work section
_EXERCISES_SECTION = re.compile(
    r"(?im)^(?:#{1,3}\s*)?(?:\d{1,2}\.?\s*)?(?:exercises?\s*/\s*tasks?|exercises?|lab\s+tasks?|"
    r"tasks?\s*(?:section)?|problems?(?:\s*/\s*exercises?)?)\b[^\n]{0,40}$"
)

_SECTION_END = re.compile(
    r"(?im)^(?:#{1,3}\s*)?(?:\d{1,2}\.?\s*)?(?:"
    r"submission|deliverables?|appendix|references?|bibliography|"
    r"grading|marks?|rubric|notes?|further\s+reading|acknowledg|"
    r"python\s+implementation|full\s+script|complete\s+code"
    r")\b"
)

_NUMBERED_ITEM = re.compile(r"(?m)^\s*(\d{1,2})[.)]\s+(\S.*)$")

_NUMBERED_INLINE = re.compile(
    r"(?<!\d)(\d{1,2})\.\s+([A-Z][^\n]{0,80}?(?::|—|-)\s|[A-Z][a-z]+(?:\s+[a-z]+){0,5}:\s)"
)

# Manual front-matter / theory headings — never treat as lab tasks
_SKIP_TITLES = re.compile(
    r"(?i)^("
    r"aim|objective|objectives|learning\s+objectives?|theory|introduction|"
    r"background|apparatus|equipment|pre[- ]?lab|procedure|methodology|"
    r"discussion|conclusion|references?|appendix|submission|deliverables?|"
    r"grading|marks?|rubric|note|notes|overview|outline|agenda|"
    r"python\s+implementation|required\s+software|dataset|materials"
    r")\b"
)

_PROMPT_CUT = re.compile(
    r"(?is)\n?\s*(?:\d{1,2}\.\s*)?(?:"
    r"python\s+implementation|record\s+your\s+values|full\s+script|"
    r"type\s+and\s+run\s+the\s+script|the\s+function\s+report\s*\("
    r").*"
)


class ManualParseError(ValueError):
    pass


@dataclass
class ManualFields:
    course_code: str = ""
    course_title: str = ""
    lab_number: str = ""
    experiment_title: str = ""
    department: str = ""


@dataclass
class ParsedTask:
    number: int
    title: str
    prompt: str
    code: str = ""
    output: str = ""


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:40])


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
    except Exception as exc:  # noqa: BLE001
        raise ManualParseError("This file could not be read. Try pasting the text instead.") from exc

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 20:
        raise ManualParseError(
            "No readable text found. Scanned PDFs are not supported; paste the text instead."
        )
    return text[:MAX_TEXT_CHARS]


_COURSE_CODE = re.compile(r"\b([A-Z]{2,4})[\s-]?(\d{3,4})\b")
_LAB_NUMBER = re.compile(
    r"\b(?:Lab|Experiment|Practical)\s*(?:No\.?|#|Number)?\s*[:\-]?\s*(\d{1,2})\b", re.I
)
_LABELLED = {
    "experiment_title": re.compile(
        r"^(?:Title|Experiment|Lab Title|Objective)\s*[:\-]\s*(.+)$", re.I | re.M
    ),
    "course_title": re.compile(r"^(?:Course(?: Title| Name)?)\s*[:\-]\s*(.+)$", re.I | re.M),
    "department": re.compile(r"^(Department of [^\n]+)$", re.I | re.M),
}
_AIM = re.compile(
    r"(?im)^(?:#{1,3}\s*)?(?:\d{1,2}\.?\s*)?aim\s*\n+(.+?)(?=\n\s*(?:\d{1,2}\.?\s*)?[A-Z]|\n{2,}|\Z)"
)
_DOC_TITLE = re.compile(
    r"(?im)^(?:lab\s*\d{1,2}\s*[:\-—]?\s*)?(implementation of .+|[\w].{10,120})$"
)


def guess_fields(text: str) -> ManualFields:
    fields = ManualFields()
    head = text[:6000]

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

    if not fields.experiment_title:
        # First non-trivial line after "Lab NN" often is the real title
        lines = [ln.strip() for ln in head.splitlines() if ln.strip()]
        for i, ln in enumerate(lines[:12]):
            if re.match(r"(?i)^lab\s*\d+", ln) and i + 1 < len(lines):
                nxt = re.sub(r"\s+", " ", lines[i + 1]).strip()
                if 8 <= len(nxt) <= 160 and not _SKIP_TITLES.match(nxt):
                    fields.experiment_title = nxt
                    break
        if not fields.experiment_title and (aim := _AIM.search(head)):
            sentence = re.sub(r"\s+", " ", aim.group(1)).strip()
            # Shorten Aim paragraph to a title-ish phrase
            if sentence.lower().startswith("to "):
                sentence = sentence[3:]
            sentence = sentence.split(".")[0].strip()
            if len(sentence) > 12:
                fields.experiment_title = (sentence[:1].upper() + sentence[1:])[:160]
    return fields


def clean_task_title(title: str, number: int = 1) -> str:
    """Strip PDF table-of-contents dots and trailing page numbers."""
    t = (title or "").strip()
    t = re.sub(r"[\.…]{2,}\s*\d*\s*$", "", t)
    t = re.sub(r"\s*\.{3,}\s*", " ", t)
    t = re.sub(r"\s+\d{1,3}\s*$", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" —-.:")
    if len(t) > 90:
        t = t[:87].rstrip() + "…"
    return t or f"Task {number}"


def _clean_prompt(raw: str) -> str:
    text = (raw or "").strip()
    text = _PROMPT_CUT.sub("", text).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Drop accidental paste of huge import blocks
    if "import numpy" in text and len(text) > 800:
        text = text.split("import numpy")[0].strip()
    return text[:2500]


def _split_title_prompt(raw: str, number: int) -> tuple[str, str]:
    text = re.sub(r"\s+", " ", (raw or "").strip())
    if not text:
        return f"Task {number}", ""

    for sep in (":", "—", "–"):
        if sep in text:
            left, right = text.split(sep, 1)
            left, right = left.strip(), right.strip()
            if 1 <= len(left) <= 70 and not left.endswith((".", "?", "!")):
                return clean_task_title(left, number)[:160], _clean_prompt(right or text)
            break

    first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    title = (first[:77] + "…") if len(first) > 80 else first
    return clean_task_title(title or f"Task {number}", number)[:160], _clean_prompt(text)


def _is_skip_title(title: str) -> bool:
    return bool(_SKIP_TITLES.match((title or "").strip()))


def _part_number(token: str) -> int:
    token = (token or "").strip().upper()
    if token.isdigit():
        return int(token)
    if len(token) == 1 and "A" <= token <= "G":
        return ord(token) - ord("A") + 1
    return 0


def _tasks_from_heads(text: str) -> list[ParsedTask]:
    lines = text.splitlines()
    starts: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        match = _TASK_HEAD.match(line.strip())
        if not match:
            continue
        number = int(match.group(1))
        title = clean_task_title((match.group(2) or "").strip(" —-.:"), number)
        if _is_skip_title(title):
            continue
        starts.append((i, number, title))

    if not starts:
        return []

    tasks: list[ParsedTask] = []
    for idx, (line_i, number, title) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        prompt = _clean_prompt("\n".join(lines[line_i + 1 : end]))
        if not title:
            title, prompt = _split_title_prompt(prompt or f"Task {number}", number)
        elif not prompt:
            prompt = title
        if _is_skip_title(title):
            continue
        tasks.append(
            ParsedTask(number=number, title=clean_task_title(title, number)[:160], prompt=prompt)
        )
    return tasks


def _tasks_from_parts(text: str) -> list[ParsedTask]:
    lines = text.splitlines()
    starts: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        match = _PART_HEAD.match(line.strip())
        if not match:
            continue
        token = match.group(1) or ""
        number = _part_number(token)
        if not number:
            continue
        subtitle = (match.group(2) or "").strip()
        inline_prompt = (match.group(3) or "").strip()
        title = f"Part {token.upper()}" + (f" ({subtitle})" if subtitle else "")
        starts.append((i, number, title[:160], inline_prompt))

    if len(starts) < 2:
        return []

    tasks: list[ParsedTask] = []
    for idx, (line_i, number, title, inline_prompt) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        block_lines = lines[line_i + 1 : end]
        prompt = _clean_prompt("\n".join(block_lines)) or _clean_prompt(inline_prompt)
        tasks.append(ParsedTask(number=number, title=title, prompt=prompt or title))
    return _dedupe_sequential(tasks)


def _exercises_body(text: str) -> str | None:
    match = _EXERCISES_SECTION.search(text)
    if not match:
        return None
    rest = text[match.end() :]
    end = _SECTION_END.search(rest)
    major = re.search(
        r"(?m)^(?:#{1,3}\s*)?(1[0-9]|[2-9]\d)\.\s+[A-Z][A-Za-z /&\-]{2,60}$",
        rest,
    )
    ends = [m.start() for m in (end, major) if m]
    if ends:
        rest = rest[: min(ends)]
    return rest.strip() or None


def _tasks_from_numbered_list(block: str) -> list[ParsedTask]:
    if not block or len(block.strip()) < 10:
        return []

    line_starts: list[tuple[int, int, str]] = []
    lines = block.splitlines()
    for i, line in enumerate(lines):
        match = _NUMBERED_ITEM.match(line)
        if not match:
            continue
        number = int(match.group(1))
        body = match.group(2).strip()
        title_guess = body.split(":", 1)[0].strip()
        if number >= 10 and not line_starts:
            continue
        if _is_skip_title(title_guess) or _is_skip_title(body):
            continue
        # Skip outline rows that are only "Part A: …" when we are inside Exercises
        # (those belong to the walkthrough). Still allow "By hand:" style.
        if re.match(r"(?i)^part\s*[A-G0-9]", body) and "exercise" not in body.lower():
            continue
        line_starts.append((i, number, body))

    if len(line_starts) >= 2:
        nums = [s[1] for s in line_starts]
        # Require a mostly contiguous run starting near 1
        if nums[0] <= 2:
            tasks: list[ParsedTask] = []
            for idx, (line_i, number, first) in enumerate(line_starts):
                end = line_starts[idx + 1][0] if idx + 1 < len(line_starts) else len(lines)
                body = "\n".join([first, *lines[line_i + 1 : end]]).strip()
                title, prompt = _split_title_prompt(body, number)
                if _is_skip_title(title):
                    continue
                tasks.append(ParsedTask(number=number, title=title, prompt=prompt or body[:2500]))
            out = _dedupe_sequential(tasks)
            if len(out) >= 2:
                return out

    compact = re.sub(r"[ \t]+", " ", block)
    compact = re.sub(r"\n{2,}", "\n", compact)
    matches = list(_NUMBERED_INLINE.finditer(compact))
    if len(matches) < 2:
        matches = list(re.finditer(r"(?<!\d)(\d{1,2})\.\s+", compact))
        if len(matches) < 2:
            return []
        tasks = []
        for idx, match in enumerate(matches):
            number = int(match.group(1))
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(compact)
            body = compact[start:end].strip()
            title, prompt = _split_title_prompt(body, number)
            if _is_skip_title(title) or re.match(r"(?i)^part\s*[A-G]", title):
                continue
            tasks.append(ParsedTask(number=number, title=title, prompt=prompt or body[:2500]))
        return _dedupe_sequential(tasks)

    tasks = []
    for idx, match in enumerate(matches):
        number = int(match.group(1))
        start = match.start(2)
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(compact)
        body = compact[start:end].strip()
        title, prompt = _split_title_prompt(body, number)
        if _is_skip_title(title) or re.match(r"(?i)^part\s*[A-G]", title):
            continue
        tasks.append(ParsedTask(number=number, title=title, prompt=prompt or body[:2500]))
    return _dedupe_sequential(tasks)


def _dedupe_sequential(tasks: list[ParsedTask]) -> list[ParsedTask]:
    if not tasks:
        return []
    tasks = sorted(tasks, key=lambda t: (t.number, -len(t.prompt)))
    seen: set[int] = set()
    unique: list[ParsedTask] = []
    for task in tasks:
        if task.number in seen:
            continue
        seen.add(task.number)
        unique.append(task)

    if any(t.number == 1 for t in unique):
        expect = 1
        run: list[ParsedTask] = []
        for task in unique:
            if task.number == expect:
                run.append(task)
                expect += 1
            elif task.number > expect:
                break
        return run or unique
    return unique


def _looks_like_graded_exercises(tasks: list[ParsedTask]) -> bool:
    """Heuristic: titles such as By hand / Learning curve, not Aim / Part A."""
    if len(tasks) < 2:
        return False
    markers = 0
    for task in tasks:
        title = task.title.lower()
        if re.match(r"(?i)^part\s+", title) or _is_skip_title(title):
            continue
        if re.search(
            r"(?i)\b(by hand|learning curve|error metric|standardis|regularis|"
            r"heteroscedastic|interaction|split variation|single feature)\b",
            f"{title} {task.prompt}",
        ):
            markers += 1
    return markers >= 2 or (
        len(tasks) >= 3 and not any(re.match(r"(?i)^part\s+", t.title) for t in tasks)
    )


def extract_tasks(text: str) -> list[ParsedTask]:
    """Split manual text into graded tasks (prefer Exercises over Part walkthrough)."""
    headed = _tasks_from_heads(text)
    if len(headed) >= 2:
        return sorted(headed, key=lambda t: (t.number, t.title))

    body = _exercises_body(text)
    if body:
        numbered = _tasks_from_numbered_list(body)
        if numbered:
            return numbered

    # Some PDFs lose the '13. Exercises' heading but keep '1. By hand:' items
    numbered = _tasks_from_numbered_list(text)
    if _looks_like_graded_exercises(numbered):
        non_part = [t for t in numbered if not re.match(r"(?i)^part\s+", t.title)]
        return non_part or numbered

    parts = _tasks_from_parts(text)
    if len(parts) >= 2:
        return parts

    if headed:
        return headed
    return []


def parse_manual(filename: str, data: bytes) -> dict:
    text = extract_text(filename, data)
    tasks = [asdict(t) for t in extract_tasks(text)]
    return {"text": text, "fields": asdict(guess_fields(text)), "tasks": tasks}
