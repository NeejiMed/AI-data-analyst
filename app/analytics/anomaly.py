"""
Statistical anomaly detection.
Uses z-score and IQR methods — no ML model needed for this level of analysis.
"""

from dataclasses import dataclass

import numpy as np
import structlog

logger = structlog.get_logger()


@dataclass
class Anomaly:
    period: str
    metric: str
    value: float
    expected_value: float
    deviation_pct: float
    severity: (
        str  # this can be "low", "medium", "high" based on deviation_pct thresholds
    )
    direction: str  # this is spike or dip based on whether value is above or below expected_value


def detect_revenue_anomalies(
    monthly_revenues: list[tuple[str, float]], z_threshold: float = 1.5
) -> list[Anomaly]:
    """
    Detect anomalous months using z-score method.

    Args:
        monthly_revenues: list of (period_label, revenue) tuples
        z_threshold: standard deviations from mean to flag as anomaly

    Returns:
        List of detected anomalies with severity and direction
    """
    logger.info("Detecting_revenue_anomalies", z_threshold=z_threshold)

    if len(monthly_revenues) < 4:
        logger.warning("Not enough data points for reliable anomaly detection")
        return []

    labels = [m[0] for m in monthly_revenues]
    values = np.array([m[1] for m in monthly_revenues])
    mean = values.mean()
    std = values.std()

    if std == 0:
        logger.warning("No variation in data, cannot compute z-scores")
        return []

    z_scores = (values - mean) / std
    anomalies = []

    for i, (label, value, z) in enumerate(zip(labels, values, z_scores)):
        if abs(z) < z_threshold:
            continue

        deviation_pct = ((value - mean) / mean) * 100
        severity = "high" if abs(z) > 2.5 else "medium" if abs(z) > 2.0 else "low"

        anomalies.append(
            Anomaly(
                period=label,
                metric="revenue",
                value=round(float(value), 2),
                expected_value=round(float(mean), 2),
                deviation_pct=round(float(deviation_pct), 2),
                severity=severity,
                direction="spike" if value > mean else "dip",
            )
        )

    logger.info(
        "Anomaly_detection_complete",
        total_periods=len(monthly_revenues),
        total_anomalies=len(anomalies),
    )

    return anomalies


def compute_summary_stats(values: list[float]) -> dict:
    """
    Compute descriptive statistics for a numeric series.
    Used by the LLM to build context for interpretation of anomalies.
    """
    if not values:
        return {}

    arr = np.array(values)
    return {
        "mean": round(float(arr.mean()), 2),
        "median": round(float(np.median(arr)), 2),
        "std_dev": round(float(arr.std()), 2),
        "min": round(float(arr.min()), 2),
        "max": round(float(arr.max()), 2),
        "q1": round(float(np.percentile(arr, 25)), 2),
        "q3": round(float(np.percentile(arr, 75)), 2),
        "count": len(values),
    }
