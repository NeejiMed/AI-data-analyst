"""
Test the SQL generation agent with realistic business questions.
Verifies both correct generation and security validation.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.query_validator import QueryValidationError, validate_sql
from app.agents.sql_agent import SQLAgent
from app.data.database import SessionLocal

db = SessionLocal()
agent = SQLAgent(db)

# ── Test 1: Business questions ──────────────────────────────
questions = [
    "What is the total revenue by region?",
    "Which product category generates the most revenue?",
    "Show me the top 10 customers by total spend",
    "What is the monthly revenue trend for 2025?",
    "What percentage of orders were refunded?",
]

print("=" * 60)
print("SQL AGENT — BUSINESS QUESTIONS")
print("=" * 60)

for question in questions:
    print(f"\nQuestion: {question}")
    result = agent.run(question)

    if result.success:
        print(f"SQL: {result.validated_sql}")
        print(f"Rows: {result.row_count}")
        if result.rows:
            # Show first 3 rows
            for row in result.rows[:3]:
                print(f"  {row}")
    else:
        print(f"ERROR: {result.error}")
    print("-" * 40)

# ── Test 2: Security validation ─────────────────────────────
print("\n" + "=" * 60)
print("SECURITY VALIDATOR TESTS")
print("=" * 60)

attack_vectors = [
    ("DROP TABLE orders", "Should block DROP"),
    ("SELECT * FROM orders; DROP TABLE orders", "Should block stacked query"),
    ("SELECT * FROM sqlite_master", "Should block system table"),
    ("UPDATE orders SET status='refunded'", "Should block UPDATE"),
    ("SELECT * FROM orders UNION SELECT * FROM customers", "Should block UNION"),
]

for sql, description in attack_vectors:
    try:
        validate_sql(sql)
        print(f"FAIL — {description}: Query was NOT blocked")
    except QueryValidationError as e:
        print(f"PASS — {description}: Blocked with: {e}")

db.close()
