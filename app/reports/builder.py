"""
Report builder that assembles a Report object from analytics and LLM data.
Seperates report construction logic from the rendering logic.
"""
import structlog

from app.analytics.engine import AnalyticsResult
from app.llm.schemas import AnalyticsInsights
from app.reports.templates import Report, ReportSection, ReportType, SectionType

logger = structlog.get_logger()

class ReportBuilder:
    """
    Constructs structured Report objects from analytics results and insights data.
    the builder pattern lets us compose reports section by section, and easily extend the report structure in the future.
    """

    def build_sales_trend_report(
            self,
            result: AnalyticsResult,
            insights: AnalyticsInsights,
            executive_summary: str = ""
    ) -> Report:
        """Build a sales trend report from analytics results and insights."""
        logger.info("Building sales trend report", result=result, insights=insights)

        report = Report(
            title="Sales trend analysis report",
            report_type=ReportType.SALES_TREND,
            period_start=result.period_start,
            period_end=result.period_end
        )

        # Section 1: Executive summary
        report.add_section(ReportSection(
            type=SectionType.SUMMARY,
            title="Executive Summary",
            content=executive_summary or insights.executive_summary
        ))

        # Section 2: Key metrics table
        if result.revenue_kpis:
            k = result.revenue_kpis
            report.add_section(ReportSection(
                type=SectionType.METRICS_TABLE,
                title="Key performance indicators",
                content=[
                    {"Metric": "Total revenue", "Value": f"${k.total_revenue:,.2f}"},
                    {"Metric": "Total orders", "Value": f"{k.total_orders:,}"},
                    {"Metric": "Average order value", "Value": f"${k.avg_order_value:,.2f}"},
                    {"Metric": "Gross profit", "Value": f"${k.gross_profit:,.2f}"},
                    {"Metric": "Gross margin", "Value": f"{k.gross_margin_pct}%"},
                    {"Metric": "Refund rate", "Value": f"{k.refund_rate_pct}%"}
                ]
            ))

        # Section 3: Regional breakdown
        if result.regional_kpis:
            report.add_section(ReportSection(
                type=SectionType.METRICS_TABLE,
                title="Regional performance",
                content=[
                    {
                        "Region": r.region,
                        "Revenue": f"${r.total_revenue:,.2f}",
                        "Orders": str(r.total_orders),
                        "Market Share": f"{r.market_share_pct}%",
                        "AOV": f"${r.avg_order_value:,.2f}"
                    }
                    for r in result.regional_kpis
                ]
            ))


        # Section 4: Quarterly trends
        if result.quarterly_trends:
            report.add_section(ReportSection(
                type=SectionType.TREND_TABLE,
                title="Quarterly Revenue Trends",
                content=[
                    {
                        "Quarter": q.quarter_label,
                        "Revenue": f"${q.total_revenue:,.2f}",
                        "Orders": str(q.total_orders),
                        "Growth": (
                            f"{q.revenue_growth_pct:+.1f}%" if q.revenue_growth_pct is not None else "Baseline"
                        ),
                    }
                    for q in result.quarterly_trends
                ]
            ))

        # Section 5: Anomalies
        if result.anomalies:
            report.add_section(ReportSection(
                type=SectionType.ANOMALY_TABLE,
                title="Detected Anomalies",
                content=[
                    {
                        "Period": a.period,
                        "Type": a.direction.title(),
                        "Deviation": f"{a.deviation_pct:.1f}%",
                        "Severity": a.severity.upper(),
                        "Expected": f"${a.expected_value:,.2f}"
                    } for a in result.anomalies
                ]
            ))

        # Section 6: AI-generated insights
        report.add_section(ReportSection(
            type=SectionType.INSIGHTS_LIST,
            title="Key insights",
            content=[
                {
                    "title": i.title,
                    "explanation": i.explanation,
                    "severity": i.severity,
                    "recommendation": i.recommendation
                }
                for i in insights.key_insights
            ]
        ))

        # Section 7: Recommendations
        report.add_section(ReportSection(
            type=SectionType.RECOMMENDATIONS,
            title="Recommended actions",
            content=insights.recommended_actions
        ))

        logger.info("Report building complete", sections=len(report.sections), report_type=report.report_type)
        return report

    def build_segmentation_report(
            self,
            result: AnalyticsResult,
            insights: AnalyticsInsights
    ) -> Report:
        """Build a customer segmentation report from analytics results and insights."""
        report = Report(
            title="Customer segmentation report",
            report_type=ReportType.CUSTOMER_SEGMENTATION,
            period_start=result.period_start,
            period_end=result.period_end
        )

        report.add_section(ReportSection(
            type=SectionType.SUMMARY,
            title="Executive Summary",
            content=insights.executive_summary
        ))

        if result.segments:
            report.add_section(ReportSection(
                type=SectionType.SEGMENT_TABLE,
                title="Customer segments (RFM analysis)", # RFM = Recency, Frequency, Monetary value
                content=[
                    {
                        "Segment": s.segment_name,
                        "Customers": str(s.customer_count),
                        "% of total": f"{s.pct_of_total}%",
                        "Avg Revenue": f"${s.avg_revenue:,.2f}",
                        "Average orders": f"{s.avg_order_frequency:.1f}",
                        "Description": s.description
                    } for s in result.segments
                ]
            ))

        report.add_section(ReportSection(
            type=SectionType.RECOMMENDATIONS,
            title="Recommended actions",
            content=insights.recommended_actions
        ))

        return report
