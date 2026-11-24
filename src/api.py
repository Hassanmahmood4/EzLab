"""Local FastAPI backend for the LabPulse web UI (http://127.0.0.1:8080).

Run: uvicorn src.api:app --host 127.0.0.1 --port 8080
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import threading
from datetime import date
from pathlib import Path
from typing import Any, Literal

import psutil
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from src import storage
from src.inference import MODEL, MODEL_PATH, STUB_MODE, GenerationCancelled, LabDetails, ModelUnavailable, StudentProfile
from src.manual_parser import ManualParseError, parse_manual
from src.pipeline import PipelineError, apply_edits, generate
from src.presets import public_presets
from src.renderer_pdf import find_typst
from src.validator import ROOT, load_universities

app = FastAPI(title="LabPulse", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "LABPULSE_WEB_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProfileIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    registration_no: str = Field(..., min_length=1, max_length=40)
    section: str = Field("", max_length=40)
    university_id: str = Field(..., min_length=2)
    university_label: str = Field("", max_length=120)
    instructor: str = Field("", max_length=120)
    department: str = Field("", max_length=160)


class LabIn(BaseModel):
    course_code: str = Field(..., min_length=1, max_length=20)
    course_title: str = Field(..., min_length=1, max_length=160)
    lab_number: str = Field(..., min_length=1, max_length=20)
    experiment_title: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=160)


class GenerateIn(BaseModel):
    profile: ProfileIn
    lab: LabIn
    raw_log: str = ""
    raw_log_name: str | None = Field(default=None, max_length=200)
    manual_text: str | None = Field(default=None, max_length=20_000)
    submission_date: str = Field(default_factory=lambda: date.today().isoformat())


class EditIn(BaseModel):
    cover: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)


def _university_label(university_id: str, label: str) -> str:
    if label.strip():
        return label.strip()
    registry = load_universities()
    return registry.get(university_id, {}).get("full_name", university_id)


def _typst_available() -> bool:
    try:
        find_typst()
        return True
    except FileNotFoundError:
        return False


def _llama_installed() -> bool:
    try:
        import llama_cpp  # noqa: F401
    except ImportError:
        return False
    return True


@app.get("/health")
def health() -> dict[str, Any]:
    process = psutil.Process()
    return {
        "status": "ok",
        "local": True,
        "platform": platform.system(),
        "model": {
            "file": MODEL_PATH.name,
            "path": str(MODEL_PATH.relative_to(ROOT)) if MODEL_PATH.is_relative_to(ROOT) else str(MODEL_PATH),
            "found": MODEL_PATH.exists(),
            "loaded": MODEL.loaded,
            "busy": MODEL.busy,
            "stub": STUB_MODE,
            "runtime_installed": _llama_installed(),
        },
        "typst": {"found": _typst_available()},
        "memory": {"rss_gb": round(process.memory_info().rss / 1024**3, 2)},
    }


@app.get("/universities")
def universities() -> list[dict[str, str]]:
    registry = load_universities()
    return [
        {"id": uid, "full_name": meta["full_name"], "logo_url": f"/universities/{uid}/logo"}
        for uid, meta in sorted(registry.items(), key=lambda kv: kv[1]["full_name"])
    ]


@app.get("/universities/{university_id}/logo")
def university_logo(university_id: str) -> FileResponse:
    meta = load_universities().get(university_id)
    if meta is None:
        raise HTTPException(404, "Unknown university")
    path = ROOT / meta["logo_path"]
    if not path.exists():
        raise HTTPException(404, "Logo missing")
    return FileResponse(path, media_type="image/png")


@app.get("/profile")
def get_profile() -> dict[str, Any] | None:
    return storage.load_profile()


@app.put("/profile")
def put_profile(profile: ProfileIn) -> dict[str, Any]:
    if profile.university_id not in load_universities():
        raise HTTPException(422, "Unknown university")
    return storage.save_profile(profile.model_dump())


@app.get("/presets")
def presets() -> list[dict[str, Any]]:
    return public_presets()


@app.post("/manual/parse")
async def manual_parse(file: UploadFile = File(...)) -> dict[str, Any]:
    data = await file.read()
    try:
        return parse_manual(file.filename or "manual.txt", data)
    except ManualParseError as exc:
        raise HTTPException(422, str(exc)) from exc


def _sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/generate")
async def generate_report(body: GenerateIn, request: Request) -> StreamingResponse:
    if MODEL.busy:
        raise HTTPException(409, "A report is already being generated.")

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
    cancel = threading.Event()

    def emit(event: str, payload: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, (event, payload))

    profile = StudentProfile(
        name=body.profile.name,
        registration_no=body.profile.registration_no,
        section=body.profile.section,
        university=_university_label(body.profile.university_id, body.profile.university_label),
        instructor=body.profile.instructor,
        date=body.submission_date,
    )
    lab = LabDetails(**body.lab.model_dump())

    def worker() -> None:
        try:
            record = generate(
                profile, lab, body.raw_log, body.profile.university_id, emit, cancel,
                raw_log_name=body.raw_log_name,
                manual_text=body.manual_text,
            )
            emit("done", {"record": record})
        except GenerationCancelled:
            emit("cancelled", {})
        except PipelineError as exc:
            emit("error", {"code": exc.code, "message": exc.message})
        except ModelUnavailable as exc:
            emit("error", {"code": "model_missing", "message": str(exc)})
        except Exception as exc:  # noqa: BLE001 — never leave the stream hanging
            emit("error", {"code": "internal", "message": str(exc)[:500]})

    threading.Thread(target=worker, daemon=True).start()

    async def stream():
        while True:
            if await request.is_disconnected():
                cancel.set()
                return
            try:
                event, payload = await asyncio.wait_for(queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            yield _sse(event, payload)
            if event in {"done", "error", "cancelled"}:
                return

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/reports")
def reports() -> list[dict[str, Any]]:
    return storage.list_records()


def _record_or_404(report_id: str) -> dict[str, Any]:
    try:
        return storage.load_record(report_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(404, "Report not found") from exc


@app.get("/reports/{report_id}")
def report(report_id: str) -> dict[str, Any]:
    return _record_or_404(report_id)


@app.post("/reports/{report_id}/edit")
def edit_report(report_id: str, body: EditIn) -> dict[str, Any]:
    _record_or_404(report_id)
    try:
        return apply_edits(report_id, body.cover, body.body)
    except PipelineError as exc:
        raise HTTPException(422, {"code": exc.code, "message": exc.message}) from exc


@app.delete("/reports/{report_id}")
def delete_report(report_id: str) -> dict[str, str]:
    _record_or_404(report_id)
    storage.delete_record(report_id)
    return {"deleted": report_id}


_MEDIA = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "plot": "image/png",
}


@app.get("/reports/{report_id}/files/{kind}")
def report_file(report_id: str, kind: Literal["pdf", "docx", "plot"], download: bool = False) -> FileResponse:
    record = _record_or_404(report_id)
    folder = storage.report_dir(report_id)
    path: Path = folder / "work" / "plot.png" if kind == "plot" else folder / f"{report_id}.{kind}"
    if not path.exists():
        raise HTTPException(404, f"No {kind} file for this report")
    cover = record["report"]["cover_page"]
    filename = f"{cover['course_code']}_{cover['lab_number']}_{cover['registration_no']}.{'png' if kind == 'plot' else kind}"
    filename = "".join(c if c.isalnum() or c in "-_." else "_" for c in filename)
    return FileResponse(
        path,
        media_type=_MEDIA[kind],
        filename=filename if download else None,
        content_disposition_type="attachment" if download else "inline",
        headers={"Cache-Control": "no-store"},
    )
