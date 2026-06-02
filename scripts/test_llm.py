"""
Test the full analytics + LLM pipeline end to end.
This is the first time the platform feels like an AI analyst.
"""

import os
import sys
from datetime import datetime

from app.analytics.engine import AnalyticsEngine
from app.data.database import session_local
from app.llm.insights import InsightsService

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db = session_local()
analytics = AnalyticsEngine(db)
insights_service = InsightsService()

print("=" * 60)
print("Running analytics engine...")
result = analytics.analyze_sales_trends(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2026, 6, 30),
)

print("Sending to LLM for interpretation...")
print("=" * 60)

# Test 1: Business question insights
question = "Analyze monthly sales trends and explain any anomalies"
insights = insights_service.generate_insights(result, question)

print("\n EXECUTIVE SUMMARY\n")
print(insights.executive_summary)

print("\n KEY INSIGHTS\n")
for i, insight in enumerate(insights.key_insights, 1):
    print(f"{i}. [{insight.severity.upper()}] {insight.title}")
    print(f"   {insight.explanation}")
    print(f"   Action: {insight.recommendation}\n")

print(" POSITIVE SIGNALS")
for s in insights.positive_signals:
    print(f"  + {s}")

print("\n RISK FACTORS")
for r in insights.risk_factors:
    print(f"  ! {r}")

print("\n RECOMMENDED ACTIONS")
for a in insights.recommended_actions:
    print(f"  -> {a}")

# Test 2: Anomaly explanation
print("\n" + "=" * 60)
print("ANOMALY EXPLANATION\n")
explanation = insights_service.explain_anomalies(result)
print(explanation)

# Test 3: Executive summary
print("\n" + "=" * 60)
print("EXECUTIVE SUMMARY (PROSE)\n")
summary = insights_service.generate_executive_summary(result)
print(summary)

db.close()
