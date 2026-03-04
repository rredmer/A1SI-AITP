"""Tests for enhanced framework status with operational details."""

from unittest.mock import MagicMock, patch

import pytest

from core.views import (
    _get_ccxt_details,
    _get_framework_status,
    _get_freqtrade_details,
    _get_vectorbt_details,
)


class TestFrameworkStatusFields:
    """Verify all frameworks return status and details fields."""

    def test_all_frameworks_have_status_field(self):
        frameworks = _get_framework_status()
        for fw in frameworks:
            assert "status" in fw, f"{fw['name']} missing 'status' field"
            assert fw["status"] in ("running", "idle", "configured", "not_installed")

    def test_all_frameworks_have_details_field(self):
        frameworks = _get_framework_status()
        for fw in frameworks:
            assert "details" in fw, f"{fw['name']} missing 'details' field"
            # details can be None (for pure libraries) or a dict
            assert fw["details"] is None or isinstance(fw["details"], dict)


class TestFreqtradeDetails:
    """Freqtrade detail helper."""

    @patch("trading.views._get_paper_trading_services")
    def test_freqtrade_running_with_mock_instances(self, mock_services):
        mock_svc = MagicMock()
        mock_svc.get_status.return_value = {
            "running": True,
            "strategy": "CryptoInvestorV1",
            "started_at": "2026-03-04T10:00:00+00:00",
        }

        async def _open_trades():
            return [{"trade_id": 1}]

        mock_svc.get_open_trades = _open_trades
        mock_services.return_value = {"civ1": mock_svc}

        result = _get_freqtrade_details()
        assert result is not None
        assert result["_status"] == "running"
        assert result["instances_running"] == 1
        assert "CryptoInvestorV1" in result["strategies"]
        assert result["open_trades"] == 1

    @patch("trading.views._get_paper_trading_services", side_effect=Exception("unreachable"))
    def test_freqtrade_idle_when_unreachable(self, mock_services):
        result = _get_freqtrade_details()
        assert result is None


@pytest.mark.django_db
class TestVectorBTDetails:
    """VectorBT detail helper."""

    def test_vectorbt_details_with_screen_results(self):
        from analysis.models import BackgroundJob, ScreenResult

        job = BackgroundJob.objects.create(
            job_type="vbt_screen",
            status="completed",
        )
        ScreenResult.objects.create(
            job=job,
            symbol="BTC/USDT",
            timeframe="1d",
            strategy_name="sma_crossover",
        )
        ScreenResult.objects.create(
            job=job,
            symbol="ETH/USDT",
            timeframe="1d",
            strategy_name="rsi_oversold",
        )

        result = _get_vectorbt_details()
        assert result is not None
        assert result["screens_available"] == 2
        assert result["total_screens"] == 2
        assert result["last_screen_at"] is not None
        # Created just now so should be "running" (within 24h)
        assert result["_status"] == "running"

    def test_vectorbt_empty_returns_idle(self):
        result = _get_vectorbt_details()
        assert result is not None
        assert result["_status"] == "idle"
        assert result["screens_available"] == 0
        assert result["total_screens"] == 0


class TestCCXTDetails:
    """CCXT detail helper."""

    @patch("market.services.exchange.ExchangeService")
    def test_ccxt_details_exchange_connected(self, mock_exchange_service):
        mock_svc = MagicMock()
        mock_exchange = MagicMock()

        async def _get_exchange():
            return mock_exchange

        async def _load_markets():
            return {}

        async def _close():
            pass

        mock_svc._get_exchange = _get_exchange
        mock_exchange.load_markets = _load_markets
        mock_svc.close = _close
        mock_exchange_service.return_value = mock_svc

        result = _get_ccxt_details()
        assert result is not None
        assert result["_status"] == "running"
        assert result["exchange"] == "kraken"
        assert result["connected"] is True
        assert isinstance(result["latency_ms"], float)
