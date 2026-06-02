"""
KPI computation module.
All business metrics are computed here
"""

from dataclasses import dataclass
from datetime import datetime

import structlog
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.data.models.business import Order, OrderItem, Product

logger = structlog.get_logger()


@dataclass
class RevenueKPIs:
    total_revenue: float
    total_orders: int
    avg_order_value: float
    total_customers: int
    gross_profit: float
    gross_margin_pct: float
    refund_rate_pct: float
    period_start: datetime
    period_end: datetime


@dataclass
class RegionalKPIs:
    region: str
    total_revenue: float
    total_orders: int
    avg_order_value: float
    market_share_pct: float


def compute_revenue_kpis(
    db: Session, start_date: datetime, end_date: datetime
) -> RevenueKPIs:
    """
    Compute revenue-related KPIs for a given time period.
    """
    logger.info("Computing_revenue_KPIs", start_date=start_date, end_date=end_date)

    base_filter = and_(Order.order_date >= start_date, Order.order_date <= end_date)

    # revenue from completed orders
    completed = (
        db.query(
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("orders"),
            func.count(func.distinct(Order.customer_id)).label("customers"),
        )
        .filter(base_filter, Order.status == "completed")
        .first()
    )

    # refunds
    refunded_count = (
        db.query(func.count(Order.id))
        .filter(base_filter, Order.status == "refunded")
        .scalar()
        or 0
    )

    total_orders = (completed.orders or 0) + refunded_count

    # gross profit via order items + product cost
    cost_result = (
        db.query(func.sum(Product.cost_price * OrderItem.quantity).label("total_cost"))
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(base_filter, Order.status == "completed")
        .first()
    )

    total_revenue = float(completed.revenue or 0)
    total_cost = float(cost_result.total_cost or 0)
    gross_profit = total_revenue - total_cost

    return RevenueKPIs(
        total_revenue=round(total_revenue, 2),
        total_orders=completed.orders or 0,
        avg_order_value=round(
            total_revenue / completed.orders if completed.orders else 0, 2
        ),
        total_customers=completed.customers or 0,
        gross_profit=round(gross_profit, 2),
        gross_margin_pct=round(
            (gross_profit / total_revenue * 100) if total_revenue else 0, 2
        ),
        refund_rate_pct=round(
            (refunded_count / total_orders * 100) if total_orders else 0, 2
        ),
        period_start=start_date,
        period_end=end_date,
    )


def compute_regional_kpis(
    db: Session, start_date: datetime, end_date: datetime
) -> list[RegionalKPIs]:
    """
    Compute regional KPIs with market share
    """
    results = (
        db.query(
            Order.region,
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("orders"),
            func.avg(Order.total_amount).label("aov"),
        )
        .filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status == "completed",
        )
        .group_by(Order.region)
        .all()
    )

    total_revenue = sum(r.revenue or 0 for r in results)

    return [
        RegionalKPIs(
            region=r.region,
            total_revenue=round(float(r.revenue or 0), 2),
            total_orders=r.orders or 0,
            avg_order_value=round(float(r.aov or 0), 2),
            market_share_pct=round(
                (float(r.revenue or 0) / total_revenue * 100) if total_revenue else 0, 2
            ),
        )
        for r in sorted(results, key=lambda x: x.revenue or 0, reverse=True)
    ]
