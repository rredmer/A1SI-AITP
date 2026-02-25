"""Tests for the background ticker poller service."""

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_poller():
    """Reset module-level poller state between tests."""
    import market.services.ticker_poller as mod

    mod._poller_task = None
    yield
    # Clean up any running tasks
    if mod._poller_task and not mod._poller_task.done():
        mod._poller_task.cancel()
    mod._poller_task = None


@pytest.mark.asyncio
async def test_start_poller_creates_task():
    """start_poller() should create an asyncio task."""
    import market.services.ticker_poller as mod

    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()

    mock_service = MagicMock()
    mock_service.fetch_tickers = AsyncMock(return_value={"BTC/USDT": {"price": 50000}})
    mock_service.close = AsyncMock()

    with patch.object(mod, "get_channel_layer", return_value=mock_layer), \
         patch("market.services.exchange.ExchangeService", return_value=mock_service):
        await mod.start_poller()
        assert mod._poller_task is not None
        assert not mod._poller_task.done()
        # Clean up
        await mod.stop_poller()


@pytest.mark.asyncio
async def test_start_poller_is_idempotent():
    """Calling start_poller() twice should reuse the existing task."""
    import market.services.ticker_poller as mod

    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()

    mock_service = MagicMock()
    mock_service.fetch_tickers = AsyncMock(return_value={})
    mock_service.close = AsyncMock()

    with patch.object(mod, "get_channel_layer", return_value=mock_layer), \
         patch("market.services.exchange.ExchangeService", return_value=mock_service):
        await mod.start_poller()
        first_task = mod._poller_task
        await mod.start_poller()
        assert mod._poller_task is first_task
        await mod.stop_poller()


@pytest.mark.asyncio
async def test_stop_poller_cancels_task():
    """stop_poller() should cancel the running task."""
    import market.services.ticker_poller as mod

    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()

    mock_service = MagicMock()
    mock_service.fetch_tickers = AsyncMock(return_value={})
    mock_service.close = AsyncMock()

    with patch.object(mod, "get_channel_layer", return_value=mock_layer), \
         patch("market.services.exchange.ExchangeService", return_value=mock_service):
        await mod.start_poller()
        assert mod._poller_task is not None
        await mod.stop_poller()
        assert mod._poller_task is None


@pytest.mark.asyncio
async def test_poll_loop_broadcasts_tickers():
    """_poll_loop should call group_send with ticker data."""
    import market.services.ticker_poller as mod

    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()

    mock_service = MagicMock()
    mock_service.fetch_tickers = AsyncMock(return_value={"BTC/USDT": {"price": 50000}})
    mock_service.close = AsyncMock()

    with patch.object(mod, "get_channel_layer", return_value=mock_layer), \
         patch("market.services.exchange.ExchangeService", return_value=mock_service):
        # Run the poll loop but cancel after first iteration
        task = asyncio.create_task(mod._poll_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        mock_layer.group_send.assert_called()
        call_args = mock_layer.group_send.call_args
        assert call_args[0][0] == "market_tickers"
        assert call_args[0][1]["type"] == "ticker_update"


@pytest.mark.asyncio
async def test_poll_loop_handles_fetch_error():
    """_poll_loop should continue after a fetch error."""
    import market.services.ticker_poller as mod

    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()

    call_count = 0

    async def failing_fetch(*args):
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Exchange down")

    mock_service = MagicMock()
    mock_service.fetch_tickers = failing_fetch
    mock_service.close = AsyncMock()

    with patch.object(mod, "get_channel_layer", return_value=mock_layer), \
         patch("market.services.exchange.ExchangeService", return_value=mock_service), \
         patch.object(mod, "POLL_INTERVAL_SECONDS", 0.01):
        task = asyncio.create_task(mod._poll_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have attempted multiple polls despite errors
        assert call_count >= 2
        # group_send should NOT have been called (no successful fetches)
        mock_layer.group_send.assert_not_called()
