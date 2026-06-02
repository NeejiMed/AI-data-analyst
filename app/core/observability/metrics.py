"""
In-process metrics collection.
Tracks LLM calls, query performance and error rates.
For a production system, you would export these to Prometheus or Datadog.
For our deployment tier, we store them in memory and expose them via a /metrics endpoint.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

import structlog

logger = structlog.get_logger()

# Thread-safe metrics store
_lock = Lock()  # To ensure thread safety when updating metrics


@dataclass
class LLMCallMetric:  # Tracks individual LLM calls within the workflow
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    success: bool


@dataclass
class WorkflowMetric:  # Tracks execution of the overall workflow for a user query
    timestamp: datetime
    intent: str
    processing_time_ms: int
    success: bool
    error: str = ""


@dataclass
class MetricsStore:  # Singleton class to store metrics in memory
    llm_calls: list[LLMCallMetric] = field(
        default_factory=list
    )  # List of LLM call metrics
    workflow_runs: list[WorkflowMetric] = field(
        default_factory=list
    )  # List of workflow execution metrics
    error_counts: dict = field(
        default_factory=lambda: defaultdict(int)
    )  # Count of different error types
    start_time: datetime = field(
        default_factory=datetime.now
    )  # When the application started


# Global metrics store - singleton instance
_metrics = MetricsStore()  # In-memory store for all metrics


def record_llm_call(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    success: bool = True,
) -> None:
    """Record a single LLM API call."""
    with _lock:
        _metrics.llm_calls.append(
            LLMCallMetric(
                timestamp=datetime.now(),
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=latency_ms,
                success=success,
            )
        )

    logger.debug(
        "llm_call_recorded",
        tokens=prompt_tokens + completion_tokens,
        latency_ms=latency_ms,
    )


def record_workflow_run(
    intent: str, processing_time_ms: int, success: bool, error: str = ""
) -> None:
    """Record a workflow execution."""
    with _lock:
        _metrics.workflow_runs.append(
            WorkflowMetric(
                timestamp=datetime.now(),
                intent=intent,
                processing_time_ms=processing_time_ms,
                success=success,
                error=error,
            )
        )
        if not success:
            _metrics.error_counts[intent] += 1

    logger.debug(
        "workflow_run_recorded", intent=intent, processing_time_ms=processing_time_ms
    )


def get_metrics_summary() -> dict:
    """
    Return aggregated metrics summary for monitoring.
    Exposed via /metrics endpoint for scraping by Prometheus or Datadog.
    """
    with _lock:
        llm_calls = _metrics.llm_calls
        workflow_runs = _metrics.workflow_runs
        uptime_seconds = (datetime.now() - _metrics.start_time).total_seconds()

    # LLM metrics
    total_llm_calls = len(llm_calls)
    total_tokens = sum(call.total_tokens for call in llm_calls)
    avg_latency_ms = (
        sum(call.latency_ms for call in llm_calls) / total_llm_calls
        if total_llm_calls
        else 0
    )

    estimated_monthly_cost = (
        total_tokens / 1_000_000
    ) * 0.59  # Assuming $0.59 per million tokens

    # Workflow metrics
    total_workflows = len(workflow_runs)
    successful = sum(1 for run in workflow_runs if run.success)
    success_rate = (successful / total_workflows) * 100 if total_workflows else 0
    avg_workflow_time = (
        sum(run.processing_time_ms for run in workflow_runs) / total_workflows
        if total_workflows
        else 0
    )

    # Intent distribution
    intent_counts: dict = defaultdict(int)
    for run in workflow_runs:
        intent_counts[run.intent] += 1

    return {
        "uptime_seconds": round(uptime_seconds),
        "llm": {
            "total_calls": total_llm_calls,
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency_ms),
            "estimated_cost_usd": round(estimated_monthly_cost, 4),
            "success_rate": round(
                sum(1 for call in llm_calls if call.success) / total_llm_calls * 100
                if total_llm_calls
                else 0,
                1,  # Success rate of LLM calls
            ),
        },
        "workflow": {
            "total_runs": total_workflows,
            "successful": successful,
            "success_rate_pct": round(success_rate, 1),
            "avg_processing_time_ms": round(avg_workflow_time),
            "intent_distribution": dict(intent_counts),  # Distribution of user intents,
            "error_counts": dict(
                _metrics.error_counts
            ),  # Count of different error types
        },
    }


def reset_metrics() -> None:
    """Reset all metrics - useful for testing or if you want to clear data."""
    with _lock:
        _metrics = MetricsStore()
