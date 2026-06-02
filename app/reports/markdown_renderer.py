"""
Markdown report renderer.
Converts a Report object into a clean Markdown document.
"""

from pathlib import Path

import structlog

from app.reports.templates import Report, ReportSection, SectionType

logger = structlog.get_logger()


class MarkdownRenderer:
    """Renders a Report object into Markdown document."""

    def render(self, report: Report) -> str:
        """Convert the Report object into a Markdown string."""
        lines = []

        # Document header
        lines += [
            f"# {report.title}",
            "",
            f"**Period:** {report.period_start.strftime('%B %d, %Y')} "
            f"to {report.period_end.strftime('%B %d, %Y')}",
            f"**Generated:** {report.generated_at.strftime('%B %d, %Y at %H:%M')}",
            "",
            "---",
            "",
        ]

        # Render each section
        for section in sorted(report.sections, key=lambda s: s.order):
            lines += self._render_section(section)
            lines.append("")  # Add spacing between sections

        return "\n".join(lines)

    def _render_section(self, section: ReportSection) -> list[str]:
        """Render a single section"""
        lines = [f"## {section.title}", ""]

        if section.type == SectionType.SUMMARY:
            lines += [str(section.title), ""]

        elif section.type == SectionType.NARRATIVE:
            lines += [str(section.content), ""]

        elif section.type in (
            SectionType.METRICS_TABLE,
            SectionType.TREND_TABLE,
            SectionType.ANOMALY_TABLE,
            SectionType.SEGMENT_TABLE,
        ):
            lines += self._render_table(section.content)

        elif section.type == SectionType.INSIGHTS_LIST:
            lines += self._render_insights(section.content)

        elif section.type == SectionType.RECOMMENDATIONS:
            lines += self._render_recommendations(section.content)

        return lines

    def _render_table(self, rows: list[dict]) -> list[str]:
        """Render a list of dicts as a Markdown table."""
        if not rows:
            return ["*No data available*", ""]

        headers = list(rows[0].keys())
        lines = []

        # Header row
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Data rows
        for row in rows:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")

        lines.append("")  # Add spacing after table
        return lines

    def _render_insights(self, insights: list[dict]) -> list[str]:
        """Render a list of insights as Markdown."""
        lines = []
        severity_icons = {"critical": "🔴", "warning": "🟡", "info": "🟢"}

        for insight in insights:
            icon = severity_icons.get(insight.get("severity", "info").lower(), "🟢")
            lines += [
                f"### {icon} {insight.get('title', 'Insight')}",
                "",
                insight.get("explanation", ""),
                "",
                f"**Recommendation:** {insight.get('recommendation', '')}",
                "",
            ]

        return lines

    def _render_recommendations(self, actions: list[str]) -> list[str]:
        """Render a list of recommendations as numbered Markdown list."""
        lines = []
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action}")

        lines.append("")  # Add spacing after list
        return lines

    def save(self, report: Report, output_dir: str = "outputs/reports") -> str:
        """
        Save the rendered Markdown report to a file.
        Returns the path to the saved file.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        content = self.render(report)
        filepath = f"{output_dir}/{report.filename_base}.md"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("markdown_report_saved", filepath=filepath)
        return filepath
