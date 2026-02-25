"""Tests for order_sync — background order sync loop for live orders."""

from unittest.mock import AsyncMock, patch

import pytest

from trading.services.order_sync import start_order_sync, stop_order_sync


class TestStartOrderSync:
    @pytest.mark.asyncio
    async def test_start_creates_task(self):
        # Reset module state
        import trading.services.order_sync as mod
        mod._sync_task = None

        with patch.object(mod, "_sync_loop", new_callable=AsyncMock):
            await start_order_sync()
            assert mod._sync_task is not None
            # Clean up
            await stop_order_sync()

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self):
        import trading.services.order_sync as mod
        mod._sync_task = None

        with patch.object(mod, "_sync_loop", new_callable=AsyncMock):
            await start_order_sync()
            first_task = mod._sync_task
            await start_order_sync()
            # Should be the same task (not recreated)
            assert mod._sync_task is first_task
            await stop_order_sync()


class TestStopOrderSync:
    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        import trading.services.order_sync as mod
        mod._sync_task = None

        with patch.object(mod, "_sync_loop", new_callable=AsyncMock):
            await start_order_sync()
            assert mod._sync_task is not None
            await stop_order_sync()
            assert mod._sync_task is None

    @pytest.mark.asyncio
    async def test_stop_noop_when_not_running(self):
        import trading.services.order_sync as mod
        mod._sync_task = None
        # Should not raise
        await stop_order_sync()
        assert mod._sync_task is None
