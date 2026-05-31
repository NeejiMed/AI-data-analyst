"""Test the RAG pipeline — ingestion, retrieval, and LLM integration."""
import os
import sys
from datetime import datetime

from app.analytics.engine import AnalyticsEngine
from app.data.database import SessionLocal
from app.llm.client import call_llm
from app.llm.parser import parse_insights_response
from app.llm.prompts import build_insights_prompt
from app.rag.pipeline import RAGPipeline
from app.rag.retrieval import ingest_knowledge_base

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("RAG PIPELINE TEST")
print("=" * 60)

# Test 1: Ingestion
print("\n1. Ingesting knowledge base...")
count = ingest_knowledge_base()
print(f"   Indexed {count} chunks")

# Test 2: Initialize pipeline
rag = RAGPipeline(auto_ingest=False)
stats = rag.get_stats()
print(f"\n2. Vector store stats: {stats}")

# Test 3: Retrieval
print("\n3. Testing semantic retrieval...")
test_queries = [
    "Why did revenue drop in Q2?",
    "What does the refund rate mean for the business?",
    "How should I interpret customer churn?",
]

for query in test_queries:
    results = rag.retrieve(query, n_results=2)
    print(f"\n   Query: '{query}'")
    for r in results:
        print(f"   >> [{r['score']:.2f}] {r['metadata']['section']}: "
            f"{r['document'][:80]}...")

# Test 4: Full RAG + Analytics + LLM pipeline
print("\n" + "=" * 60)
print("4. Full RAG-augmented insight generation...")
print("=" * 60)

db = SessionLocal()
analytics = AnalyticsEngine(db)
result = analytics.analyze_sales_trends(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2026, 6, 30),
)

question = "Why did revenue decrease in Q2 and what should we do about it?"
rag_context = rag.build_context(question)
analytics_context = result.to_llm_context()

messages = build_insights_prompt(analytics_context, question, rag_context)
raw = call_llm(messages, temperature=0.3, response_format="json")
insights = parse_insights_response(raw)

print(f"\nQuestion: {question}")
print(f"\nExecutive Summary:\n{insights.executive_summary}")
print("\nRecommended Actions:")
for action in insights.recommended_actions:
    print(f"  -> {action}")

db.close()
