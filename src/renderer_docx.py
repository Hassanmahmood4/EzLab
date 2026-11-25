"""Render task / code / output lab reports to Word (.docx)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from src.validator import ValidationResult

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "master_cover.docx"

NAVY = RGBColor(0x1A, 0x27, 0x44)
MUTE = RGBColor(0x5C, 0x64, 0x78)
SOFT = "F4F6F9"


def ensure_docx_template(path: Path = TEMPLATE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        Document().save(path)
    return path


def _set_run(run, *, size=11, bold=False, italic=False, color=NAVY, font="Times New Roman"):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), font)
    rfonts.set(qn("w:hAnsi"), font)
    rfonts.set(qn("w:eastAsia"), font)


def _space(paragraph, before=0, after=6, line=1.15):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line


def _set_page_border(section) -> None:
    sect_pr = section._sectPr
    for child in list(sect_pr):
        if child.tag == qn("w:pgBorders"):
            sect_pr.remove(child)
    borders = OxmlElement("w:pgBorders")
    borders.set(qn("w:offsetFrom"), "page")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "12")
        el.set(qn("w:space"), "18")
        el.set(qn("w:color"), "1A2744")
        borders.append(el)
    sect_pr.append(borders)


def _shade_paragraph(paragraph, hex_color: str = SOFT) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    ppr.append(shd)


def _add_mono_block(doc: Document, label: str, text: str) -> None:
    heading = doc.add_paragraph()
    _space(heading, before=10, after=2)
    r = heading.add_run(label)
    _set_run(r, size=11, bold=True, color=NAVY)

    body = (text or "").rstrip() or "(none)"
    for line in body.splitlines() or [""]:
        p = doc.add_paragraph()
        _space(p, before=0, after=0, line=1.05)
        _shade_paragraph(p)
        run = p.add_run(line if line else " ")
        _set_run(run, size=9, color=NAVY, font="Courier New")


def render_docx(result: ValidationResult, output_path: Path) -> Path:
    report = result.report
    cover = report.cover_page
    resolved = {
        "university_full_name": result.university["full_name"],
    }

    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    for edge in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, edge, Cm(1.7))
    _set_page_border(section)

    if result.logo_path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _space(p, before=0, after=2)
        p.add_run().add_picture(str(result.logo_path), width=Cm(10))

    uni = doc.add_paragraph()
    uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _space(uni, before=0, after=1)
    r = uni.add_run(resolved["university_full_name"])
    _set_run(r, size=14, bold=True)

    meta_lines = [
        "LAB REPORT",
        f"{cover.lab_number}: {cover.experiment_title}",
        f"Course: {cover.course_code} — {cover.course_title}",
        f"Department: {cover.department}",
    ]
    if cover.section:
        meta_lines.append(f"Section: {cover.section}")
    if cover.semester:
        meta_lines.append(f"Semester: {cover.semester}")
    meta_lines.extend(
        [
            f"Submitted By: {cover.student_name}",
            f"Registration No.: {cover.registration_no}",
            f"Lab Instructor: {cover.instructor or '—'}",
            f"Submission Date: {cover.submission_date}",
        ]
    )
    for line in meta_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _space(p, before=0, after=2)
        r = p.add_run(line)
        _set_run(r, size=11)

    doc.add_page_break()

    for task in report.tasks:
        title = doc.add_paragraph()
        _space(title, before=14, after=6)
        r = title.add_run(f"Task {task.number} — {task.title}")
        _set_run(r, size=13, bold=True)

        if task.prompt.strip():
            prompt = doc.add_paragraph()
            _space(prompt, before=0, after=8)
            r = prompt.add_run(task.prompt.strip())
            _set_run(r, size=11)

        _add_mono_block(doc, "Code", task.code)
        _add_mono_block(doc, "Output", task.output)

        figures = list(getattr(task, "figures", None) or [])
        if figures:
            heading = doc.add_paragraph()
            _space(heading, before=10, after=4)
            r = heading.add_run("Visualization Output")
            _set_run(r, size=11, bold=True, color=NAVY)
            for name in figures:
                path = result.work_dir / name
                if not path.exists():
                    continue
                pic = doc.add_paragraph()
                pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _space(pic, before=2, after=6)
                pic.add_run().add_picture(str(path), width=Cm(14))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return output_path
