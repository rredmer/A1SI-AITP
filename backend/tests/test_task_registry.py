"""Tests for task registry — maps task_type strings to executor functions."""

from unittest.mock import MagicMock, patch

import pytest

from core.services.task_registry import TASK_REGISTRY


class TestTaskRegistryContents:
    def test_registry_has_expected_keys(self):
        expected_keys = [
            "data_refresh",
            "regime_detection",
            "order_sync",
            "data_quality",
            "news_fetch",
            "workflow",
            "risk_monitoring",
        ]
        for key in expected_keys:
            assert key in TASK_REGISTRY, f"Missing registry key: {key}"

    def test_all_executors_are_callable(self):
        for key, executor in TASK_REGISTRY.items():
            assert callable(executor), f"Executor for {key} is not callable"


class TestTaskRegistryOrderSync:
    @pytest.mark.django_db
    def test_order_sync_no_open_orders(self):
        executor = TASK_REGISTRY["order_sync"]
        progress_calls = []

        def progress_cb(pct, msg):
            progress_calls.append((pct, msg))

        result = executor({}, progress_cb)
        assert result["status"] == "completed"
        assert result["synced"] == 0


class TestTaskRegistryRegimeDetection:
    def test_regime_detection_handles_import_error(self):
        executor = TASK_REGISTRY["regime_detection"]

        with patch(
            "core.services.task_registry.RegimeService",
            side_effect=ImportError("no regime module"),
            create=True,
        ), patch(
            "market.services.regime.RegimeService",
            side_effect=ImportError("no regime module"),
        ):
            result = executor({}, lambda pct, msg: None)
            assert result["status"] == "error"
            assert "error" in result


class TestTaskRegistryRiskMonitoring:
    @pytest.mark.django_db
    def test_risk_monitoring_no_portfolios(self):
        executor = TASK_REGISTRY["risk_monitoring"]
        progress_calls = []

        def progress_cb(pct, msg):
            progress_calls.append((pct, msg))

        result = executor({}, progress_cb)
        assert result["status"] == "completed"
        assert result["message"] == "No portfolios"
