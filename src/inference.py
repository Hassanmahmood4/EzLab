"""llama.cpp loader for the fine-tuned EzLab GGUF, plus telemetry.

Only the fine-tuned model is loaded by the app. Set ``LABPULSE_STUB=1`` to run
without a GGUF (dev only): generation returns a minimal schema-valid stub.
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


def extract_json(text: str) -> str:
    """Return the first complete JSON object in model output (tolerates fences + trailing junk)."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("Model output contained no JSON object")
    try:
        obj, _end = json.JSONDecoder().raw_decode(cleaned[start:])
    except json.JSONDecodeError as exc:
        # Fallback: outermost braces (may still fail validation later)
        end = cleaned.rfind("}")
        if end <= start:
            raise ValueError("Model output contained no JSON object") from exc
        try:
            obj = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc2:
            raise ValueError(f"Model output was not valid JSON: {exc2}") from exc2
    return json.dumps(obj, ensure_ascii=False)


def _rss_gb() -> float:
    return psutil.Process().memory_info().rss / 1024**3


class EzLabModel:
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

    def _make_llama(self, Llama: Any, *, n_gpu_layers: int) -> Any:
        return Llama(
            model_path=str(self.model_path),
            n_ctx=N_CTX,
            n_threads=max(2, (os.cpu_count() or 4) // 2),
            n_gpu_layers=n_gpu_layers,
            logits_all=False,
            embedding=False,
            verbose=False,
        )

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

            # Prefer Metal/CUDA when available; fall back to CPU if context init fails
            # (common when Metal reports a null device under restricted hosts).
            preferred = int(os.environ.get("LABPULSE_N_GPU_LAYERS", "-1"))
            try:
                self._llm = self._make_llama(Llama, n_gpu_layers=preferred)
            except Exception as first_exc:
                if preferred == 0 and os.environ.get("GGML_METAL") == "0":
                    raise ModelUnavailable(
                        f"Failed to load GGUF model: {first_exc}"
                    ) from first_exc
                os.environ["GGML_METAL"] = "0"
                try:
                    self._llm = self._make_llama(Llama, n_gpu_layers=0)
                except Exception as cpu_exc:
                    raise ModelUnavailable(
                        f"Failed to load GGUF model (GPU and CPU): {cpu_exc}"
                    ) from cpu_exc
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
            "semester": "",
        },
        "tasks": [
            {
                "number": 1,
                "title": title,
                "prompt": "Complete the exercise described in the lab manual.",
                "code": "print('hello lab')\n",
                "output": "hello lab\n",
            }
        ],
    }


MODEL = EzLabModel()
