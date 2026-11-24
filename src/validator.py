"""Schema validation, numerical grounding, safe plot execution, university resolve."""

from __future__ import annotations

import ast
import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.schema import LabReportSchema, validate_report

ROOT = Path(__file__).resolve().parents[1]
UNIVERSITIES_PATH = ROOT / "assets" / "universities.json"

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_BLOCKED_PLOT_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "input", "breakpoint",
    "os", "sys", "subprocess", "pathlib", "shutil", "socket", "requests",
}


@dataclass
class GroundingResult:
    total_numbers: int = 0
    grounded: int = 0
    missing: list[str] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if self.total_numbers == 0:
            return 1.0
        return self.grounded / self.total_numbers


@dataclass
class ValidationResult:
    report: LabReportSchema
    grounding: GroundingResult
    university: dict[str, Any]
    logo_path: Path
    plot_path: Path | None = None
    plot_error: str | None = None

    @property
    def ok(self) -> bool:
        return self.plot_error is None and self.grounding.accuracy >= 0.85


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


def _normalize_number(token: str) -> str:
    try:
        value = float(token)
    except ValueError:
        return token
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def extract_numbers(text: str) -> set[str]:
    return {_normalize_number(m.group(0)) for m in _NUMBER_RE.finditer(text)}


def check_numerical_grounding(report: LabReportSchema, raw_log: str) -> GroundingResult:
    """Require table numeric cells to appear in the raw log (normalized)."""
    raw_nums = extract_numbers(raw_log)
    result = GroundingResult()
    for table in report.report_body.tables:
        for row in table.rows:
            for cell in row:
                nums = extract_numbers(cell)
                if not nums:
                    continue
                for num in nums:
                    result.total_numbers += 1
                    if num in raw_nums:
                        result.grounded += 1
                    else:
                        # Allow simple derived % / ratios already present as substrings
                        if any(num in _normalize_number(x) or _normalize_number(x) in num for x in raw_nums):
                            result.grounded += 1
                        else:
                            result.missing.append(num)
    return result


_UNIT_FACTORS = (1000.0, 0.001, 1_000_000.0, 0.000001)


@dataclass
class CellTrace:
    """Where one table cell's number came from in the raw log."""

    status: str  # "text" | "grounded" | "normalised" | "derived" | "ungrounded"
    line: int | None = None  # 1-based raw-log line number

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "line": self.line}


def _decimals(token: str) -> int:
    return len(token.split(".", 1)[1]) if "." in token else 0


def _close(a: float, b: float, decimals: int) -> bool:
    tolerance = 0.5 * 10 ** (-decimals) + 1e-9
    return abs(a - b) <= max(tolerance, abs(b) * 1e-6)


def _line_numbers(raw_log: str) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for line_no, line in enumerate(raw_log.splitlines(), start=1):
        for num in extract_numbers(line):
            index.setdefault(num, []).append(line_no)
    return index


def _is_derived(value: float, decimals: int, siblings: list[float]) -> bool:
    for i, a in enumerate(siblings):
        for j, b in enumerate(siblings):
            if i == j:
                continue
            candidates = [a - b, a + b, a * b]
            if b != 0:
                candidates += [a / b, a / b * 100]
            if any(_close(c, value, decimals) for c in candidates):
                return True
    return False


def trace_tables(report: LabReportSchema, raw_log: str) -> list[list[list[dict[str, Any]]]]:
    """Trace every table cell back to a raw-log line.

    Returns tables -> rows -> cells. A cell is ``grounded`` when its number
    appears in the log, ``normalised`` when it is a log number rescaled by a
    unit factor (e.g. 1.85 s -> 1850 ms), ``derived`` when it is arithmetic over
    sibling cells in the same row, and ``ungrounded`` otherwise.
    """
    line_index = _line_numbers(raw_log)
    raw_values = [(float(n), lines) for n, lines in line_index.items()]
    traced: list[list[list[dict[str, Any]]]] = []

    for table in report.report_body.tables:
        table_trace: list[list[dict[str, Any]]] = []
        for row in table.rows:
            row_numbers = [extract_numbers(cell) for cell in row]
            # Prefer the log line that holds most of this row's numbers.
            votes: dict[int, int] = {}
            for nums in row_numbers:
                for num in nums:
                    for line_no in line_index.get(num, []):
                        votes[line_no] = votes.get(line_no, 0) + 1
            row_line = max(votes, key=votes.get) if votes else None

            siblings = [float(n) for nums in row_numbers for n in nums]
            row_trace: list[dict[str, Any]] = []
            for cell, nums in zip(row, row_numbers):
                match = _NUMBER_RE.search(cell)
                if not nums or match is None:
                    row_trace.append(CellTrace("text").as_dict())
                    continue
                token = match.group(0)
                num = _normalize_number(token)
                value = float(token)
                decimals = _decimals(token)

                if num in line_index:
                    lines = line_index[num]
                    line = row_line if row_line in lines else lines[0]
                    row_trace.append(CellTrace("grounded", line).as_dict())
                    continue

                normalised_line = None
                for raw_value, lines in raw_values:
                    if any(_close(raw_value * f, value, max(decimals, 1)) for f in _UNIT_FACTORS):
                        normalised_line = row_line if row_line in lines else lines[0]
                        break
                if normalised_line is not None:
                    row_trace.append(CellTrace("normalised", normalised_line).as_dict())
                elif _is_derived(value, decimals, [s for s in siblings if s != value]):
                    row_trace.append(CellTrace("derived", row_line).as_dict())
                else:
                    row_trace.append(CellTrace("ungrounded").as_dict())
            table_trace.append(row_trace)
        traced.append(table_trace)
    return traced


