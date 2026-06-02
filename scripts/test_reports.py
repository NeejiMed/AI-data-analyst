"""Test the full report generation pipeline."""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from app.analytics.engine import AnalyticsEngine  # noqa: E402
from app.data.database import SessionLocal  # noqa: E402
from app.llm.client import call_llm  # noqa: E402
from app.llm.parser import parse_insights_response, parse_text_response  # noqa: E402
from app.llm.prompts import build_insights_prompt, build_summary_prompt  # noqa: E402
from app.rag.pipeline import RAGPipeline  # noqa: E402
from app.reports.builder import ReportBuilder  # noqa: E402
from app.reports.markdown_renderer import MarkdownRenderer  # noqa: E402
from app.reports.pdf_renderer import PDFRenderer  # noqa: E402

print("=" * 60)
print("REPORT GENERATION ENGINE TEST")
print("=" * 60)

db = SessionLocal()
analytics = AnalyticsEngine(db)
rag = RAGPipeline(auto_ingest=False)
builder = ReportBuilder()
md_renderer = MarkdownRenderer()
pdf_renderer = PDFRenderer()

# Step 1: Get analytics data
print("\n1. Computing analytics...")
result = analytics.analyze_sales_trends(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2026, 6, 30),
)
print(f"   KPIs computed, {len(result.anomalies)} anomalies detected")

# Step 2: Generate LLM insights with RAG
print("2. Generating RAG-augmented insights...")
question = "Provide a comprehensive sales trend analysis"
rag_context = rag.build_context(question)
messages = build_insights_prompt(result.to_llm_context(), question, rag_context)
raw = call_llm(messages, temperature=0.3, response_format="json")
insights = parse_insights_response(raw)
print(f"   Generated {len(insights.key_insights)} insights")

# Step 3: Get executive summary prose
print("3. Generating executive summary...")

summary_messages = build_summary_prompt(result.to_llm_context())
exec_summary = parse_text_response(
    call_llm(summary_messages, temperature=0.4, max_tokens=600)
)
print(f"   Summary generated ({len(exec_summary)} chars)")

# Step 4: Build report object
print("4. Building report...")
report = builder.build_sales_trend_report(result, insights, exec_summary)
print(f"   Report built with {len(report.sections)} sections")

# Step 5: Save as Markdown
print("5. Saving Markdown report...")
md_path = md_renderer.save(report)
print(f"   Saved: {md_path}")

# Step 6: Save as PDF
print("6. Saving PDF report...")
pdf_path = pdf_renderer.save(report)
print(f"   Saved: {pdf_path}")

# Step 7: Preview markdown content
print("\n" + "=" * 60)
print("MARKDOWN PREVIEW (first 50 lines)")
print("=" * 60)
with open(md_path, encoding="utf-8") as f:
    lines = f.readlines()
    print("".join(lines[:80]))

db.close()
print("\nReport generation complete.")
