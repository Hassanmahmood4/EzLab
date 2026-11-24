"""llama.cpp loader for the fine-tuned LabPulse GGUF, plus prompt building and telemetry.

Only the fine-tuned model is ever loaded by the app. Set ``LABPULSE_STUB=1`` to run
the UI without a model (development only): generation then replays the ground-truth
answer of a matching preset.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import psutil

from src.schema import SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT / "models" / "labpulse-1.5b-q4_k_m.gguf"
MODEL_PATH = Path(os.environ.get("LABPULSE_MODEL", DEFAULT_MODEL_PATH))
STUB_MODE = os.environ.get("LABPULSE_STUB") == "1"

N_CTX = 4096
MAX_NEW_TOKENS = 2048
TEMPERATURE = 0.1


class GenerationCancelled(Exception):
    pass


class ModelUnavailable(RuntimeError):
    pass


@dataclass
class StudentProfile:
    name: str
    registration_no: str
    section: str
    university: str
    instructor: str
    date: str


@dataclass
class LabDetails:
    course_code: str
    course_title: str
    lab_number: str
    experiment_title: str
    department: str


@dataclass
class GenerationStats:
    tokens: int = 0
    seconds: float = 0.0
    peak_rss_gb: float = 0.0

    @property
    def tokens_per_second(self) -> float:
        return self.tokens / self.seconds if self.seconds > 0 else 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "tokens": self.tokens,
            "seconds": round(self.seconds, 2),
            "tokens_per_second": round(self.tokens_per_second, 1),
            "peak_rss_gb": round(self.peak_rss_gb, 2),
        }


@dataclass
class GenerationResult:
    text: str
    stats: GenerationStats = field(default_factory=GenerationStats)


MAX_MANUAL_CHARS = 8_000


def build_user_prompt(
    profile: StudentProfile,
    lab: LabDetails,
    raw_log: str = "",
    manual_text: str = "",
) -> str:
    """Prompt the model with cover-page details, the lab manual, and an optional log."""
    lab_number = lab.lab_number.strip()
    if lab_number and not lab_number.lower().startswith("lab"):
        lab_number = f"Lab {lab_number.zfill(2)}"
    manual = (manual_text or "").strip()
    if len(manual) > MAX_MANUAL_CHARS:
        manual = manual[:MAX_MANUAL_CHARS] + "\n[manual truncated]"
    header = (
        "STUDENT PROFILE:\n"
        f"Name: {profile.name}\n"
        f"Registration No: {profile.registration_no}\n"
        f"Section: {profile.section}\n"
        f"University: {profile.university}\n"
        f"Instructor: {profile.instructor}\n"
        f"Date: {profile.date}\n\n"
        "LAB MANUAL:\n"
        f"Course: {lab.course_code} — {lab.course_title}\n"
        f"{lab_number}: {lab.experiment_title}\n"
        f"Department: {lab.department}\n"
    )
    if manual:
        header += f"\n{manual}\n"
    log = (raw_log or "").strip()
    if log:
        return (
            header
            + "Write a grounded lab report from the raw experimental log. "
            "Audit unit mismatches/outliers. Output JSON only.\n\n"
            f"RAW DATA LOG:\n{log}"
        )
    return (
        header
        + "Write a complete lab report for this experiment. "
        "Include typical, internally consistent tables, a plot, equations, "
        "methodology, discussion and conclusion. Output JSON only."
    )


def extract_json(text: str) -> str:
    """Return the outermost JSON object in model output (tolerates code fences)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("Model output contained no JSON object")
    return cleaned[start : end + 1]


def _rss_gb() -> float:
    return psutil.Process().memory_info().rss / 1024**3


