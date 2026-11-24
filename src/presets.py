"""Built-in sample labs (from the held-out test set) for the "Try a sample" row."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRESETS_PATH = ROOT / "assets" / "presets.json"


@lru_cache(maxsize=1)
def load_presets() -> list[dict[str, Any]]:
    if not PRESETS_PATH.exists():
        return []
    return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))


def public_presets() -> list[dict[str, Any]]:
    """Presets without their ground-truth answers."""
    return [{k: v for k, v in p.items() if k != "answer"} for p in load_presets()]


def find_preset_answer(user_prompt: str) -> dict[str, Any] | None:
    """Stub-mode lookup: match a prompt to a sample by log or experiment title."""
    for preset in load_presets():
        if preset["raw_log"].strip() and preset["raw_log"].strip() in user_prompt:
            return preset["answer"]
        title = preset.get("lab", {}).get("experiment_title", "")
        if title and title in user_prompt:
            return preset["answer"]
    return None
