"""
PDF report renderer using reportlab.
Converts a Report object into a professional PDF document.
"""
from pathlib import Path

import structlog

from app.reports.templates import Report, SectionType

logger = structlog.get_logger()
# ruff: noqa: E402

def _check_reportlab() -> bool:
    """Check if reportlab is available without importing it."""
    import importlib.util
    return importlib.util.find_spec("reportlab") is not None


class PDFRenderer:
    """
    Renders a Report as a PDF document using reportlab.
    Falls back to saving Markdown if reportlab is not installed.
    """

    def save(self, report: Report, output_dir: str = "outputs/reports") -> str:
        """Render and save report as PDF. Returns the file path."""

        if not _check_reportlab():
            logger.warning(
                "reportlab_not_installed_falling_back_to_markdown"
            )
            from app.reports.markdown_renderer import MarkdownRenderer
            return MarkdownRenderer().save(report, output_dir)

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filepath = f"{output_dir}/{report.filename_base}.pdf"

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        style_h1 = ParagraphStyle(
            "H1", parent=styles["Heading1"],
            fontSize=20, spaceAfter=6,
        )
        style_h2 = ParagraphStyle(
            "H2", parent=styles["Heading2"],
            fontSize=14, spaceAfter=4, spaceBefore=12,
        )
        style_body = ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=10, spaceAfter=6, leading=14,
        )
        style_meta = ParagraphStyle(
            "Meta", parent=styles["Normal"],
            fontSize=9, textColor=colors.grey,
        )

        elements = []

        # Title
        elements.append(Paragraph(report.title, style_h1))
        elements.append(Paragraph(
            f"Period: {report.period_start.strftime('%B %d, %Y')} to "
            f"{report.period_end.strftime('%B %d, %Y')} | "
            f"Generated: {report.generated_at.strftime('%B %d, %Y')}",
            style_meta,
        ))
        elements.append(HRFlowable(width="100%", thickness=1,
                                    color=colors.lightgrey))
        elements.append(Spacer(1, 0.2 * inch))

        # Sections
        for section in sorted(report.sections, key=lambda s: s.order):
            elements.append(Paragraph(section.title, style_h2))

            if section.type in (SectionType.SUMMARY, SectionType.NARRATIVE):
                elements.append(Paragraph(str(section.content), style_body))

            elif section.type in (
                SectionType.METRICS_TABLE,
                SectionType.TREND_TABLE,
                SectionType.ANOMALY_TABLE,
                SectionType.SEGMENT_TABLE,
            ):
                if section.content:
                    headers = list(section.content[0].keys())
                    data = [headers] + [
                        [row.get(h, "") for h in headers]
                        for row in section.content
                    ]
                    col_width = (6.5 * inch) / len(headers)
                    table = Table(data, colWidths=[col_width] * len(headers))
                    table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                         [colors.white, colors.HexColor("#F8F9FA")]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("PADDING", (0, 0), (-1, -1), 4),
                    ]))
                    elements.append(table)

            elif section.type == SectionType.INSIGHTS_LIST:
                for insight in section.content:
                    sev = insight.get("severity", "info").upper()
                    elements.append(Paragraph(
                        f"<b>[{sev}] {insight.get('title', '')}</b>",
                        style_body,
                    ))
                    elements.append(Paragraph(
                        insight.get("explanation", ""), style_body
                    ))
                    elements.append(Paragraph(
                        f"<i>Action: {insight.get('recommendation', '')}</i>",
                        style_body,
                    ))

            elif section.type == SectionType.RECOMMENDATIONS:
                for i, action in enumerate(section.content, 1):
                    elements.append(Paragraph(
                        f"{i}. {action}", style_body
                    ))

            elements.append(Spacer(1, 0.1 * inch))

        doc.build(elements)
        logger.info("pdf_report_saved", filepath=filepath)
        return filepath