class LabPulseModel:
    """Lazily loaded, process-wide llama.cpp model. One generation at a time."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.model_path = model_path
        self._llm: Any = None
        self._load_lock = threading.Lock()
        self._generate_lock = threading.Lock()

    @property
    def available(self) -> bool:
        return STUB_MODE or self.model_path.exists()

    @property
    def loaded(self) -> bool:
        return self._llm is not None

    @property
    def busy(self) -> bool:
        return self._generate_lock.locked()

    def _load(self) -> Any:
        with self._load_lock:
            if self._llm is not None:
                return self._llm
            if not self.model_path.exists():
                raise ModelUnavailable(f"Model file not found: {self.model_path}")
            try:
                from llama_cpp import Llama
            except ImportError as exc:
                raise ModelUnavailable(
                    "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
                ) from exc
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=N_CTX,
                n_threads=max(2, (os.cpu_count() or 4) // 2),
                n_gpu_layers=-1,
                logits_all=False,
                embedding=False,
                verbose=False,
            )
            return self._llm

    def generate(
        self,
        user_prompt: str,
        on_token: Callable[[int], None] | None = None,
        cancel: threading.Event | None = None,
    ) -> GenerationResult:
        if STUB_MODE:
            return _stub_generate(user_prompt, on_token, cancel)
        if not self._generate_lock.acquire(blocking=False):
            raise RuntimeError("Another report is already being generated")
        try:
            llm = self._load()
            stats = GenerationStats(peak_rss_gb=_rss_gb())
            started = time.perf_counter()
            parts: list[str] = []
            stream = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_NEW_TOKENS,
                stream=True,
            )
            for chunk in stream:
                if cancel is not None and cancel.is_set():
                    raise GenerationCancelled()
                delta = chunk["choices"][0].get("delta", {}).get("content")
                if not delta:
                    continue
                parts.append(delta)
                stats.tokens += 1
                if stats.tokens % 32 == 0:
                    stats.peak_rss_gb = max(stats.peak_rss_gb, _rss_gb())
                if on_token is not None:
                    on_token(stats.tokens)
            stats.seconds = time.perf_counter() - started
            stats.peak_rss_gb = max(stats.peak_rss_gb, _rss_gb())
            return GenerationResult(text="".join(parts), stats=stats)
        finally:
            self._generate_lock.release()


def _stub_generate(
    user_prompt: str,
    on_token: Callable[[int], None] | None,
    cancel: threading.Event | None,
) -> GenerationResult:
    from src.presets import find_preset_answer

    answer = find_preset_answer(user_prompt)
    if answer is None:
        answer = _synthetic_stub_report(user_prompt)
    text = json.dumps(answer, ensure_ascii=False)
    stats = GenerationStats(peak_rss_gb=_rss_gb())
    started = time.perf_counter()
    total = max(1, len(text) // 4)
    for token in range(1, total + 1, 24):
        if cancel is not None and cancel.is_set():
            raise GenerationCancelled()
        time.sleep(0.03)
        if on_token is not None:
            on_token(token)
    stats.tokens = total
    stats.seconds = time.perf_counter() - started
    return GenerationResult(text=text, stats=stats)


def _synthetic_stub_report(user_prompt: str) -> dict[str, Any]:
    """A schema-valid report so stub mode still returns a lab without a matching sample."""
    def field(label: str, fallback: str) -> str:
        match = re.search(rf"{label}:\s*(.+)", user_prompt)
        return match.group(1).strip() if match else fallback

    course_line = re.search(r"Course:\s*(.+?)\s+—\s+(.+)", user_prompt)
    lab_line = re.search(r"(Lab\s+\S+):\s*(.+)", user_prompt)
    course_code = course_line.group(1).strip() if course_line else "CS-000"
    course_title = course_line.group(2).strip() if course_line else "Computer Science Lab"
    lab_number = lab_line.group(1).strip() if lab_line else "Lab 01"
    experiment = lab_line.group(2).strip() if lab_line else "Laboratory Exercise"
    name = field("Name", "Student")
    title = experiment
    return {
        "cover_page": {
            "university_id": "fast_nuces",
            "university_raw": field("University", "FAST-NUCES"),
            "department": field("Department", "Department of Computer Science"),
            "course_code": course_code,
            "course_title": course_title,
            "lab_number": lab_number,
            "experiment_title": title,
            "student_name": name,
            "registration_no": field("Registration No", "00L-0000"),
            "section": field("Section", "A"),
            "instructor": field("Instructor", "Lab Instructor"),
            "submission_date": field("Date", "2026-01-01"),
        },
        "anomaly_check": {"status": "ok", "flags": []},
        "report_body": {
            "abstract": (
                f"This lab investigated {title}. The procedure in the lab manual was followed, "
                "and measurements were recorded for four configurations of the exercise. "
                "Results matched the expected trend for this experiment."
            ),
            "apparatus": ["Lab workstation", "Course toolchain", "Lab manual"],
            "methodology": (
                f"The steps listed in the {lab_number} manual for {title} were carried out in order. "
                "Each configuration was run three times and the mean of the recorded metric was kept."
            ),
            "equations_latex": [r"T_{\mathrm{avg}}=\frac{1}{k}\sum_{i=1}^{k} t_i"],
            "tables": [
                {
                    "caption": f"{title} — measured results",
                    "headers": ["Trial", "Input", "Time (ms)", "Pass"],
                    "rows": [
                        ["1", "10", "1.20", "Yes"],
                        ["2", "100", "8.40", "Yes"],
                        ["3", "1000", "61.00", "Yes"],
                        ["4", "10000", "490.00", "Yes"],
                    ],
                }
            ],
            "plot_code": (
                "import matplotlib.pyplot as plt\n"
                "x = [10, 100, 1000, 10000]\n"
                "y = [1.20, 8.40, 61.00, 490.00]\n"
                "plt.figure(figsize=(6, 4))\n"
                "plt.plot(x, y, 'o-')\n"
                "plt.xscale('log')\n"
                "plt.xlabel('Input')\n"
                "plt.ylabel('Time (ms)')\n"
                f"plt.title({title!r})\n"
                "plt.grid(True, which='both', ls=':')\n"
                "plt.tight_layout()\n"
                "plt.savefig('plot.png', dpi=300)"
            ),
            "discussion": (
                f"Observed times for {title} increased with input size, as expected from the lab manual. "
                "No unit mismatches were present because these figures were written for this report."
            ),
            "conclusion": (
                f"The experiment for {title} was completed as specified in the lab manual, "
                "and the tabulated results support the intended learning outcome."
            ),
        },
    }


MODEL = LabPulseModel()
