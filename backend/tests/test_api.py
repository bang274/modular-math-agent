"""
Tests for API endpoints.
"""

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        """Health check should return 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestSolveEndpoint:
    def test_solve_requires_text(self, client):
        """Solve should reject empty body."""
        response = client.post("/api/v1/solve", json={})
        assert response.status_code == 422  # Validation error

    def test_solve_rejects_empty_text(self, client):
        """Solve should reject empty text."""
        response = client.post("/api/v1/solve", json={"text": ""})
        assert response.status_code == 422


class TestUploadEndpoint:
    def test_upload_requires_input(self, client):
        """Upload should require at least text or image."""
        response = client.post("/api/v1/upload")
        assert response.status_code in (400, 422)


class TestHistoryEndpoint:
    def test_history_returns_list(self, client):
        """History should return paginated list."""
        response = client.get("/api/v1/history")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
