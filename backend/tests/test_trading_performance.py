"""Trading performance analytics tests."""

from datetime import datetime, timezone

import pytest

from trading.models import Order, OrderStatus
from trading.services.performance import TradingPerformanceService


def _create_order(symbol="BTC/USDT", side="buy", amount=1.0, price=100.0,
                  mode="paper", asset_class="crypto", portfolio_id=1,
                  status=OrderStatus.FILLED, **kwargs):
    return Order.objects.create(
        exchange_id="binance",
        symbol=symbol,
        side=side,
        order_type="market",
        amount=amount,
        price=price,
        avg_fill_price=price,
        filled=amount,
        status=status,
        mode=mode,
        asset_class=asset_class,
        portfolio_id=portfolio_id,
        timestamp=kwargs.get("timestamp", datetime.now(timezone.utc)),
    )


@pytest.mark.django_db
class TestTradingPerformanceService:
    def test_empty_returns_zeros(self):
        result = TradingPerformanceService.get_summary(portfolio_id=1)
        assert result["total_trades"] == 0
        assert result["win_rate"] == 0.0
        assert result["total_pnl"] == 0.0

    def test_single_filled_order(self):
        _create_order(side="buy", amount=1.0, price=100.0)
        result = TradingPerformanceService.get_summary(portfolio_id=1)
        assert result["total_trades"] == 1

    def test_multiple_symbols_pnl(self):
        # BTC: buy 1 @ 100, sell 1 @ 150 → +50
        _create_order(symbol="BTC/USDT", side="buy", amount=1.0, price=100.0)
        _create_order(symbol="BTC/USDT", side="sell", amount=1.0, price=150.0)
        # ETH: buy 2 @ 50, sell 2 @ 40 → -20
        _create_order(symbol="ETH/USDT", side="buy", amount=2.0, price=50.0)
        _create_order(symbol="ETH/USDT", side="sell", amount=2.0, price=40.0)

        result = TradingPerformanceService.get_summary(portfolio_id=1)
        assert result["total_trades"] == 4
        assert result["win_count"] == 1
        assert result["loss_count"] == 1
        assert result["total_pnl"] == 30.0  # 50 - 20
        assert result["best_trade"] == 50.0
        assert result["worst_trade"] == -20.0

    def test_mode_filter(self):
        _create_order(mode="paper")
        _create_order(mode="live")
        paper = TradingPerformanceService.get_summary(portfolio_id=1, mode="paper")
        live = TradingPerformanceService.get_summary(portfolio_id=1, mode="live")
        assert paper["total_trades"] == 1
        assert live["total_trades"] == 1

    def test_asset_class_filter(self):
        _create_order(asset_class="crypto")
        _create_order(asset_class="equity")
        crypto = TradingPerformanceService.get_summary(portfolio_id=1, asset_class="crypto")
        equity = TradingPerformanceService.get_summary(portfolio_id=1, asset_class="equity")
        assert crypto["total_trades"] == 1
        assert equity["total_trades"] == 1

    def test_date_range_filter(self):
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 2, 1, tzinfo=timezone.utc)
        _create_order(timestamp=t1)
        _create_order(timestamp=t2)
        result = TradingPerformanceService.get_summary(
            portfolio_id=1,
            date_from="2026-01-15T00:00:00Z",
        )
        assert result["total_trades"] == 1

    def test_by_symbol_grouping(self):
        _create_order(symbol="BTC/USDT", side="buy", amount=1.0, price=100.0)
        _create_order(symbol="BTC/USDT", side="sell", amount=1.0, price=120.0)
        _create_order(symbol="ETH/USDT", side="buy", amount=1.0, price=50.0)

        results = TradingPerformanceService.get_by_symbol(portfolio_id=1)
        assert len(results) == 2
        symbols = {r["symbol"] for r in results}
        assert symbols == {"BTC/USDT", "ETH/USDT"}


@pytest.mark.django_db
class TestTradingPerformanceAPI:
    def test_summary_endpoint(self, client, django_user_model):
        user = django_user_model.objects.create_user(username="perf_user", password="pass")
        client.force_login(user)
        resp = client.get("/api/trading/performance/summary/")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_trades" in data
        assert "win_rate" in data

    def test_by_symbol_endpoint(self, client, django_user_model):
        user = django_user_model.objects.create_user(username="perf_user2", password="pass")
        client.force_login(user)
        resp = client.get("/api/trading/performance/by-symbol/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_requires_auth(self, client):
        resp = client.get("/api/trading/performance/summary/")
        assert resp.status_code in (401, 403)
