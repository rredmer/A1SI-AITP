"""Background ticker poller — fetches prices via ccxt and broadcasts to WebSocket clients."""

import asyncio
import contextlib
import logging

from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

_poller_task: asyncio.Task | None = None
_poller_lock = asyncio.Lock()

POLL_INTERVAL_SECONDS = 10
DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]


async def _poll_loop() -> None:
    """Continuously fetch tickers and broadcast to the market_tickers group."""
    channel_layer = get_channel_layer()

    while True:
        try:
            from market.services.exchange import ExchangeService

            service = ExchangeService()
            try:
                tickers = await service.fetch_tickers(DEFAULT_SYMBOLS)
                if tickers:
                    await channel_layer.group_send(
                        "market_tickers",
                        {
                            "type": "ticker_update",
                            "data": {"tickers": tickers},
                        },
                    )
            finally:
                await service.close()
        except Exception as e:
            logger.warning(f"Ticker poll failed: {e}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def start_poller() -> None:
    """Start the ticker poller if not already running. Idempotent."""
    global _poller_task

    async with _poller_lock:
        if _poller_task is not None and not _poller_task.done():
            return
        _poller_task = asyncio.create_task(_poll_loop())
        logger.info("Ticker poller started")


async def stop_poller() -> None:
    """Stop the ticker poller if running. Idempotent."""
    global _poller_task

    async with _poller_lock:
        if _poller_task is not None and not _poller_task.done():
            _poller_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await _poller_task
            _poller_task = None
            logger.info("Ticker poller stopped")
