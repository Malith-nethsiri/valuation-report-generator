"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_health(self, client: TestClient):
        """Test root endpoint returns health status."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data

    def test_api_health(self, client: TestClient):
        """Test /api/health endpoint returns health status."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data

    def test_detailed_health(self, client: TestClient):
        """Test /api/health/detailed endpoint returns detailed status."""
        response = client.get("/api/health/detailed")

        assert response.status_code == 200
        data = response.json()

        # Should have status
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # Should have timestamp
        assert "timestamp" in data

        # Should have checks section
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_detailed_health_includes_database_check(self, client: TestClient):
        """Test that detailed health includes database connectivity check."""
        response = client.get("/api/health/detailed")

        assert response.status_code == 200
        data = response.json()

        # Database check should be present
        assert "database" in data["checks"]
        assert "status" in data["checks"]["database"]
