"""Verify the analytics engine produces correct results."""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from app.analytics.engine import AnalyticsEngine
from app.data.database import SessionLocal

db = SessionLocal()
engine = AnalyticsEngine(db)

print("=== Sales Trend Analysis ===")
result = engine.analyze_sales_trends(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2026, 6, 30),
)
print(result.to_llm_context())

print("\n=== Anomalies Detected ===")
for a in result.anomalies:
    print(f"  {a.period}: {a.direction} ({a.severity}) - {a.deviation_pct}% from expected")

print("\n=== Customer Segmentation ===")
seg_result = engine.analyze_customer_segments(
    reference_date=datetime(2026, 6, 30)
)
for s in seg_result.segments:
    print(f"  {s.segment_name}: {s.customer_count} customers - {s.description}")

db.close()
