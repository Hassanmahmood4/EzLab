#!/usr/bin/env python3
"""Generate 300x300 placeholder university crest PNGs from universities.json."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "universities.json"
LOGOS_DIR = ROOT / "logos"

# Distinct muted academic colors per university id (R, G, B)
PALETTE: dict[str, tuple[int, int, int]] = {
    "nust": (30, 90, 60),
    "fast_nuces": (20, 70, 140),
    "comsats": (140, 40, 40),
    "uet_lahore": (90, 50, 20),
    "giki": (40, 80, 110),
    "pieas": (60, 50, 100),
    "lums": (100, 30, 50),
    "ned": (20, 90, 90),
    "air_university": (50, 70, 110),
    "itu": (110, 70, 20),
    "qau": (70, 90, 40),
    "pu": (80, 40, 70),
    "pak_austria": (25, 55, 95),
    "bahria": (15, 45, 100),
    "iiui": (35, 100, 55),
    "numl": (90, 35, 35),
    "szabist": (55, 25, 85),
    "iba": (120, 55, 25),
    "riphah": (25, 85, 75),
    "uet_taxila": (75, 45, 25),
}

SIZE = 300
MARGIN = 18


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ):
        path = Path(name)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _initials(university_id: str) -> str:
    parts = university_id.replace("_", " ").split()
    if len(parts) == 1:
        slug = parts[0]
        return slug[:4].upper() if len(slug) <= 4 else "".join(c for c in slug if c.isalpha())[:3].upper()
    return "".join(p[0] for p in parts).upper()[:4]


def _wrap_label(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.replace("(", " (").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:4]


def make_crest(university_id: str, full_name: str, out_path: Path) -> None:
    color = PALETTE.get(university_id, (50, 50, 50))
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer ring + filled disc
    draw.ellipse([MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN], fill=(*color, 255))
    draw.ellipse(
        [MARGIN + 10, MARGIN + 10, SIZE - MARGIN - 10, SIZE - MARGIN - 10],
        outline=(255, 255, 255, 230),
        width=3,
    )

    initials = _initials(university_id)
    title_font = _load_font(64 if len(initials) <= 3 else 48)
    label_font = _load_font(14)

    # Initials centered
    bbox = draw.textbbox((0, 0), initials, font=title_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((SIZE - tw) / 2, (SIZE - th) / 2 - 18),
        initials,
        fill=(255, 255, 255, 255),
        font=title_font,
    )

    # Short name under initials
    short = full_name.split("(")[0].strip()
    if len(short) > 42:
        short = short[:40].rstrip() + "…"
    lines = _wrap_label(draw, short, label_font, SIZE - 2 * MARGIN - 40)
    y = SIZE // 2 + 42
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=label_font)
        lw = bbox[2] - bbox[0]
        draw.text(((SIZE - lw) / 2, y), line, fill=(255, 255, 255, 220), font=label_font)
        y += 16

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    for university_id, meta in registry.items():
        out = LOGOS_DIR / f"{university_id}.png"
        make_crest(university_id, meta["full_name"], out)
        print(f"wrote {out.relative_to(ROOT.parent)}")
    print(f"generated {len(registry)} placeholder crests in {LOGOS_DIR}")


if __name__ == "__main__":
    main()
