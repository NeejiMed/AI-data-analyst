"""
Customer segmentation analysis.
RFM (Recency, Frequency, Monetary) scoring — industry standard approach.
"""
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.models.business import Order

logger = structlog.get_logger()

@dataclass
class CustomerSegment:
    segment_name: str
    customer_count: int
    avg_revenue: float
    avg_order_frequency: float
    pct_of_total: float
    description: str

def compute_rfm_segments(
        db: Session,
        reference_date: datetime
) -> list[CustomerSegment]:
    """
    RFM segmentation — Recency, Frequency, Monetary value.
    Standard CRM analytics technique used by every serious business.

    Segments:
    - Champions: bought recently, buy often, spend the most
    - Loyal: buy regularly, decent spend
    - At Risk: used to buy often but haven't recently
    - Lost: haven't bought in a long time
    """
    logger.info("Computing_RFM_segments", reference_date=reference_date)

    results = db.query(
        Order.customer_id,
        func.max(Order.order_date).label('last_order_date'),
        func.count(Order.id).label('frequency'),
        func.sum(Order.total_amount).label('monetary')
    ).filter(
        Order.status == 'completed'
    ).group_by(Order.customer_id).all()

    if not results:
        return []

    df = pd.DataFrame([{
        'customer_id': r.customer_id,
        'recency_days': (reference_date - r.last_order_date).days,
        'frequency': r.frequency,
        'monetary': float(r.monetary or 0)
    } for r in results])

    # score each dimension on a 1-4
    df["r_score"] = pd.qcut(df["recency_days"], q=4, labels=[4, 3, 2, 1]).astype(int) # more recent = higher score
    df["f_score"] = pd.qcut(df["frequency"].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int) # more frequent = higher score
    df["m_score"] = pd.qcut(df["monetary"].rank(method='first'), q=4, labels=[1, 2, 3, 4]).astype(int) # higher spend = higher score
    df["rfm_score"] = df["r_score"] + df["f_score"] + df["m_score"] # the higher the better ranking, ranges from 3 to 12

    # define segments based on RFM score
    def assign_segment(score: int) -> str:
        if score >= 10:
            return "Champions"
        elif score >= 8:
            return "Loyal"
        elif score >= 6:
            return "Promising"
        elif score >= 4:
            return "At Risk"
        else:
            return "Lost"

    df["segment"] = df["rfm_score"].apply(assign_segment)
    total_customers = len(df)

    segments = []
    for seg_name in ["Champions", "Loyal", "Promising", "At Risk", "Lost"]:
        seg_df = df[df["segment"] == seg_name]
        if seg_df.empty:
            continue

        description = {
            "Champions": "High value, recent, frequent buyers. Reward them.",
            "Loyal": "Regular buyers with solid spend. Upsell opportunities.",
            "Promising": "Recent buyers with growth potential.",
            "At Risk": "Previously active, now disengaged. Re-engage urgently.",
            "Lost": "Long inactive. Win-back campaign needed.",
        }

        segments.append(CustomerSegment(
            segment_name=seg_name,
            customer_count=len(seg_df),
            avg_revenue=round(seg_df["monetary"].mean(), 2),
            avg_order_frequency=round(seg_df["frequency"].mean(), 2),
            pct_of_total=round((len(seg_df) / total_customers * 100), 2),
            description=description[seg_name]
        ))

    return segments
