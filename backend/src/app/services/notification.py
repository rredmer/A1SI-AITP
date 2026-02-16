"""
Notification service — Telegram + webhook delivery for risk alerts.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger("notification_service")


class NotificationService:
    """Fire-and-forget notification delivery to Telegram and webhooks."""

    @staticmethod
    async def send_telegram(message: str) -> tuple[bool, str]:
        """Send a message via Telegram Bot API. Returns (delivered, error)."""
        token = settings.telegram_bot_token
        chat_id = settings.telegram_chat_id

        if not token or not chat_id:
            return False, "Telegram not configured"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                })
                if resp.status_code == 200:
                    return True, ""
                return False, f"Telegram API returned {resp.status_code}"
        except Exception as e:
            logger.error(f"Telegram delivery failed: {e}")
            return False, str(e)

    @staticmethod
    async def send_webhook(message: str, event_type: str) -> tuple[bool, str]:
        """POST to a generic webhook URL. Returns (delivered, error)."""
        webhook_url = settings.notification_webhook_url

        if not webhook_url:
            return False, "Webhook not configured"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json={
                    "event_type": event_type,
                    "message": message,
                })
                if resp.status_code < 300:
                    return True, ""
                return False, f"Webhook returned {resp.status_code}"
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return False, str(e)
