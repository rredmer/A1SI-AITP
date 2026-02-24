"""WebSocket consumer tests."""

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from market.consumers import MarketTickerConsumer, SystemEventsConsumer

User = get_user_model()


@database_sync_to_async
def _create_user():
    return User.objects.create_user(username="wsuser", password="testpass123!")


def _make_communicator(consumer_class, path, user=None):
    """Build a WebsocketCommunicator with an optional authenticated user."""
    communicator = WebsocketCommunicator(consumer_class.as_asgi(), path)
    if user:
        communicator.scope["user"] = user
    return communicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMarketTickerConsumer:
    async def test_anonymous_rejected(self):
        from django.contrib.auth.models import AnonymousUser

        comm = _make_communicator(MarketTickerConsumer, "/ws/market/tickers/", user=AnonymousUser())
        connected, code = await comm.connect()
        assert not connected or code == 4001
        await comm.disconnect()

    async def test_authenticated_accepted(self):
        user = await _create_user()
        comm = _make_communicator(MarketTickerConsumer, "/ws/market/tickers/", user=user)
        connected, _ = await comm.connect()
        assert connected
        await comm.disconnect()

    async def test_ticker_update_relayed(self):
        from channels.layers import get_channel_layer

        user = await _create_user()
        comm = _make_communicator(MarketTickerConsumer, "/ws/market/tickers/", user=user)
        connected, _ = await comm.connect()
        assert connected

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "market_tickers",
            {
                "type": "ticker_update",
                "data": {"tickers": [{"symbol": "BTC/USDT", "price": 50000}]},
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["tickers"][0]["symbol"] == "BTC/USDT"
        await comm.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestSystemEventsConsumer:
    async def test_anonymous_rejected(self):
        from django.contrib.auth.models import AnonymousUser

        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=AnonymousUser())
        connected, code = await comm.connect()
        assert not connected or code == 4001
        await comm.disconnect()

    async def test_order_update_relayed(self):
        user = await _create_user()
        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=user)
        connected, _ = await comm.connect()
        assert connected

        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "system_events",
            {
                "type": "order_update",
                "data": {"order_id": 1, "status": "filled"},
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "order_update"
        assert response["data"]["order_id"] == 1
        await comm.disconnect()

    async def test_halt_status_relayed(self):
        user = await _create_user()
        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=user)
        connected, _ = await comm.connect()
        assert connected

        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "system_events",
            {
                "type": "halt_status",
                "data": {"is_halted": True, "halt_reason": "emergency"},
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "halt_status"
        assert response["data"]["is_halted"] is True
        await comm.disconnect()

    async def test_news_update_relayed(self):
        user = await _create_user()
        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=user)
        connected, _ = await comm.connect()
        assert connected

        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "system_events",
            {
                "type": "news_update",
                "data": {"asset_class": "crypto", "articles_fetched": 5},
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "news_update"
        assert response["data"]["articles_fetched"] == 5
        await comm.disconnect()

    async def test_sentiment_update_relayed(self):
        user = await _create_user()
        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=user)
        connected, _ = await comm.connect()
        assert connected

        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "system_events",
            {
                "type": "sentiment_update",
                "data": {"asset_class": "crypto", "avg_score": 0.3, "overall_label": "positive"},
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "sentiment_update"
        assert response["data"]["avg_score"] == 0.3
        await comm.disconnect()

    async def test_scheduler_event_relayed(self):
        user = await _create_user()
        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=user)
        connected, _ = await comm.connect()
        assert connected

        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "system_events",
            {
                "type": "scheduler_event",
                "data": {"task_id": "t1", "task_name": "Test", "status": "submitted"},
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "scheduler_event"
        assert response["data"]["status"] == "submitted"
        await comm.disconnect()

    async def test_regime_change_relayed(self):
        user = await _create_user()
        comm = _make_communicator(SystemEventsConsumer, "/ws/system/", user=user)
        connected, _ = await comm.connect()
        assert connected

        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "system_events",
            {
                "type": "regime_change",
                "data": {
                    "symbol": "BTC/USDT",
                    "previous_regime": "ranging",
                    "new_regime": "strong_trend_up",
                    "confidence": 0.85,
                },
            },
        )

        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "regime_change"
        assert response["data"]["symbol"] == "BTC/USDT"
        assert response["data"]["new_regime"] == "strong_trend_up"
        await comm.disconnect()
