"""Built-in sample labs for the \"Try a sample\" row (task / code / output)."""

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
    return list(load_presets())
