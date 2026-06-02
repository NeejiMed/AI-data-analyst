"""
Trend analysis — monthly/quarterly time series computation.
Returns structured data the LLM can interpret.
"""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import structlog
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.data.models.business import Order

logger = structlog.get_logger()


@dataclass
class MonthlyTrend:
    year: int
    month: int
    month_label: str
    total_revenue: float
    total_orders: int
    avg_order_value: float
    revenue_growth_pct: float | None  # vs previous month
    is_anomaly: bool


@dataclass
class QuarterlyTrend:
    year: int
    quarter: int
    quarter_label: str
    total_revenue: float
    total_orders: int
    revenue_growth_pct: float | None  # vs previous quarter


MONTH_NAMES = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def compute_monthly_trends(
    db: Session, start_date: datetime, end_date: datetime
) -> list[MonthlyTrend]:
    """
    Compute monthly trends.
    Flags months where growth deviates significantly from the mean.
    """
    logger.info("computing_monthly_trends")

    results = (
        db.query(
            extract("year", Order.order_date).label("year"),
            extract("month", Order.order_date).label("month"),
            func.sum(Order.total_amount).label("total_revenue"),
            func.count(Order.id).label("total_orders"),
            func.avg(Order.total_amount).label("aov"),
        )
        .filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status == "completed",
        )
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    if not results:
        return []

    # build into a pandas series for easier growth rate computation
    revenues = [float(r.total_revenue) for r in results]
    df = pd.Series(revenues)
    pct_changes = df.pct_change() * 100

    # anomaly: growth rate > 1.5 std dev from mean
    mean_growth = pct_changes[1:].mean()  # skip first NaN
    std_growth = pct_changes[1:].std()  # skip first NaN

    trends = []
    for i, row in enumerate(results):
        growth = float(pct_changes.iloc[i]) if i > 0 else None
        is_anomaly = (
            growth is not None
            and std_growth > 0
            and abs(growth - mean_growth) > 1.5 * std_growth
        )
        trends.append(
            MonthlyTrend(
                year=int(row.year),
                month=int(row.month),
                month_label=f"{MONTH_NAMES[int(row.month)]} {int(row.year)}",
                total_revenue=round(float(row.total_revenue), 2),
                total_orders=int(row.total_orders or 0),
                avg_order_value=round(float(row.aov or 0), 2),
                revenue_growth_pct=round(growth, 2) if growth is not None else None,
                is_anomaly=is_anomaly,
            )
        )

    return trends


def compute_quarterly_trends(
    db: Session, start_date: datetime, end_date: datetime
) -> list[QuarterlyTrend]:
    """
    Compute quarterly trends.
    """
    logger.info("computing_quarterly_trends")

    results = (
        db.query(
            extract("year", Order.order_date).label("year"),
            func.ceil(extract("month", Order.order_date) / 3).label("quarter"),
            func.sum(Order.total_amount).label("total_revenue"),
            func.count(Order.id).label("total_orders"),
        )
        .filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status == "completed",
        )
        .group_by("year", "quarter")
        .order_by("year", "quarter")
        .all()
    )

    revenues = [float(r.total_revenue or 0) for r in results]
    pct_changes = pd.Series(revenues).pct_change() * 100

    return [
        QuarterlyTrend(
            year=int(r.year),
            quarter=int(r.quarter),
            quarter_label=f"Q{int(r.quarter)} {int(r.year)}",
            total_revenue=round(float(r.total_revenue or 0), 2),
            total_orders=int(r.total_orders or 0),
            revenue_growth_pct=round(float(pct_changes.iloc[i]), 2) if i > 0 else None,
        )
        for i, r in enumerate(results)
    ]
