"""Rate limit header tests.

Verify that X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset
headers are present on all API responses, including 429 responses.
"""

import time

import pytest


@pytest.mark.django_db
class TestRateLimitHeaders:
    """Test standard rate limit headers on API responses."""

    @pytest.fixture(autouse=True)
    def _rate_limit_settings(self, settings):
        """Set rate limit values for all tests in this class."""
        settings.RATE_LIMIT_GENERAL = 10
        settings.RATE_LIMIT_LOGIN = 3

    def test_response_includes_rate_limit_headers(self, client, django_user_model):
        """All API responses should include the three rate limit headers."""
        user = django_user_model.objects.create_user(username="rl_user", password="pass")
        client.force_login(user)
        resp = client.get("/api/health/", REMOTE_ADDR="10.0.1.1")
        assert "X-RateLimit-Limit" in resp
        assert "X-RateLimit-Remaining" in resp
        assert "X-RateLimit-Reset" in resp

    def test_remaining_decreases_with_requests(self, client, django_user_model):
        """X-RateLimit-Remaining should decrease with each request."""
        user = django_user_model.objects.create_user(username="rl_user2", password="pass")
        client.force_login(user)
        resp1 = client.get("/api/health/", REMOTE_ADDR="10.0.1.2")
        resp2 = client.get("/api/health/", REMOTE_ADDR="10.0.1.2")
        r1 = int(resp1["X-RateLimit-Remaining"])
        r2 = int(resp2["X-RateLimit-Remaining"])
        assert r2 < r1

    def test_429_includes_rate_limit_headers(self, client, django_user_model):
        """429 responses should include all rate limit headers."""
        user = django_user_model.objects.create_user(username="rl_user3", password="pass")
        client.force_login(user)
        # Exhaust limit
        for _ in range(10):
            client.get("/api/health/", REMOTE_ADDR="10.0.1.3")
        resp = client.get("/api/health/", REMOTE_ADDR="10.0.1.3")
        assert resp.status_code == 429
        assert "X-RateLimit-Limit" in resp
        assert "X-RateLimit-Remaining" in resp
        assert "X-RateLimit-Reset" in resp

    def test_429_remaining_is_zero(self, client, django_user_model):
        """When rate limited, remaining should be 0."""
        user = django_user_model.objects.create_user(username="rl_user4", password="pass")
        client.force_login(user)
        for _ in range(10):
            client.get("/api/health/", REMOTE_ADDR="10.0.1.4")
        resp = client.get("/api/health/", REMOTE_ADDR="10.0.1.4")
        assert resp.status_code == 429
        assert int(resp["X-RateLimit-Remaining"]) == 0

    def test_reset_header_is_unix_timestamp(self, client, django_user_model):
        """X-RateLimit-Reset should be a Unix timestamp in the future."""
        user = django_user_model.objects.create_user(username="rl_user5", password="pass")
        client.force_login(user)
        resp = client.get("/api/health/", REMOTE_ADDR="10.0.1.5")
        reset = int(resp["X-RateLimit-Reset"])
        now = int(time.time())
        # Reset should be in the future (within ~60s window)
        assert reset >= now
        assert reset <= now + 61

    def test_login_endpoint_uses_login_limit(self, client):
        """Login endpoint should report the login-specific rate limit."""
        resp = client.post(
            "/api/auth/login/",
            {"username": "x", "password": "y"},
            content_type="application/json",
            REMOTE_ADDR="10.0.1.6",
        )
        assert int(resp["X-RateLimit-Limit"]) == 3
