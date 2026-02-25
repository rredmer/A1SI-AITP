"""Tests for NotificationService — Telegram + webhook delivery."""

from unittest.mock import AsyncMock, patch

import pytest

from core.services.notification import NotificationService


class TestSendTelegram:
    @pytest.mark.asyncio
    async def test_not_configured(self):
        with patch("core.services.notification.settings") as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = ""
            mock_settings.TELEGRAM_CHAT_ID = ""
            delivered, error = await NotificationService.send_telegram("test message")
            assert delivered is False
            assert "not configured" in error.lower()

    @pytest.mark.asyncio
    async def test_success(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        with (
            patch("core.services.notification.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_settings.TELEGRAM_BOT_TOKEN = "fake-token"
            mock_settings.TELEGRAM_CHAT_ID = "12345"
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            delivered, error = await NotificationService.send_telegram("hello")
            assert delivered is True
            assert error == ""

    @pytest.mark.asyncio
    async def test_api_error(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 400

        with (
            patch("core.services.notification.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_settings.TELEGRAM_BOT_TOKEN = "fake-token"
            mock_settings.TELEGRAM_CHAT_ID = "12345"
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            delivered, error = await NotificationService.send_telegram("hello")
            assert delivered is False
            assert "400" in error


class TestSendWebhook:
    @pytest.mark.asyncio
    async def test_not_configured(self):
        with patch("core.services.notification.settings") as mock_settings:
            mock_settings.NOTIFICATION_WEBHOOK_URL = ""
            delivered, error = await NotificationService.send_webhook("test", "halt")
            assert delivered is False
            assert "not configured" in error.lower()

    @pytest.mark.asyncio
    async def test_success(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        with (
            patch("core.services.notification.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_settings.NOTIFICATION_WEBHOOK_URL = "https://hooks.example.com/test"
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            delivered, error = await NotificationService.send_webhook("halt msg", "halt")
            assert delivered is True
            assert error == ""


class TestSendTelegramSync:
    def test_not_configured(self):
        with patch("core.services.notification.settings") as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = ""
            mock_settings.TELEGRAM_CHAT_ID = ""
            delivered, error = NotificationService.send_telegram_sync("test")
            assert delivered is False
            assert "not configured" in error.lower()

    def test_network_exception_handled(self):
        with (
            patch("core.services.notification.settings") as mock_settings,
            patch("httpx.Client") as mock_client_cls,
        ):
            mock_settings.TELEGRAM_BOT_TOKEN = "fake-token"
            mock_settings.TELEGRAM_CHAT_ID = "12345"
            mock_client_cls.return_value.__enter__ = lambda s: s
            mock_client_cls.return_value.__exit__ = lambda s, *a: False
            mock_client_cls.return_value.post.side_effect = Exception("Connection refused")

            delivered, error = NotificationService.send_telegram_sync("test")
            assert delivered is False
            assert "Connection refused" in error
