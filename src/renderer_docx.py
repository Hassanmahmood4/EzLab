"""Render LabPulse reports to Word (.docx) via docxtpl."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, Cm
from docxtpl import DocxTemplate, InlineImage

from src.schema import LabReportSchema
from src.validator import ValidationResult, report_to_resolved_dict

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "master_cover.docx"


def ensure_docx_template(path: Path = TEMPLATE_PATH) -> Path:
    """Create a Jinja2-ready Word template if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)

    # Cover
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("{{ university_logo }}")
    run.font.size = Pt(12)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("{{ university_full_name }}")
    r.bold = True
    r.font.size = Pt(16)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("{{ cover.department }}")
    r.font.size = Pt(12)

    lab = doc.add_paragraph()
    lab.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = lab.add_run("{{ cover.lab_number }} — {{ cover.experiment_title }}")
    r.bold = True
    r.font.size = Pt(14)

    meta_lines = [
        "Course: {{ cover.course_code }} — {{ cover.course_title }}",
        "Student: {{ cover.student_name }}",
        "Registration No: {{ cover.registration_no }}",
        "Section: {{ cover.section }}",
        "Instructor: {{ cover.instructor }}",
        "Submission Date: {{ cover.submission_date }}",
    ]
    for line in meta_lines:
        p = doc.add_paragraph(line)
        p.paragraph_format.space_after = Pt(2)

    doc.add_page_break()

    doc.add_heading("Abstract", level=1)
    doc.add_paragraph("{{ body.abstract }}")

    doc.add_heading("Apparatus / Tools", level=1)
    doc.add_paragraph("{% for item in body.apparatus %}- {{ item }}\n{% endfor %}")

    doc.add_heading("Methodology", level=1)
    doc.add_paragraph("{{ body.methodology }}")

    doc.add_heading("Equations", level=1)
    doc.add_paragraph("{% for eq in body.equations_latex %}{{ eq }}\n{% endfor %}")

    doc.add_heading("Anomaly Check", level=1)
    doc.add_paragraph("Status: {{ anomaly.status }}")
    doc.add_paragraph("{% for flag in anomaly.flags %}- {{ flag }}\n{% endfor %}")

    doc.add_heading("Results", level=1)
    doc.add_paragraph("{% for table in tables %}")
    doc.add_paragraph("{{ table.caption }}")
    doc.add_paragraph("{{ table.rendered }}")
    doc.add_paragraph("{% endfor %}")

    doc.add_heading("Figure", level=1)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("{{ plot_image }}")

    doc.add_heading("Discussion", level=1)
    doc.add_paragraph("{{ body.discussion }}")

    doc.add_heading("Conclusion", level=1)
    doc.add_paragraph("{{ body.conclusion }}")

    doc.save(path)
    return path


def _render_table_block(headers: list[str], rows: list[list[str]]) -> str:
    lines = [" | ".join(headers), " | ".join("---" for _ in headers)]
    for row in rows:
        lines.append(" | ".join(row))
    return "\n".join(lines)


def build_docx_context(result: ValidationResult, tpl: DocxTemplate) -> dict[str, Any]:
    report = result.report
    resolved = report_to_resolved_dict(result)

    tables = []
    for table in report.report_body.tables:
        tables.append(
            {
                "caption": table.caption,
                "headers": table.headers,
                "rows": table.rows,
                "rendered": _render_table_block(table.headers, table.rows),
            }
        )

    logo = InlineImage(tpl, str(result.logo_path), width=Inches(1.1))
    plot_image = ""
    if result.plot_path and result.plot_path.exists():
        plot_image = InlineImage(tpl, str(result.plot_path), width=Inches(5.2))

    return {
        "university_logo": logo,
        "university_full_name": resolved["university_full_name"],
        "cover": report.cover_page.model_dump(),
        "anomaly": {
            "status": report.anomaly_check.status.value,
            "flags": report.anomaly_check.flags,
        },
        "body": {
            "abstract": report.report_body.abstract,
            "apparatus": report.report_body.apparatus,
            "methodology": report.report_body.methodology,
            "equations_latex": report.report_body.equations_latex,
            "discussion": report.report_body.discussion,
            "conclusion": report.report_body.conclusion,
        },
        "tables": tables,
        "plot_image": plot_image,
    }


def render_docx(
    result: ValidationResult,
    output_path: Path,
    template_path: Path = TEMPLATE_PATH,
) -> Path:
    ensure_docx_template(template_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tpl = DocxTemplate(str(template_path))
    context = build_docx_context(result, tpl)
    tpl.render(context)
    tpl.save(str(output_path))
    return output_path


def render_docx_from_report(
    report: LabReportSchema | dict,
    raw_log: str,
    output_path: Path,
    work_dir: Path | None = None,
) -> Path:
    from src.validator import validate_and_prepare

    result = validate_and_prepare(report, raw_log, work_dir=work_dir, run_plot=True)
    if result.plot_error:
        raise RuntimeError(f"plot failed: {result.plot_error}")
    return render_docx(result, output_path)
