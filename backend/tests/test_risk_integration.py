"""Integration tests for RiskManagementService — periodic checks, halt/resume, notifications."""

from unittest.mock import patch

import pytest

from risk.models import AlertLog, RiskLimitChange, RiskLimits, RiskMetricHistory, RiskState
from risk.services.risk import RiskManagementService


@pytest.fixture
def portfolio_state(db):
    """Create a portfolio with risk state and limits for testing."""
    state = RiskState.objects.create(
        portfolio_id=1,
        total_equity=10000.0,
        peak_equity=10000.0,
        daily_start_equity=10000.0,
    )
    limits = RiskLimits.objects.create(
        portfolio_id=1,
        max_portfolio_drawdown=0.15,
        max_daily_loss=0.05,
    )
    return state, limits


# ── Periodic Risk Check ─────────────────────────────────────


@pytest.mark.django_db
class TestPeriodicRiskCheck:
    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_ok_when_within_limits(self, mock_telegram, portfolio_state):
        """Periodic check returns 'ok' when drawdown is within limits."""
        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "ok"
        assert result["portfolio_id"] == 1

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_auto_halts_on_drawdown_breach(self, mock_telegram, portfolio_state):
        """When drawdown exceeds limit, trading is auto-halted."""
        state, limits = portfolio_state
        # Set equity to trigger drawdown > 15%
        state.total_equity = 8000.0  # 20% drawdown from peak of 10000
        state.save()

        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "auto_halted"
        assert "Drawdown" in result["reason"]

        # Verify state is halted
        state.refresh_from_db()
        assert state.is_halted is True

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_auto_halts_on_daily_loss_breach(self, mock_telegram, portfolio_state):
        """When daily loss exceeds limit, trading is auto-halted."""
        state, limits = portfolio_state
        # Set daily_pnl to trigger daily loss > 5% of equity
        state.daily_pnl = -600.0  # 6% of 10000
        state.save()

        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "auto_halted"
        assert "Daily loss" in result["reason"]

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_warning_at_80_percent(self, mock_telegram, portfolio_state):
        """At 80% of drawdown limit, a warning is issued."""
        state, limits = portfolio_state
        # 80% of 15% = 12% drawdown
        state.total_equity = 8750.0  # 12.5% drawdown (> 80% of 15%)
        state.save()

        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "warning"
        assert "warning" in result.get("warning", "").lower()

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_skips_already_halted(self, mock_telegram, portfolio_state):
        """If already halted, periodic check returns 'halted' without further checks."""
        state, _ = portfolio_state
        state.is_halted = True
        state.halt_reason = "manual halt"
        state.save()

        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "halted"

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_records_metrics(self, mock_telegram, portfolio_state):
        """Periodic check should record a metric history entry."""
        initial_count = RiskMetricHistory.objects.count()
        RiskManagementService.periodic_risk_check(1)
        assert RiskMetricHistory.objects.count() == initial_count + 1


# ── Halt / Resume ───────────────────────────────────────────


@pytest.mark.django_db
class TestHaltResume:
    def test_halt_creates_alert_log(self, portfolio_state):
        """halt_trading should create a kill_switch_halt AlertLog entry."""
        initial = AlertLog.objects.filter(event_type="kill_switch_halt").count()
        RiskManagementService.halt_trading(1, "test halt reason")
        assert AlertLog.objects.filter(event_type="kill_switch_halt").count() == initial + 1

    def test_resume_clears_halt_state(self, portfolio_state):
        """resume_trading should clear is_halted and halt_reason."""
        state, _ = portfolio_state
        state.is_halted = True
        state.halt_reason = "was halted"
        state.save()

        result = RiskManagementService.resume_trading(1)
        assert result["is_halted"] is False

        state.refresh_from_db()
        assert state.is_halted is False
        assert state.halt_reason == ""


# ── Update Limits ───────────────────────────────────────────


@pytest.mark.django_db
class TestUpdateLimits:
    def test_update_limits_creates_change_log(self, portfolio_state):
        """Changing a limit should create a RiskLimitChange record."""
        initial = RiskLimitChange.objects.count()
        RiskManagementService.update_limits(
            portfolio_id=1,
            updates={"max_portfolio_drawdown": 0.20},
            changed_by="admin",
            reason="Increased risk tolerance",
        )
        assert RiskLimitChange.objects.count() == initial + 1
        change = RiskLimitChange.objects.latest("changed_at")
        assert change.field_name == "max_portfolio_drawdown"
        assert change.old_value == "0.15"
        assert change.new_value == "0.2"
        assert change.changed_by == "admin"

    def test_update_limits_no_change_no_log(self, portfolio_state):
        """Setting a limit to its current value should not create a change record."""
        initial = RiskLimitChange.objects.count()
        RiskManagementService.update_limits(
            portfolio_id=1,
            updates={"max_portfolio_drawdown": 0.15},  # same as default
        )
        assert RiskLimitChange.objects.count() == initial

    def test_update_limits_returns_updated_object(self, portfolio_state):
        """update_limits should return the updated RiskLimits."""
        result = RiskManagementService.update_limits(
            portfolio_id=1,
            updates={"max_daily_loss": 0.10},
        )
        assert isinstance(result, RiskLimits)
        assert result.max_daily_loss == 0.10


# ── Notifications ───────────────────────────────────────────


@pytest.mark.django_db
class TestSendNotification:
    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(True, ""),
    )
    def test_send_notification_creates_two_alert_logs(self, mock_telegram, portfolio_state):
        """send_notification creates one 'log' entry and one 'telegram' entry."""
        initial = AlertLog.objects.count()
        RiskManagementService.send_notification(1, "test_event", "info", "Test message")
        assert AlertLog.objects.count() == initial + 2
        assert AlertLog.objects.filter(channel="log").exists()
        assert AlertLog.objects.filter(channel="telegram").exists()

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_notification_records_telegram_failure(self, mock_telegram, portfolio_state):
        """When Telegram fails, the AlertLog records delivered=False."""
        RiskManagementService.send_notification(1, "test_event", "warning", "Fail test")
        telegram_log = AlertLog.objects.filter(channel="telegram").last()
        assert telegram_log.delivered is False
        assert telegram_log.error == "not configured"


# ── Status and Check Trade ──────────────────────────────────


@pytest.mark.django_db
class TestStatusAndCheckTrade:
    def test_get_status_returns_dict(self, portfolio_state):
        """get_status should return equity, drawdown, etc."""
        result = RiskManagementService.get_status(1)
        assert result["equity"] == 10000.0
        assert result["drawdown"] == 0.0
        assert result["is_halted"] is False

    @patch(
        "risk.services.risk.NotificationService.send_telegram_sync",
        return_value=(False, "not configured"),
    )
    def test_check_trade_logs_to_trade_check(self, mock_telegram, portfolio_state):
        """check_trade should create a TradeCheckLog entry."""
        from risk.models import TradeCheckLog

        initial = TradeCheckLog.objects.count()
        approved, reason = RiskManagementService.check_trade(
            portfolio_id=1,
            symbol="BTC/USDT",
            side="buy",
            size=0.01,
            entry_price=50000.0,
        )
        assert TradeCheckLog.objects.count() == initial + 1
        assert isinstance(approved, bool)
