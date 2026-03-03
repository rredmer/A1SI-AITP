"""Tests for ForexPaperTradingService — entries, exits, status, API wiring."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from django.utils import timezone

from market.models import MarketOpportunity
from trading.models import Order, OrderStatus, TradingMode

_PRICE_PATH = (
    "trading.services.forex_paper_trading"
    ".ForexPaperTradingService._get_price"
)
_SUBMIT_PATH = (
    "trading.services.generic_paper_trading"
    ".GenericPaperTradingService.submit_order"
)


def _create_opportunity(symbol="EUR/USD", score=80, direction="bullish", acted_on=False):
    """Helper to create a forex MarketOpportunity."""
    return MarketOpportunity.objects.create(
        symbol=symbol,
        opportunity_type="breakout",
        score=score,
        asset_class="forex",
        timeframe="1h",
        details={"reason": "test", "direction": direction},
        expires_at=timezone.now() + timedelta(hours=24),
        acted_on=acted_on,
    )


def _create_filled_order(symbol="EUR/USD", side="buy", hours_ago=0):
    """Helper to create a filled forex paper order."""
    now = timezone.now()
    order = Order.objects.create(
        symbol=symbol,
        side=side,
        order_type="market",
        amount=1000.0,
        price=1.0800,
        mode=TradingMode.PAPER,
        asset_class="forex",
        exchange_id="yfinance",
        status=OrderStatus.FILLED,
        timestamp=now - timedelta(hours=hours_ago),
        filled_at=now - timedelta(hours=hours_ago),
        avg_fill_price=1.0800,
    )
    return order


@pytest.mark.django_db
class TestForexPaperTradingEntries:
    @patch(_PRICE_PATH, return_value=1.0800)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_entry_from_high_score_opportunity(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        _create_opportunity(score=80)

        service = ForexPaperTradingService()
        entries = service._check_entries()

        assert entries == 1
        assert Order.objects.filter(asset_class="forex", mode=TradingMode.PAPER).count() == 1
        assert MarketOpportunity.objects.get().acted_on is True

    @patch(_PRICE_PATH, return_value=1.0800)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_skip_low_score_opportunity(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        _create_opportunity(score=50)

        service = ForexPaperTradingService()
        entries = service._check_entries()

        assert entries == 0

    @patch(_PRICE_PATH, return_value=1.0800)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_respect_max_positions(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        # Create 3 existing filled orders for different symbols
        for pair in ["EUR/USD", "GBP/USD", "USD/JPY"]:
            _create_filled_order(symbol=pair, side="buy")

        # New opportunity
        _create_opportunity(symbol="AUD/USD", score=85)

        service = ForexPaperTradingService()
        entries = service._check_entries()

        assert entries == 0

    @patch(_PRICE_PATH, return_value=1.0800)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_no_duplicate_symbols(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        _create_filled_order(symbol="EUR/USD", side="buy")
        _create_opportunity(symbol="EUR/USD", score=90)

        service = ForexPaperTradingService()
        entries = service._check_entries()

        assert entries == 0

    @patch(_PRICE_PATH, return_value=1.0800)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_marks_acted_on(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        opp = _create_opportunity(score=75)

        service = ForexPaperTradingService()
        service._check_entries()

        opp.refresh_from_db()
        assert opp.acted_on is True


@pytest.mark.django_db
class TestForexPaperTradingExits:
    @patch(_PRICE_PATH, return_value=1.0850)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_exit_on_time_limit(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        _create_filled_order(symbol="EUR/USD", side="buy", hours_ago=25)

        service = ForexPaperTradingService()
        exits = service._check_exits()

        assert exits == 1

    @patch(_PRICE_PATH, return_value=1.0850)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_exit_on_score_decay(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        _create_filled_order(symbol="EUR/USD", side="buy", hours_ago=2)
        # Create a low-score opportunity
        _create_opportunity(symbol="EUR/USD", score=30, acted_on=True)

        service = ForexPaperTradingService()
        exits = service._check_exits()

        assert exits == 1

    @patch(_PRICE_PATH, return_value=1.0850)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_exit_on_opposing_signal(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        _create_filled_order(symbol="EUR/USD", side="buy", hours_ago=2)
        # Create a bearish opportunity (opposing direction)
        _create_opportunity(symbol="EUR/USD", score=75, direction="bearish", acted_on=True)

        service = ForexPaperTradingService()
        exits = service._check_exits()

        assert exits == 1

    @patch(_PRICE_PATH, return_value=1.0850)
    def test_no_exit_when_fresh_and_strong(self, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        _create_filled_order(symbol="EUR/USD", side="buy", hours_ago=2)
        # Strong bullish signal — no exit
        _create_opportunity(symbol="EUR/USD", score=80, direction="bullish", acted_on=True)

        service = ForexPaperTradingService()
        exits = service._check_exits()

        assert exits == 0


@pytest.mark.django_db
class TestForexPaperTradingStatus:
    def test_get_status_shape(self):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        service = ForexPaperTradingService()
        status = service.get_status()

        assert status["running"] is True
        assert status["strategy"] == "ForexSignals"
        assert status["asset_class"] == "forex"
        assert status["engine"] == "signal_based"
        assert "open_positions" in status
        assert "total_trades" in status

    def test_api_includes_forex_instance(self, authenticated_client):
        resp = authenticated_client.get("/api/paper-trading/status/")
        assert resp.status_code == 200
        data = resp.json()
        instances = [s["instance"] for s in data]
        assert "forex_signals" in instances


@pytest.mark.django_db
class TestForexRunCycle:
    @patch(_PRICE_PATH, return_value=1.0800)
    @patch(_SUBMIT_PATH, new_callable=AsyncMock)
    def test_run_cycle_returns_summary(self, mock_submit, mock_price):
        from trading.services.forex_paper_trading import ForexPaperTradingService

        mock_submit.return_value = None
        _create_opportunity(score=80)

        service = ForexPaperTradingService()
        result = service.run_cycle()

        assert result["status"] == "completed"
        assert "entries_created" in result
        assert "exits_created" in result


class TestForexTaskRegistration:
    def test_forex_paper_trading_in_registry(self):
        from core.services.task_registry import TASK_REGISTRY

        assert "forex_paper_trading" in TASK_REGISTRY
        assert callable(TASK_REGISTRY["forex_paper_trading"])