def summarize_trace(traced: list[list[list[dict[str, Any]]]]) -> dict[str, int]:
    counts = {"grounded": 0, "normalised": 0, "derived": 0, "ungrounded": 0}
    for table in traced:
        for row in table:
            for cell in row:
                if cell["status"] in counts:
                    counts[cell["status"]] += 1
    counts["total"] = sum(counts.values())
    return counts


def _assert_safe_plot_code(code: str) -> ast.Module:
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [node.module.split(".")[0]] if node.module else []
            for name in names:
                if name not in {"matplotlib", "pyplot", "plt", "numpy", "np"}:
                    raise ValueError(f"Disallowed import in plot_code: {name}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _BLOCKED_PLOT_NAMES:
                raise ValueError(f"Disallowed call in plot_code: {node.func.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("Disallowed dunder attribute in plot_code")
    return tree


def run_plot_code(plot_code: str, output_dir: Path) -> Path:
    """Execute matplotlib plot_code in a restricted namespace; return plot.png path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "plot.png"
    _assert_safe_plot_code(plot_code)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Drop imports (plt is injected) and rewrite savefig target
    lines = [
        ln for ln in plot_code.splitlines()
        if not ln.strip().startswith("import ") and not ln.strip().startswith("from ")
    ]
    safe_code = "\n".join(lines)
    safe_code = re.sub(
        r"savefig\(\s*['\"]plot\.png['\"]",
        f"savefig({str(plot_path)!r}",
        safe_code,
    )

    ns: dict[str, Any] = {
        "__builtins__": {
            "range": range, "len": len, "min": min, "max": max,
            "float": float, "int": int, "list": list, "dict": dict,
            "enumerate": enumerate, "zip": zip, "print": print,
        },
        "plt": plt,
    }
    exec(compile(safe_code, "<plot_code>", "exec"), ns, ns)  # noqa: S102 — gated by AST allowlist
    plt.close("all")

    if not plot_path.exists():
        # Fallback: if code saved elsewhere named plot.png in cwd
        cwd_plot = Path("plot.png")
        if cwd_plot.exists():
            cwd_plot.replace(plot_path)
        else:
            raise FileNotFoundError("plot_code did not produce plot.png")
    return plot_path


def validate_and_prepare(
    payload: dict | str | LabReportSchema,
    raw_log: str,
    work_dir: Path | None = None,
    run_plot: bool = True,
) -> ValidationResult:
    report = payload if isinstance(payload, LabReportSchema) else validate_report(payload)
    university = resolve_university(report.cover_page.university_id)
    grounding = check_numerical_grounding(report, raw_log)

    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="labpulse_"))
    work.mkdir(parents=True, exist_ok=True)

    plot_path = None
    plot_error = None
    if run_plot:
        try:
            plot_path = run_plot_code(report.report_body.plot_code, work)
        except Exception as exc:  # noqa: BLE001 — surface to caller
            plot_error = str(exc)

    return ValidationResult(
        report=report,
        grounding=grounding,
        university=university,
        logo_path=Path(university["logo_abs"]),
        plot_path=plot_path,
        plot_error=plot_error,
    )


def report_to_resolved_dict(result: ValidationResult) -> dict[str, Any]:
    data = result.report.model_dump(mode="json")
    data["university_full_name"] = result.university["full_name"]
    data["university_logo_path"] = str(result.logo_path)
    data["plot_path"] = str(result.plot_path) if result.plot_path else ""
    data["grounding_accuracy"] = round(result.grounding.accuracy, 4)
    return data
