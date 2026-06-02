"""
Prompt templates for all LLM interactions.
Centralized here so prompt changes don't require hunting through business logic files.
Prompt engineering principles applied:
- System prompt defines role and constraints clearly
- User prompt contains only the data context and specific question, no instructions
- Output format is explicitly specified
- We instruct the model not to invent numbers
"""

SYSTEM_ANALYST = """You are a senior business intelligence analyst with 15 years
of experience interpreting data for C-suite executives.

Your role:
- Interpret pre-computed analytics data provided to you
- Explain trends, anomalies, and patterns in plain business language
- Provide actionable recommendations grounded in the data
- Be concise, specific, and avoid generic statements

Critical constraints:
- NEVER invent, estimate, or calculate numbers not explicitly provided
- ONLY reference figures that appear in the data context below
- If you are uncertain, say so explicitly
- Speak in terms of business impact, not technical metrics
- Audience: non-technical business executives"""

SYSTEM_SQL_ASSISTANT = """You are a precise SQL generation assistant.
You write safe, read-only SELECT queries based on a given database schema.
You never use DROP, DELETE, UPDATE, INSERT, or any data-modifying statements."""


def build_insights_prompt(
    analytics_context: str, user_question: str, rag_context: str = ""
) -> list[dict]:
    """
    Build the message list for insights generation.

    args:
        analystics_context: serialized AnalyticsResult.to_llm_context()
        user_question: the original business question from the user, e.g. "What are the key trends and anomalies in our sales data for the last quarter?"
        rag_context: relevant context retrieved from the RAG system

    returns:
    OpenAI-format messages list
    """
    rag_section = (
        f"\n**Business Domain Context:**\n{rag_context}\n" if rag_context else ""
    )

    return [
        {"role": "system", "content": SYSTEM_ANALYST},
        {
            "role": "user",
            "content": f"""Based on the following data, answer this question:

            **Business Question:** {user_question}
            {rag_section}
            **Analytics Data:**
            {analytics_context}

            Respond with a JSON object matching this exact structure:
            {{
                "executive_summary": "3-4 sentence summary",
                "key_insights": [
                    {{
                        "title": "insight headline",
                        "explanation": "2-3 sentence explanation",
                        "severity": "info|warning|critical",
                        "recommendation": "specific action to take"
                    }}
                ],
                "positive_signals": ["signal 1", "signal 2"],
                "risk_factors": ["risk 1", "risk 2"],
                "recommended_actions": ["action 1", "action 2", "action 3"]
            }}

            Base every insight strictly on the provided data. Do not add numbers not present above.""",
        },
    ]


def build_anomaly_explanation_prompt(
    anomaly_context: str, trend_context: str
) -> list[dict]:
    """
    Build prompt for explaining detected anomalies.
    """
    return [
        {"role": "system", "content": SYSTEM_ANALYST},
        {
            "role": "user",
            "content": f"""Explain the following detected anomalies in business terms.

            **Anomalies detected**:
            {anomaly_context}

            **Surrounding trend context**:
            {trend_context}

            Respond with a json object:
            {{
                "anomaly_explanations": [
                    {{
                        "period": "month/quarter label",
                        "what_happened": "Plain english description",
                        "likely_cause": "Most probable business reason",
                        "business_impact": "what this means for the business",
                        "confidence": "high|medium|low"
                    }},
                ],
                "overall_pattern": "one paragraph describing the overall trend pattern"
            }}""",
        },
    ]


def build_summary_prompt(
    analytics_context: str, report_type: str = "executive"
) -> list[dict]:
    """
    Build prompt for generating executive summary narratives.
    """
    tone = (
        "formal and concise, suitable for a board presentation"
        if report_type == "executive"
        else "analytical and detailed, suitable for a data team report"
    )

    return [
        {"role": "system", "content": SYSTEM_ANALYST},
        {
            "role": "user",
            "content": f"""Generate a {report_type} summary of the following analytics.

            Tone: {tone}
            **Data:**
            {analytics_context}

            Write 3-5 paragraphs covering: overall performance, key trends, notable anomalies
            and strategic recommendations.
            Ground every statement in the provided numbers.""",
        },
    ]
