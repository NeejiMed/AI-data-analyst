"""Integration tests for the FastAPI endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    mock_settings = MagicMock()
    mock_settings.groq_api_key = "test-key"
    with patch("app.core.config.get_settings", return_value=mock_settings):
        from app.main import app
        return TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contains_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_health_contains_components(self, client):
        response = client.get("/health")
        data = response.json()
        assert "components" in data


class TestMetricsEndpoint:

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_structure(self, client):
        response = client.get("/metrics")
        data = response.json()
        assert "llm" in data
        assert "workflow" in data
        assert "uptime_seconds" in data


class TestRootEndpoint:

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
