"""
Analytics engine — main entry point.
Orchestrates KPI computation, trend analysis, anomaly detection,
and segmentation into a single structured result.
"""
from dataclasses import dataclass, field
from datetime import datetime

import structlog
from sqlalchemy.orm import Session

from app.analytics.anomaly import (
    Anomaly,
    compute_summary_stats,
    detect_revenue_anomalies,
)
from app.analytics.kpi import (
    RegionalKPIs,
    RevenueKPIs,
    compute_regional_kpis,
    compute_revenue_kpis,
)
from app.analytics.segmentation import CustomerSegment, compute_rfm_segments
from app.analytics.trends import (
    MonthlyTrend,
    QuarterlyTrend,
    compute_monthly_trends,
    compute_quarterly_trends,
)

logger = structlog.get_logger()

@dataclass
class AnalyticsResult:
    """
    structured result returned by the analytics engine.
    """
    query_type: str
    period_start: datetime
    period_end: datetime
    revenue_kpis: RevenueKPIs | None = None
    regional_kpis: list[RegionalKPIs] = field(default_factory=list)
    monthly_trends: list[MonthlyTrend] = field(default_factory=list)
    quarterly_trends: list[QuarterlyTrend] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    segments: list[CustomerSegment] = field(default_factory=list)
    summary_stats: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_llm_context(self) -> str:
        """
        Serialize analytics result into a structured string
        the LLM can reason over. This is injected into prompts.
        """
        lines = [
            f"## Analytics Report: {self.query_type}",
            f"Period: {self.period_start.date()} to {self.period_end.date()}",
            "",
        ]

        if self.revenue_kpis:
            k = self.revenue_kpis
            lines += [
                "### Revenue KPIs",
                f"- Total Revenue: ${k.total_revenue:,.2f}",
                f"- Total Orders: {k.total_orders}",
                f"- Average Order Value: ${k.avg_order_value:,.2f}",
                f"- Gross Profit: ${k.gross_profit:,.2f}",
                f"- Gross Margin: {k.gross_margin_pct:.2f}%",
                f"- Refund Rate: {k.refund_rate_pct:.2f}%",
                "",
            ]

        if self.regional_kpis:
            lines.append("### Regional breakdown")
            for r in self.regional_kpis:
                lines.append(
                    f"- {r.region}: ${r.total_revenue:,.2f} "
                    f"({r.market_share_pct}% share)"
                    f"{r.total_orders} orders"
                )
            lines.append("")

        if self.anomalies:
            lines.append("### Detected Anomalies")
            for a in self.anomalies:
                lines.append(
                    f"- [{a.severity.upper()}] {a.period}:"
                    f" {a.direction} of {abs(a.deviation_pct):.1f}% "
                    f"vs expected ${a.expected_value:,.2f}"
                )
            lines.append("")

        if self.segments:
            lines.append("### Customer Segments (RFM)")
            for s in self.segments:
                lines.append(
                    f"- {s.segment_name}: {s.customer_count} customers "
                    f"({s.pct_of_total}%), avg revenue ${s.avg_revenue:,.2f}"
                )
            lines.append("")

        if self.quarterly_trends:
            lines.append("### Quarterly Trends")
            for q in self.quarterly_trends:
                growth = (
                    f"{q.revenue_growth_pct:+.1f}%"
                    if q.revenue_growth_pct is not None else "baseline"
                )
                lines.append(
                    f"- {q.quarter_label}: ${q.total_revenue:,.2f} ({growth})"
                )
            lines.append("")

        return "\n".join(lines)

class AnalyticsEngine:
    """
    Main analytics engine.
    Each public method corresponds to a business question type.
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_sales_trends(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> AnalyticsResult:

        logger.info("Workflow_running_sales_trends_analysis", start_date=start_date, end_date=end_date)

        kpis = compute_revenue_kpis(self.db, start_date, end_date)
        monthly = compute_monthly_trends(self.db, start_date, end_date)
        quarterly = compute_quarterly_trends(self.db, start_date, end_date)
        regional = compute_regional_kpis(self.db, start_date, end_date)

        monthly_revenues = [
            (m.month_label, m.total_revenue) for m in monthly
        ]
        anomalies = detect_revenue_anomalies(monthly_revenues)
        revenue_values = [m.total_revenue for m in monthly]
        stats = compute_summary_stats(revenue_values)

        return AnalyticsResult(
            query_type="Sales Trends Analysis",
            period_start=start_date,
            period_end=end_date,
            revenue_kpis=kpis,
            regional_kpis=regional,
            monthly_trends=monthly,
            quarterly_trends=quarterly,
            anomalies=anomalies,
            summary_stats=stats
        )

    def analyze_customer_segments(
        self,
        reference_date: datetime
    ) -> AnalyticsResult:
        logger.info("Workflow_running_customer_segmentation_analysis", reference_date=reference_date)

        segments = compute_rfm_segments(self.db, reference_date)
        kpis = compute_revenue_kpis(
            self.db,
            datetime(reference_date.year - 1, reference_date.month, 1),
            reference_date
        )
        return AnalyticsResult(
            query_type="Customer Segmentation Analysis",
            period_start=datetime(reference_date.year - 1,1,1),
            period_end=reference_date,
            revenue_kpis=kpis,
            segments=segments
        )
