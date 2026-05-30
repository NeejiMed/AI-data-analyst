"""
Insights service, orchestrates analytics datat & LLM interpretation.
This is the bridge between the analytics engine and the LLM layer.
"""
import structlog

from app.analytics.engine import AnalyticsResult
from app.llm.client import call_llm
from app.llm.parser import parse_insights_response, parse_text_response
from app.llm.prompts import (
    build_anomaly_explanation_prompt,
    build_insights_prompt,
    build_summary_prompt,
)
from app.llm.schemas import AnalyticsInsights

logger = structlog.get_logger()

class InsightsService:
    """
    Combines analytics results with LLM interpretation.
    Single responsibility is to take raw analytics data and return business insights.
    """

    def generate_insights(
            self,
            result: AnalyticsResult,
            user_question: str
    ) -> AnalyticsInsights:
        """
        Generate structured business insights from analytics results using the LLM.
        """
        logger.info(
            "generating_insights",
            query_type=result.query_type,
            question_preview=user_question[:60]
        )

        context = result.to_llm_context()
        messages = build_insights_prompt(context, user_question)

        raw = call_llm(messages, temperature=0.3, response_format="json")
        insights = parse_insights_response(raw)
        logger.info("insights_generated", insight_count=len(insights.key_insights))

        return insights

    def explain_anomalies(self, result: AnalyticsResult) -> str:
        """
        Generate natural language explanations for detected anomalies.
        """
        if not result.anomalies:
            return "No significant anomalies detected in this period."

        anomaly_lines = "\n".join([
            f"- {a.period}: {a.direction} of {abs(a.deviation_pct):.1f}% "
            f"({a.severity} severity)"
            for a in result.anomalies
        ])

        trend_lines = ""
        if result.quarterly_trends:
            trend_lines = "\n".join([
                f"- {q.quarter_label}: ${q.total_revenue:,.2f} "
                f"({q.revenue_growth_pct:+.1f}%)"
                if q.revenue_growth_pct is not None
                else f"- {q.quarter_label}: ${q.total_revenue:,.2f} (baseline)"
                for q in result.quarterly_trends
            ])

        messages = build_anomaly_explanation_prompt(anomaly_lines, trend_lines)
        raw = call_llm(messages, temperature=0.3)
        return parse_text_response(raw)

    def generate_executive_summary(self, result: AnalyticsResult) -> str:
            """
            Generate a concise executive summary of the analytics results.
            """

            context = result.to_llm_context()
            messages = build_summary_prompt(context, report_type="executive")
            raw = call_llm(messages, temperature=0.4, max_tokens=800)
            return parse_text_response(raw)
