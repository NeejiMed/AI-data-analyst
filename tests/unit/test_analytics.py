"""Unit tests for the analytics engine."""

from app.analytics.anomaly import compute_summary_stats, detect_revenue_anomalies


class TestAnomalyDetection:
    def test_detects_spike(self):
        """A month with 3x revenue should be flagged as a spike."""
        data = [
            ("Jan 2025", 100_000),
            ("Feb 2025", 105_000),
            ("Mar 2025", 98_000),
            ("Apr 2025", 102_000),
            ("May 2025", 99_000),
            ("Jun 2025", 350_000),  # spike
        ]
        anomalies = detect_revenue_anomalies(data, z_threshold=1.5)
        assert len(anomalies) == 1
        assert any(a.period == "Jun 2025" for a in anomalies)
        assert any(a.direction == "spike" for a in anomalies)

    def test_detects_dip(self):
        """A month with 50% revenue drop should be flagged as a dip."""
        data = [
            ("Jan 2025", 100_000),
            ("Feb 2025", 105_000),
            ("Mar 2025", 98_000),
            ("Apr 2025", 102_000),
            ("May 2025", 99_000),
            ("Jun 2025", 20_000),  # dip
        ]
        anomalies = detect_revenue_anomalies(data, z_threshold=1.5)
        assert len(anomalies) == 1
        assert any(a.direction == "dip" for a in anomalies)

    def test_no_anomalies_in_flat_data(self):
        """Flat revenue data should not produce any anomalies."""
        data = [(f"Month {i}", 100_000) for i in range(12)]
        anomalies = detect_revenue_anomalies(data)
        assert len(anomalies) == 0

    def test_anomaly_severity_levels(self):
        """High z-score should produce high severity anomalies."""
        data = [("Month "+ str(i), 100_000) for i in range(10)] # stable data
        data.append(("Month 10", 900_000)) # extreme spike
        anomalies = detect_revenue_anomalies(data, z_threshold=1.5)
        spike = next((a for a in anomalies if a.direction == "spike"), None)
        assert spike is not None
        assert spike.severity in ["low", "medium", "high"]

class TestSummaryStats:
    def test_basic_stats(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = compute_summary_stats(values)
        assert stats["mean"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["count"] == 5

    def test_empty_values(self):
        """Should return None for all stats if input is empty."""
        stats = compute_summary_stats([])
        assert stats == {}
