"""Circuit breaker unit tests."""

import time

import pytest

from market.services.circuit_breaker import (
    CircuitBreaker,
    get_breaker,
    reset_breaker,
)


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker("test-exchange")
        state = cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert cb.can_execute() is True

    def test_trips_after_threshold(self):
        cb = CircuitBreaker("test-exchange", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        state = cb.get_state()
        assert state["state"] == "open"
        assert state["failure_count"] == 3
        assert cb.can_execute() is False

    def test_rejects_when_open(self):
        cb = CircuitBreaker("test-exchange", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute() is False

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker("test-exchange", failure_threshold=1, reset_timeout_seconds=0.1)
        cb.record_failure()
        assert cb.can_execute() is False
        time.sleep(0.15)
        assert cb.can_execute() is True
        state = cb.get_state()
        assert state["state"] == "half_open"

    def test_success_in_half_open_closes(self):
        cb = CircuitBreaker("test-exchange", failure_threshold=1, reset_timeout_seconds=0.1)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.can_execute() is True  # transitions to half_open
        cb.record_success()
        state = cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0

    def test_failure_in_half_open_reopens(self):
        cb = CircuitBreaker("test-exchange", failure_threshold=1, reset_timeout_seconds=0.1)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.can_execute() is True  # transitions to half_open
        cb.record_failure()
        state = cb.get_state()
        assert state["state"] == "open"

    def test_per_exchange_isolation(self):
        cb1 = CircuitBreaker("exchange-a", failure_threshold=2)
        cb2 = CircuitBreaker("exchange-b", failure_threshold=2)
        cb1.record_failure()
        cb1.record_failure()
        assert cb1.can_execute() is False
        assert cb2.can_execute() is True

    def test_manual_reset(self):
        cb = CircuitBreaker("test-exchange", failure_threshold=1)
        cb.record_failure()
        assert cb.can_execute() is False
        cb.reset()
        state = cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert cb.can_execute() is True


class TestCircuitBreakerRegistry:
    def test_get_breaker_creates_and_reuses(self):
        # Clear module-level registry for isolation
        from market.services import circuit_breaker

        orig = circuit_breaker._breakers.copy()
        circuit_breaker._breakers.clear()
        try:
            b1 = get_breaker("registry-test")
            b2 = get_breaker("registry-test")
            assert b1 is b2
        finally:
            circuit_breaker._breakers.clear()
            circuit_breaker._breakers.update(orig)

    def test_reset_breaker_nonexistent(self):
        assert reset_breaker("nonexistent-exchange-xyz") is False


@pytest.mark.django_db
class TestCircuitBreakerAPI:
    def test_get_breaker_status(self, client, django_user_model):
        user = django_user_model.objects.create_user(username="cb_user", password="pass")
        client.force_login(user)
        resp = client.get("/api/market/circuit-breaker/")
        assert resp.status_code == 200
        assert "breakers" in resp.json()

    def test_reset_breaker_via_api(self, client, django_user_model):
        user = django_user_model.objects.create_user(username="cb_user2", password="pass")
        client.force_login(user)
        # Register a breaker first
        get_breaker("api-test-exchange")
        resp = client.post(
            "/api/market/circuit-breaker/",
            data={"exchange_id": "api-test-exchange", "action": "reset"},
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_reset_breaker_not_found(self, client, django_user_model):
        user = django_user_model.objects.create_user(username="cb_user3", password="pass")
        client.force_login(user)
        resp = client.post(
            "/api/market/circuit-breaker/",
            data={"exchange_id": "no-such-exchange", "action": "reset"},
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_requires_auth(self, client):
        resp = client.get("/api/market/circuit-breaker/")
        assert resp.status_code in (401, 403)
