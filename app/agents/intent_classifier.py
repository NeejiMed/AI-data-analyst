"""
Intent classifier agent that determines the user's intent based on their query and routes it to the appropriate handler (data retrieval, analysis, visualization, or report generation).

We use a lightweight LLM call with structured output rather than a keyword matcher.
This handles paraphrasing and ambiguous phrasing better that keyword matching would struggle with.
Example:
    "Why did we lose money in spring?" -> intent: sales_trends
    "Who are our best customers?"      -> intent: segmentation
    "Show me refunds by region"        -> intent: sql_query
    "What happened in October?"        -> intent: anomaly_investigation
"""

import json
from enum import StrEnum

import structlog

from app.llm.client import call_llm

logger = structlog.get_logger()


class QueryIntent(StrEnum):
    SALES_TREND = "sales_trend"
    SEGMENTATION = "segmentation"
    SQL_QUERY = "sql_query"
    ANOMALY_INVESTIGATION = "anomaly_investigation"
    GENERAL = "general"


INTENT_SYSTEM = """You are a query intent classifier for a business analytics platform.
Classify the user's question into exactly one category.

Categories:
- sales_trend: Questions about revenue over time, growth, quarterly/monthly performance
- segmentation: Questions about customer groups, segments, RFM (recency, frequency, monetary), customer behavior
- sql_query: Requests for specific data lookups, counts, lists, or custom queries
- anomaly_investigation: Questions about unusual events, spikes, dips or "why did X happen" type questions
- general: greetings, metaquestions, or unclear requests
Respond with ONLY a JSON object with the following format:
{"intent": "<category>", "confidence": <0-1 float>,"reasoning": "<one sentence>"}"""


def classify_intent(question: str) -> tuple[QueryIntent, float, str]:
    """Classify the user's query intent using an LLM.
    Returns:
        tuple of (intent, confidence, reasoning)
    """
    logger.info("Classifying_query_intent", question_preview=question[:60])

    messages = [
        {"role": "system", "content": INTENT_SYSTEM},
        {"role": "user", "content": question},
    ]

    try:
        raw = call_llm(
            messages, temperature=0.1, max_tokens=100, response_format="json"
        )
        data = json.loads(raw)
        intent_str = data.get("intent", "general")
        confidence = float(data.get("confidence", 0.5))
        reasoning = data.get("reasoning", "")

        intent = QueryIntent(intent_str)
        logger.info(
            "Intent_classified",
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
        )
        return intent, confidence, reasoning

    except Exception as e:
        logger.warning("Intent_classification_failed", error=str(e))
        return QueryIntent.GENERAL, 0.5, "Classification failed"
