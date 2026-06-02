"""
LLM client — wraps the Groq API using the OpenAI-compatible interface.
Handles retries, timeouts, and error normalization.
"""
import time

import structlog
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

def get_llm_client() -> OpenAI:
    """
    Returns an openai-compatible client pointed at the Groq API.
    Using the OpenAI SDK against Groq's API means 0 vendor lock-in - swapping to openai or anthropic
    requires two config values, not rewriting all the code that calls the client.
    """
    return OpenAI(
        api_key=settings.groq_api_key,
        base_url=settings.llm_base_url
    )

@retry(
    stop=stop_after_attempt(3),
    wait = wait_exponential(multiplier=1, min=2, max=10),# exponential backoff: 2s, 4s, 8s
    retry=retry_if_exception_type(Exception) # catch all exceptions, can be refined to specific
)

def call_llm(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 1500,
    response_format: str = "text" # or "json"
) -> str:
    """
    Core LLM call with automatic retry on failure

    args:
        messages: OpenAI-format message list
        temperature: 0.0 = deterministic, 1.0 = creative.
            Analytics insights use low temprature
        max_tokens: cap on response length
        response_format: "text" or "json"
    returns:
         Raw string response from the model
    """
    client = get_llm_client()
    _start = time.time()

    logger.info(
        "llm_call_start",
        model=settings.llm_model,
        temperature=temperature,
        message_count=len(messages)
    )

    kwargs = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)

    content = response.choices[0].message.content
    usage = response.usage

    # Record metrics
    from app.core.observability.metrics import record_llm_call
    record_llm_call(
        model=settings.llm_model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        latency_ms=int((time.time() - _start) * 1000),
        success=True,
    )

    logger.info(
        "llm_call_complete",
        prompt_tokens=usage.prompt_tokens,
        total_tokens=usage.total_tokens
    )

    return content
