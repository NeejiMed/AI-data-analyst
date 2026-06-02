"""
Pydantic schemas for structured LLM output.
The LLM returns json, we validate it here before use in the app.
Never trust raw llm output without validation!
"""

from pydantic import BaseModel, Field


class InsightPoint(BaseModel):
    title: str = Field(description="Short insight headline")
    explanation: str = Field(description="2-3 sentence business explanation")
    severity: str = Field(description="info, warning or critical")
    recommendation: str = Field(
        description="Actionable recommendation for the business"
    )


class AnalyticsInsights(BaseModel):
    executive_summary: str = Field(
        description="3-4 sentence summary for a business executive"
    )
    key_insights: list[InsightPoint] = Field(
        description="3-5 specific insights from the data"
    )
    positive_signals: list[str] = Field(description="What is going well")
    risk_factors: list[str] = Field(description="What needs attention or improvement")
    recommended_actions: list[str] = Field(
        description="Top 3 recommended actions for the business"
    )


class AnomalyExplanation(BaseModel):
    period: str
    what_happened: str = Field(description="Plain english description of the anomaly")
    likely_cause: str = Field(
        description="Most probable business reason for the anomaly"
    )
    business_impact: str = Field(description="How this impacts the business")
    confidence: str = Field(description="high, medium or low")
