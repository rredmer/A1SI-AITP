"""Tests for Telegram alerting — rate limiter, scanner, risk, daily report."""

import time
from unittest.mock import patch

import pytest

# ── Rate limiter ─────────────────────────────────────────────


class TestRateLimiter:
    def setup_method(self):
        """Clear the module-level rate limit state before each test."""
        from core.services.notification import _last_sent, _rate_limit_lock

        with _rate_limit_lock:
            _last_sent.clear()

    def test_is_rate_limited_allows_first_call(self):
        from core.services.notification import is_rate_limited

        assert is_rate_limited("test_key", cooldown=300) is False

    def test_is_rate_limited_blocks_second_call(self):
        from core.services.notification import is_rate_limited

        assert is_rate_limited("dup_key", cooldown=300) is False
        assert is_rate_limited("dup_key", cooldown=300) is True

    def test_is_rate_limited_different_keys_independent(self):
        from core.services.notification import is_rate_limited

        assert is_rate_limited("key_a", cooldown=300) is False
        assert is_rate_limited("key_b", cooldown=300) is False

    def test_is_rate_limited_allows_after_cooldown(self):
        from core.services.notification import _last_sent, _rate_limit_lock, is_rate_limited

        is_rate_limited("expire_key", cooldown=1)
        # Fake the last-sent time to the past
        with _rate_limit_lock:
            _last_sent["expire_key"] = time.monotonic() - 2
        assert is_rate_limited("expire_key", cooldown=1) is False


class TestSendTelegramRateLimited:
    def setup_method(self):
        from core.services.notification import _last_sent, _rate_limit_lock

        with _rate_limit_lock:
            _last_sent.clear()

    @patch("core.services.notification.NotificationService.send_telegram_sync")
    def test_sends_on_first_call(self, mock_send):
        from core.services.notification import send_telegram_rate_limited

        mock_send.return_value = (True, "")
        ok, err = send_telegram_rate_limited("hello", "key1")
        assert ok is True
        assert err == ""
        mock_send.assert_called_once_with("hello")

    @patch("core.services.notification.NotificationService.send_telegram_sync")
    def test_skips_on_rate_limit(self, mock_send):
        from core.services.notification import send_telegram_rate_limited

        mock_send.return_value = (True, "")
        send_telegram_rate_limited("first", "key2")
        ok, err = send_telegram_rate_limited("second", "key2")
        assert ok is False
        assert err == "rate_limited"
        assert mock_send.call_count == 1


# ── Scanner Telegram ─────────────────────────────────────────


class TestScannerTelegram:
    @patch("core.services.notification.send_telegram_rate_limited")
    def test_maybe_alert_uses_rate_limited_send(self, mock_send):
        from market.services.market_scanner import MarketScannerService

        mock_send.return_value = (True, "")
        scanner = MarketScannerService()
        opp = {
            "type": "breakout",
            "score": 85,
            "details": {"reason": "test reason"},
        }
        # Patch WS broadcast to avoid channel layer setup
        with patch("core.services.ws_broadcast.broadcast_opportunity"):
            scanner._maybe_alert("BTC/USDT", opp, asset_class="crypto")

        mock_send.assert_called_once()
        args = mock_send.call_args
        assert "BTC/USDT" in args[0][0]
        assert "[CRYPTO]" in args[0][0]
        assert args[0][1] == "opp:BTC/USDT:breakout"

    @patch("core.services.notification.send_telegram_rate_limited")
    def test_maybe_alert_includes_asset_class(self, mock_send):
        from market.services.market_scanner import MarketScannerService

        mock_send.return_value = (True, "")
        scanner = MarketScannerService()
        opp = {
            "type": "rsi_bounce",
            "score": 82,
            "details": {"reason": "RSI bounced"},
        }
        with patch("core.services.ws_broadcast.broadcast_opportunity"):
            scanner._maybe_alert("EUR/USD", opp, asset_class="forex")

        msg = mock_send.call_args[0][0]
        assert "[FOREX]" in msg


# ── Risk Telegram ────────────────────────────────────────────


@pytest.mark.django_db
class TestRiskTelegram:
    def test_send_notification_with_rate_key(self):
        from portfolio.models import Portfolio

        Portfolio.objects.create(id=99, name="Test", exchange_id="kraken")

        with (
            patch("core.services.notification.send_telegram_rate_limited") as mock_rl,
            patch("core.services.notification.NotificationService.send_telegram_sync") as mock_sync,
        ):
            mock_rl.return_value = (True, "")
            from risk.services.risk import RiskManagementService

            RiskManagementService.send_notification(
                portfolio_id=99,
                event_type="risk_warning",
                severity="warning",
                message="Drawdown at 80%",
                telegram_rate_key="risk_warning:99",
                telegram_cooldown=3600.0,
            )
            mock_rl.assert_called_once()
            mock_sync.assert_not_called()

    def test_send_notification_without_rate_key(self):
        from portfolio.models import Portfolio

        Portfolio.objects.create(id=100, name="Test", exchange_id="kraken")

        with (
            patch("core.services.notification.send_telegram_rate_limited") as mock_rl,
            patch("core.services.notification.NotificationService.send_telegram_sync") as mock_sync,
        ):
            mock_sync.return_value = (True, "")
            from risk.services.risk import RiskManagementService

            RiskManagementService.send_notification(
                portfolio_id=100,
                event_type="risk_auto_halt",
                severity="critical",
                message="Auto halt triggered",
            )
            mock_sync.assert_called_once()
            mock_rl.assert_not_called()


# ── Daily report Telegram ────────────────────────────────────


class TestDailyReportTelegram:
    @patch("core.services.notification.NotificationService.send_telegram_sync")
    def test_daily_report_sends_telegram(self, mock_send):
        mock_send.return_value = (True, "")
        mock_report = {
            "regime": {"dominant_regime": "ranging", "avg_confidence": 0.72},
            "strategy_performance": {
                "total_orders": 5,
                "win_rate": 60.0,
                "total_pnl": 123.45,
            },
            "system_status": {
                "days_paper_trading": 7,
                "min_days_required": 14,
            },
        }

        gen_path = "market.services.daily_report.DailyReportService.generate"
        with patch(gen_path, return_value=mock_report):
            from core.services.task_registry import _run_daily_report

            result = _run_daily_report({}, lambda p, m: None)

        assert result["status"] == "completed"
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "Daily Intelligence Report" in msg
        assert "ranging" in msg
        assert "60.0%" in msg
        assert "7/14" in msg
