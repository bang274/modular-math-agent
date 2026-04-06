"""
Tests for API endpoints.

Covers: health, solve, upload, history, metrics,
        middleware (request ID, timing), error handler.
"""

import pytest

from app.telemetry.metrics import metrics


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


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        """Metrics endpoint should return summary data."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "latency" in data
        assert "p50_ms" in data["latency"]
        assert "p95_ms" in data["latency"]
        assert "p99_ms" in data["latency"]
        assert "error_rate_pct" in data
        assert "uptime_seconds" in data

    def test_metrics_has_tool_usage(self, client):
        """Metrics should include tool and route breakdowns."""
        response = client.get("/api/v1/metrics")
        data = response.json()
        assert "tool_usage" in data
        assert "route_usage" in data


class TestRequestIDMiddleware:
    def test_response_has_request_id(self, client):
        """Every response should include X-Request-ID header."""
        response = client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    def test_request_id_is_uuid_format(self, client):
        """Auto-generated request ID should be a valid UUID."""
        import uuid
        response = client.get("/api/v1/health")
        request_id = response.headers["x-request-id"]
        # Should not raise ValueError
        uuid.UUID(request_id)

    def test_custom_request_id_preserved(self, client):
        """Client-supplied X-Request-ID should be preserved."""
        custom_id = "my-custom-trace-123"
        response = client.get(
            "/api/v1/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["x-request-id"] == custom_id


class TestTimingMiddleware:
    def test_response_has_process_time(self, client):
        """Every response should include X-Process-Time header."""
        response = client.get("/api/v1/health")
        assert "x-process-time" in response.headers
        # Should be a valid float
        elapsed = float(response.headers["x-process-time"])
        assert elapsed >= 0


class TestErrorHandler:
    def test_422_is_json(self, client):
        """Validation errors should return JSON."""
        response = client.post("/api/v1/solve", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
