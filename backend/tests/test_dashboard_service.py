"""Tests for DashboardService — KPI aggregation service."""

from unittest.mock import patch

import pytest

from core.services.dashboard import DashboardService


@pytest.mark.django_db
class TestDashboardServiceGetKpis:
    def test_returns_all_sections_empty_db(self):
        kpis = DashboardService.get_kpis()
        assert "portfolio" in kpis
        assert "trading" in kpis
        assert "risk" in kpis
        assert "platform" in kpis
        assert "generated_at" in kpis

    def test_empty_portfolio_defaults(self):
        kpis = DashboardService.get_kpis()
        assert kpis["portfolio"]["count"] == 0
        assert kpis["portfolio"]["total_value"] == 0.0
        assert kpis["portfolio"]["unrealized_pnl"] == 0.0

    def test_empty_trading_defaults(self):
        kpis = DashboardService.get_kpis()
        assert kpis["trading"]["total_trades"] == 0
        assert kpis["trading"]["open_orders"] == 0

    def test_empty_risk_defaults(self):
        kpis = DashboardService.get_kpis()
        assert kpis["risk"]["equity"] == 0.0
        assert kpis["risk"]["is_halted"] is False

    def test_asset_class_filter_passed_through(self):
        """asset_class param doesn't crash even with no data."""
        kpis = DashboardService.get_kpis(asset_class="crypto")
        assert kpis["portfolio"]["count"] == 0
        assert kpis["trading"]["total_trades"] == 0


@pytest.mark.django_db
class TestDashboardServicePartialFailures:
    def test_portfolio_failure_returns_defaults(self):
        with patch(
            "core.services.dashboard.DashboardService._get_portfolio_kpis",
            side_effect=Exception("db down"),
        ):
            # The top-level get_kpis calls _get_portfolio_kpis directly,
            # but _get_portfolio_kpis has its own try/except, so we need
            # to patch deeper.
            pass

        # Test via the internal method's own exception handling
        with patch(
            "portfolio.services.analytics.PortfolioAnalyticsService.get_portfolio_summary",
            side_effect=Exception("analytics exploded"),
        ):
            from portfolio.models import Portfolio

            Portfolio.objects.create(name="Test", exchange_id="binance")
            kpis = DashboardService.get_kpis()
            assert kpis["portfolio"]["count"] == 0
            assert kpis["portfolio"]["total_value"] == 0.0
            # Other sections still work
            assert "trading" in kpis
            assert "risk" in kpis

    def test_trading_failure_returns_defaults(self):
        with patch(
            "trading.services.performance.TradingPerformanceService.get_summary",
            side_effect=Exception("performance down"),
        ):
            from portfolio.models import Portfolio

            Portfolio.objects.create(name="Test2", exchange_id="binance")
            kpis = DashboardService.get_kpis()
            assert kpis["trading"]["total_trades"] == 0
            assert kpis["trading"]["win_rate"] == 0.0
            assert "portfolio" in kpis

    def test_risk_failure_returns_defaults(self):
        with patch(
            "risk.services.risk.RiskManagementService.get_status",
            side_effect=Exception("risk service down"),
        ):
            from portfolio.models import Portfolio

            Portfolio.objects.create(name="Test3", exchange_id="binance")
            kpis = DashboardService.get_kpis()
            assert kpis["risk"]["equity"] == 0.0
            assert kpis["risk"]["is_halted"] is False

    def test_platform_failure_returns_defaults(self):
        with patch(
            "core.services.dashboard.get_processed_dir",
            side_effect=Exception("filesystem error"),
        ):
            kpis = DashboardService.get_kpis()
            assert kpis["platform"]["data_files"] == 0
            assert kpis["platform"]["active_jobs"] == 0
