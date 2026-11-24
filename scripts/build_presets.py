"""Extract the three demo presets from data/test.jsonl into assets/presets.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = ROOT / "data" / "test.jsonl"
OUT_PATH = ROOT / "assets" / "presets.json"

# (preset id, label, test.jsonl index)
PRESETS = [
    ("pf-loop-runtime", "PF Loop Runtime w/ Unit Bug", 55),
    ("oop-unit-test-coverage", "OOP Unit-Test Coverage", 75),
    ("os-scheduling", "OS Scheduling Lab", 29),
]

_FIELD = r"^{}: (.*)$"


def _field(text: str, name: str) -> str:
    match = re.search(_FIELD.format(re.escape(name)), text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Missing field {name!r} in prompt")
    return match.group(1).strip()


def parse_prompt(user: str) -> dict:
    course = re.search(r"^Course: (.+?) — (.+)$", user, flags=re.MULTILINE)
    lab = re.search(r"^(Lab \d+): (.+)$", user, flags=re.MULTILINE)
    raw_log = user.split("RAW DATA LOG:\n", 1)[1]
    return {
        "profile": {
            "name": _field(user, "Name"),
            "registration_no": _field(user, "Registration No"),
            "section": _field(user, "Section"),
            "university": _field(user, "University"),
            "instructor": _field(user, "Instructor"),
            "date": _field(user, "Date"),
        },
        "lab": {
            "course_code": course.group(1),
            "course_title": course.group(2),
            "lab_number": lab.group(1),
            "experiment_title": lab.group(2),
            "department": _field(user, "Department"),
        },
        "raw_log": raw_log,
    }


def main() -> None:
    rows = [json.loads(line) for line in TEST_PATH.read_text(encoding="utf-8").splitlines()]
    presets = []
    for preset_id, label, index in PRESETS:
        messages = rows[index]["messages"]
        parsed = parse_prompt(messages[1]["content"])
        answer = json.loads(messages[2]["content"])
        presets.append(
            {
                "id": preset_id,
                "label": label,
                "university_id": answer["cover_page"]["university_id"],
                **parsed,
                "answer": answer,
            }
        )
    OUT_PATH.write_text(json.dumps(presets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(presets)} presets -> {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
