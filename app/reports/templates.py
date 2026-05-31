"""
Report templates and data structures.
A report is a structured document that presents insights derived from data analysis.
Seperating the data model from the renderer means we can produce markdown reports, PDFs or HTML from the same report object.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ReportType(Enum):
    SALES_TREND = "sales_trend"
    EXECUTIVE_SUMMARY = "executive_summary"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    ANOMALY_INVESTIGATION = "anomaly_investigation"
    CUSTOM = "custom"

class SectionType(Enum):
    HEADER = "header"
    SUMMARY = "summary"
    METRICS_TABLE = "metrics_table"
    INSIGHTS_LIST = "insights_list"
    TREND_TABLE = "trend_table"
    ANOMALY_TABLE = "anomaly_table"
    SEGMENT_TABLE = "segment_table"
    RECOMMENDATIONS = "recommendations"
    NARRATIVE = "narrative"

@dataclass
class ReportSection:
    type: SectionType # The type of section, which determines how it should be rendered.
    title: str # A title for the section, which can be used in the report's table of contents or as a header.
    content: str | list | dict # Depending on the section type, content can be a string (for narrative sections), a list of insights, or a dict for tables.
    order: int = 0 # Order in which the section should appear in the report

@dataclass
class Report:
    title: str
    report_type: ReportType # The type of report, which can be used to determine the overall structure and which sections to include.
    period_start: datetime # The start date of the reporting period.
    period_end: datetime # The end date of the reporting period.
    generated_at: datetime = field(default_factory=datetime.now) # When the report was generated.
    sections: list[ReportSection] = field(default_factory=list) # A list of sections that make up the report.
    metadata: dict = field(default_factory=dict) # Additional metadata about the report, such as the data sources used, the analyst who generated it, etc.

    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report."""
        section.order = len(self.sections) # Set the order based on the current number of sections
        self.sections.append(section)

    @property
    def filename_base(self) -> str:
        """Generate a base filename for the report based on its title and period."""
        date_str = self.generated_at.strftime("%Y%m%d_%H%M%S") # Use generation timestamp for uniqueness
        type_str = self.report_type.value
        return f"report_{type_str}_{date_str}"
