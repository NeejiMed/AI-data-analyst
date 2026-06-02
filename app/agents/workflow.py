"""
Agentic workflow orchestrator.
Routes user questions to the correct pipeline and assembles responses.
This is the single entry point for handling all user queries in the system.
The frontend, API and CLI all call this one class.
"""

import time
from datetime import datetime

import structlog
from sqlalchemy.orm import Session

from app.agents.intent_classifier import QueryIntent, classify_intent
from app.agents.response import AgentResponse
from app.agents.sql_agent import SQLAgent
from app.analytics.engine import AnalyticsEngine
from app.llm.client import call_llm
from app.llm.parser import parse_insights_response, parse_text_response
from app.llm.prompts import (
    build_anomaly_explanation_prompt,
    build_insights_prompt,
    build_summary_prompt,
)
from app.rag.pipeline import RAGPipeline
from app.reports.builder import ReportBuilder
from app.reports.markdown_renderer import MarkdownRenderer
from app.visualization.engine import VisualizationEngine

logger = structlog.get_logger()

DEFAULT_START = datetime(2025, 1, 1)
DEFAULT_END = datetime(2026, 6, 30)


class AnalyticsWorkflow:
    """
    Main agentic workflow orchestrator for handling user queries.
    Responsibilities:
    - Classify user intent
    - Route to appropriate agents/pipelines
    - Execute analytics, LLM, RAG, visualization, and report generation steps
    - Return a unified AgentResponse object with all outputs for frontend consumption
    """

    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsEngine(db)
        self.sql_agent = SQLAgent(db)
        self.rag = RAGPipeline(auto_ingest=False)
        self.viz = VisualizationEngine()
        self.report_builder = ReportBuilder()
        self.md_renderer = MarkdownRenderer()

    def run(self, question: str) -> AgentResponse:
        """
        Main entry point. Accepts a user question, processes it, and returns a complete response.
        """
        start_time = time.time()
        logger.info("Workflow_started", question_preview=question[:80])

        # Step 1: Classify intent
        intent, confidence, reasoning = classify_intent(question)
        logger.info("Workflow_routing", intent=intent, confidence=confidence)

        # Step 2: Route to appropriate pipeline based on intent
        try:
            if intent == QueryIntent.SQL_QUERY:
                response = self._run_sql_pipeline(question, intent)
            elif intent == QueryIntent.SEGMENTATION:
                response = self._run_segmentation_pipeline(question, intent)
            elif intent == QueryIntent.ANOMALY_INVESTIGATION:
                response = self._run_anomaly_pipeline(question, intent)
            else:  # Default to sales trend analysis for general and sales_trend intents
                response = self._run_sales_trend_pipeline(question, intent)
        except Exception as e:
            logger.error("workflow_execution_failed", error=str(e))
            return AgentResponse(
                question=question, intent=intent, success=False, error=str(e)
            )

        # Step 3: Record processing time and return response
        elapsed_ms = int((time.time() - start_time) * 1000)
        response.processing_time_ms = elapsed_ms
        logger.info("Workflow_completed", intent=intent, processing_time_ms=elapsed_ms)
        return response

    def _run_sales_trend_pipeline(
        self, question: str, intent: QueryIntent
    ) -> AgentResponse:
        """Pipeline for handling sales trend analysis questions."""
        logger.info("Workflow_running_sales_trend_pipeline")

        # Analytics
        result = self.analytics.analyze_sales_trends(DEFAULT_START, DEFAULT_END)

        # RAG & LLM insights
        rag_context = self.rag.build_context(question)
        messages = build_insights_prompt(result.to_llm_context(), question, rag_context)
        raw = call_llm(messages, temperature=0.3, response_format="json")
        insights = parse_insights_response(raw)

        # Executive summary
        summary_messages = build_summary_prompt(result.to_llm_context())
        exec_summary = parse_text_response(
            call_llm(summary_messages, temperature=0.4, max_tokens=600)
        )

        # Visualizations
        charts = self.viz.generate_sales_charts(result)
        chart_paths = {name: data["paths"] for name, data in charts.items()}

        # Build report
        report = self.report_builder.build_sales_trend_report(
            result, insights, exec_summary
        )
        md_path = self.md_renderer.save(report)

        return AgentResponse(
            question=question,
            intent=intent,
            success=True,
            executive_summary=exec_summary,
            insights=[
                {
                    "title": ins.title,
                    "explanation": ins.explanation,
                    "severity": ins.severity,
                    "recommendation": ins.recommendation,
                }
                for ins in insights.key_insights
            ],
            positive_signals=insights.positive_signals,
            risk_factors=insights.risk_factors,
            recommended_actions=insights.recommended_actions,
            chart_paths=chart_paths,
            report_paths={"markdown": md_path},
        )

    def _run_segmentation_pipeline(
        self, question: str, intent: QueryIntent
    ) -> AgentResponse:
        """Customer segmentation analysis pipeline."""
        logger.info("Running_segmentation_pipeline")

        result = self.analytics.analyze_customer_segments(DEFAULT_END)
        rag_context = self.rag.build_context(question)
        messages = build_insights_prompt(result.to_llm_context(), question, rag_context)
        raw = call_llm(messages, temperature=0.3, response_format="json")
        insights = parse_insights_response(raw)

        charts = self.viz.generate_segmentation_charts(result)
        chart_paths = {name: data["paths"] for name, data in charts.items()}
        report = self.report_builder.build_segmentation_report(result, insights)
        md_path = self.md_renderer.save(report)

        return AgentResponse(
            question=question,
            intent=intent,
            success=True,
            executive_summary=insights.executive_summary,
            insights=[
                {
                    "title": ins.title,
                    "explanation": ins.explanation,
                    "severity": ins.severity,
                    "recommendation": ins.recommendation,
                }
                for ins in insights.key_insights
            ],
            positive_signals=insights.positive_signals,
            risk_factors=insights.risk_factors,
            recommended_actions=insights.recommended_actions,
            chart_paths=chart_paths,
            report_paths={"markdown": md_path},
        )

    def _run_anomaly_pipeline(
        self, question: str, intent: QueryIntent
    ) -> AgentResponse:
        """Anomaly investigation pipeline."""
        logger.info("Running_anomaly_pipeline")

        result = self.analytics.analyze_sales_trends(DEFAULT_START, DEFAULT_END)

        anomaly_lines = "\n".join(
            [
                f"- {a.period}: {a.direction} of "
                f"{abs(a.deviation_pct):.1f}% ({a.severity} severity)"
                for a in result.anomalies
            ]
        )

        trend_lines = "\n".join(
            [
                f"- {q.quarter_label}: ${q.total_revenue:,.2f} "
                f"({q.revenue_growth_pct:+.1f}%)"
                if q.revenue_growth_pct is not None
                else f"- {q.quarter_label}: ${q.total_revenue:,.2f} (baseline)"
                for q in result.quarterly_trends
            ]
        )

        messages = build_anomaly_explanation_prompt(anomaly_lines, trend_lines)

        explanation = parse_text_response(call_llm(messages, temperature=0.3))

        charts = self.viz.generate_sales_charts(result, save=True)
        chart_paths = {name: data["paths"] for name, data in charts.items()}

        return AgentResponse(
            question=question,
            intent=intent,
            success=True,
            executive_summary=explanation,
            chart_paths=chart_paths,
        )

    def _run_sql_pipeline(self, question: str, intent: QueryIntent) -> AgentResponse:
        """Pipeline for handling direct SQL query requests."""
        logger.info("Running_sql_pipeline")

        sql_result = self.sql_agent.run(question)

        if not sql_result.success:
            return AgentResponse(
                question=question,
                intent=intent,
                success=False,
                error=sql_result.error or "SQL query failed",
            )

        # Use LLM to interpret the result in plain English
        context = sql_result.to_llm_context()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a data analyst. Interpret the following "
                    "SQL query results and explain what they show "
                    "in 2-3 clear sentences for a business audience."
                ),
            },
            {
                "role": "user",
                "content": (f"Question: {question}\n\n" f"Query results:\n {context}"),
            },
        ]
        interpretation = parse_text_response(
            call_llm(messages, temperature=0.3, max_tokens=300)
        )

        return AgentResponse(
            question=question,
            intent=intent,
            success=True,
            executive_summary=interpretation,
            sql_query=sql_result.validated_sql,
            sql_results=sql_result.rows,
            sql_row_count=sql_result.row_count,
        )
