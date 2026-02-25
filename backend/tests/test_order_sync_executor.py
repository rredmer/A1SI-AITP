"""Tests for the _run_order_sync task registry executor — P12-2."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from django.utils import timezone

from core.services.task_registry import TASK_REGISTRY
from trading.models import Order, OrderStatus, TradingMode


def _progress_noop(pct: float, msg: str) -> None:
    pass


def _create_order(
    *,
    status: str = OrderStatus.SUBMITTED,
    mode: str = TradingMode.LIVE,
    created_at: timezone.datetime | None = None,
    exchange_order_id: str = "exch-123",
) -> Order:
    order = Order.objects.create(
        exchange_id="binance",
        exchange_order_id=exchange_order_id,
        symbol="BTC/USDT",
        side="buy",
        order_type="limit",
        amount=1.0,
        price=50000.0,
        status=status,
        mode=mode,
        portfolio_id=1,
        timestamp=timezone.now(),
    )
    if created_at is not None:
        Order.objects.filter(pk=order.pk).update(created_at=created_at)
        order.refresh_from_db()
    return order


@pytest.mark.django_db
class TestOrderSyncImportPath:
    def test_order_sync_uses_correct_import(self):
        """Verify _run_order_sync imports from trading.services.live_trading (not live)."""
        executor = TASK_REGISTRY["order_sync"]
        # With no orders, it should complete without import errors
        result = executor({}, _progress_noop)
        assert result["status"] == "completed"
        assert result["total"] == 0


@pytest.mark.django_db
class TestOrderSyncLiveOrders:
    def test_syncs_live_orders(self):
        """Verify sync_order is called for each live pending order."""
        _create_order(status=OrderStatus.SUBMITTED)
        _create_order(status=OrderStatus.OPEN)

        mock_sync = AsyncMock()
        with patch(
            "trading.services.live_trading.LiveTradingService.sync_order",
            mock_sync,
        ):
            result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        assert result["status"] == "completed"
        assert result["total"] == 2
        assert result["synced"] == 2
        assert mock_sync.call_count == 2

    def test_skips_paper_orders(self):
        """Paper orders should not be synced."""
        _create_order(mode=TradingMode.PAPER)
        _create_order(mode=TradingMode.LIVE, status=OrderStatus.OPEN)

        mock_sync = AsyncMock()
        with patch(
            "trading.services.live_trading.LiveTradingService.sync_order",
            mock_sync,
        ):
            result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        assert result["total"] == 1
        assert result["synced"] == 1
        assert mock_sync.call_count == 1


@pytest.mark.django_db
class TestOrderSyncTimeout:
    def test_times_out_stuck_submitted_orders(self):
        """SUBMITTED orders older than timeout hours should be marked ERROR."""
        old_time = timezone.now() - timedelta(hours=25)
        order = _create_order(status=OrderStatus.SUBMITTED, created_at=old_time)

        result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        order.refresh_from_db()
        assert order.status == OrderStatus.ERROR
        assert "timeout" in order.error_message.lower()
        assert result["timed_out"] == 1
        assert result["synced"] == 0

    def test_does_not_timeout_recent_submitted(self):
        """Recent SUBMITTED orders should be synced normally."""
        _create_order(status=OrderStatus.SUBMITTED)  # just created

        mock_sync = AsyncMock()
        with patch(
            "trading.services.live_trading.LiveTradingService.sync_order",
            mock_sync,
        ):
            result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        assert result["timed_out"] == 0
        assert result["synced"] == 1

    def test_timeout_setting_is_configurable(self, settings):
        """ORDER_SYNC_TIMEOUT_HOURS setting should control timeout cutoff."""
        settings.ORDER_SYNC_TIMEOUT_HOURS = 1
        old_time = timezone.now() - timedelta(hours=2)
        order = _create_order(status=OrderStatus.SUBMITTED, created_at=old_time)

        result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        order.refresh_from_db()
        assert order.status == OrderStatus.ERROR
        assert result["timed_out"] == 1


@pytest.mark.django_db
class TestOrderSyncErrorHandling:
    def test_handles_exchange_error_gracefully(self):
        """Exchange errors should be counted, not crash the whole sync."""
        _create_order(status=OrderStatus.OPEN)

        mock_sync = AsyncMock(side_effect=Exception("Exchange unreachable"))
        with patch(
            "trading.services.live_trading.LiveTradingService.sync_order",
            mock_sync,
        ):
            result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        assert result["status"] == "completed"
        assert result["errors"] == 1
        assert result["synced"] == 0

    def test_progress_callback_is_called(self):
        """Progress callback should be invoked during sync."""
        _create_order(status=OrderStatus.OPEN)

        calls: list[tuple[float, str]] = []

        def track_progress(pct: float, msg: str) -> None:
            calls.append((pct, msg))

        mock_sync = AsyncMock()
        with patch(
            "trading.services.live_trading.LiveTradingService.sync_order",
            mock_sync,
        ):
            TASK_REGISTRY["order_sync"]({}, track_progress)

        assert len(calls) >= 2  # initial + at least one per-order
        assert calls[0][0] == 0.0  # initial progress

    def test_empty_queue_returns_zeros(self):
        """Empty order queue should return all zeros."""
        result = TASK_REGISTRY["order_sync"]({}, _progress_noop)

        assert result["status"] == "completed"
        assert result["total"] == 0
        assert result["synced"] == 0
        assert result["timed_out"] == 0
        assert result["errors"] == 0
