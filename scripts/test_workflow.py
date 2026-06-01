import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.workflow import AnalyticsWorkflow  # noqa: E402
from app.data.database import SessionLocal  # noqa: E402

db = SessionLocal()
workflow = AnalyticsWorkflow(db)

test_questions = [
    "Analyze monthly sales trends and explain anomalies",
    "Generate customer segmentation insights",
    "What is the total revenue by product category?",
]

for question in test_questions:
    print("\n" + "=" * 60)
    print(f"QUESTION: {question}")
    print("=" * 60)

    response = workflow.run(question)

    print(f"Intent:     {response.intent}")
    print(f"Success:    {response.success}")
    print(f"Time:       {response.processing_time_ms}ms")

    if response.success:
        print(f"\nSummary:\n{response.executive_summary[:300]}...")
        if response.insights:
            print(f"\nInsights: {len(response.insights)}")
            print(f"  - {response.insights[0]['title']}")
        if response.chart_paths:
            print(f"\nCharts: {list(response.chart_paths.keys())}")
        if response.report_paths:
            print(f"Report: {response.report_paths}")
        if response.sql_query:
            print(f"\nSQL: {response.sql_query[:100]}...")
            print(f"Rows: {response.sql_row_count}")
    else:
        print(f"Error: {response.error}")

db.close()
