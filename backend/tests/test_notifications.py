"""
Tests for notification service and alert logging.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_telegram_not_configured(self):
        from app.services.notification import NotificationService

        with patch("app.services.notification.settings") as mock_settings:
            mock_settings.telegram_bot_token = ""
            mock_settings.telegram_chat_id = ""
            delivered, error = await NotificationService.send_telegram("test")
            assert delivered is False
            assert "not configured" in error.lower()

    @pytest.mark.asyncio
    async def test_webhook_not_configured(self):
        from app.services.notification import NotificationService

        with patch("app.services.notification.settings") as mock_settings:
            mock_settings.notification_webhook_url = ""
            delivered, error = await NotificationService.send_webhook("test", "test_event")
            assert delivered is False
            assert "not configured" in error.lower()

    @pytest.mark.asyncio
    async def test_telegram_delivery_success(self):
        from app.services.notification import NotificationService

        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        with (
            patch("app.services.notification.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_settings.telegram_bot_token = "fake-token"
            mock_settings.telegram_chat_id = "12345"
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            delivered, error = await NotificationService.send_telegram("test message")
            assert delivered is True
            assert error == ""

    @pytest.mark.asyncio
    async def test_webhook_delivery_success(self):
        from app.services.notification import NotificationService

        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        with (
            patch("app.services.notification.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_settings.notification_webhook_url = "https://hooks.example.com/test"
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            delivered, error = await NotificationService.send_webhook("test", "halt")
            assert delivered is True
            assert error == ""


class TestAlertLogging:
    @pytest.mark.asyncio
    async def test_halt_creates_alerts(self, client):
        resp = await client.post("/api/risk/1/halt", json={"reason": "alert test"})
        assert resp.status_code == 200

        alerts_resp = await client.get("/api/risk/1/alerts?limit=10")
        assert alerts_resp.status_code == 200
        alerts = alerts_resp.json()
        assert len(alerts) > 0
        halt_alerts = [a for a in alerts if a["event_type"] == "halt"]
        assert len(halt_alerts) > 0
        assert halt_alerts[0]["severity"] == "critical"
