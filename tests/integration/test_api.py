"""Integration tests for the FastAPI endpoints."""
import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test.db")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client():
    """Create a test client."""
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
