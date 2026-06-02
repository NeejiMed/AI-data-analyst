"""
Parses and validates raw LLM responses into structured Pydantic objects.
This is the defensive layer between raw LLM output and application logic.
"""

import json
import re

import structlog
from pydantic import ValidationError

from app.llm.schemas import AnalyticsInsights

logger = structlog.get_logger()


def extract_json_from_response(raw: str) -> dict:
    """
    Extracts the JSON object from the raw LLM response string.
    LLMs sometimes wrap json in markdown code blocks, we strip that
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = cleaned.rstrip("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("json_parse_failed", error=str(e), raw_preview=raw[:200])
        raise ValueError(f"Failed to parse JSON from LLM response: {e}") from e


def parse_insights_response(raw: str) -> AnalyticsInsights:
    """
    parse and validate LLM insights response.
    Raises ValueError if response doesn't match expected format or fails validation.
    """
    try:
        data = extract_json_from_response(raw)
        return AnalyticsInsights(**data)
    except ValidationError as e:
        logger.error("insights_validation_failed", error=str(e))
        raise ValueError(f"LLM response failed validation: {e}") from e


def parse_text_response(raw: str) -> str:
    """
    For free-form text responses, we just return the cleaned string.
    """
    return raw.strip()
