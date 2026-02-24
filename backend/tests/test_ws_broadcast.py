"""Tests for WebSocket broadcast utilities (core/services/ws_broadcast.py)."""

from unittest.mock import MagicMock, patch


class TestBroadcastHelpers:
    """Test broadcast functions with mocked channel layer."""

    @patch("channels.layers.get_channel_layer")
    def test_broadcast_news_update(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_news_update

        broadcast_news_update("crypto", 5, {"avg_score": 0.3})

        mock_layer.group_send.assert_called_once()
        call_args = mock_layer.group_send.call_args
        assert call_args[0][0] == "system_events"
        event = call_args[0][1]
        assert event["type"] == "news_update"
        assert event["data"]["asset_class"] == "crypto"
        assert event["data"]["articles_fetched"] == 5

    @patch("channels.layers.get_channel_layer")
    def test_broadcast_sentiment_update(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_sentiment_update

        broadcast_sentiment_update("equity", 0.25, "positive", 10)

        mock_layer.group_send.assert_called_once()
        event = mock_layer.group_send.call_args[0][1]
        assert event["type"] == "sentiment_update"
        assert event["data"]["avg_score"] == 0.25

    @patch("channels.layers.get_channel_layer")
    def test_broadcast_scheduler_event(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_scheduler_event

        broadcast_scheduler_event(
            task_id="task1",
            task_name="Data Refresh",
            task_type="data_refresh",
            status="submitted",
            job_id="job123",
            message="Task submitted",
        )

        event = mock_layer.group_send.call_args[0][1]
        assert event["type"] == "scheduler_event"
        assert event["data"]["task_id"] == "task1"
        assert event["data"]["status"] == "submitted"

    @patch("channels.layers.get_channel_layer")
    def test_broadcast_regime_change(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_regime_change

        broadcast_regime_change("BTC/USDT", "ranging", "strong_trend_up", 0.85)

        event = mock_layer.group_send.call_args[0][1]
        assert event["type"] == "regime_change"
        assert event["data"]["symbol"] == "BTC/USDT"
        assert event["data"]["previous_regime"] == "ranging"
        assert event["data"]["new_regime"] == "strong_trend_up"
        assert event["data"]["confidence"] == 0.85

    @patch("channels.layers.get_channel_layer")
    def test_no_channel_layer_does_not_raise(self, mock_get_layer):
        mock_get_layer.return_value = None

        from core.services.ws_broadcast import broadcast_news_update

        # Should not raise
        broadcast_news_update("crypto", 0)

    @patch("channels.layers.get_channel_layer")
    def test_broadcast_failure_does_not_raise(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_layer.group_send.side_effect = RuntimeError("channel error")
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_regime_change

        # Should not raise despite error
        broadcast_regime_change("BTC/USDT", "ranging", "high_volatility", 0.5)

    @patch("channels.layers.get_channel_layer")
    def test_news_update_includes_timestamp(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_news_update

        broadcast_news_update("forex", 3)

        event = mock_layer.group_send.call_args[0][1]
        assert "timestamp" in event["data"]

    @patch("channels.layers.get_channel_layer")
    def test_news_update_default_sentiment_summary(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        from core.services.ws_broadcast import broadcast_news_update

        broadcast_news_update("crypto", 2)  # No sentiment_summary arg

        event = mock_layer.group_send.call_args[0][1]
        assert event["data"]["sentiment_summary"] == {}
