"""Risk monitoring periodic check tests."""
import pytest

from portfolio.models import Portfolio
from risk.models import AlertLog, RiskLimits, RiskMetricHistory, RiskState
from risk.services.risk import RiskManagementService


def _setup_portfolio(portfolio_id=1, equity=10000.0, peak=10000.0, daily_pnl=0.0):
    """Create portfolio with risk state and limits."""
    Portfolio.objects.get_or_create(
        id=portfolio_id, defaults={"name": f"Test Portfolio {portfolio_id}"},
    )
    state, _ = RiskState.objects.get_or_create(portfolio_id=portfolio_id)
    state.total_equity = equity
    state.peak_equity = peak
    state.daily_start_equity = peak
    state.daily_pnl = daily_pnl
    state.is_halted = False
    state.halt_reason = ""
    state.save()
    limits, _ = RiskLimits.objects.get_or_create(portfolio_id=portfolio_id)
    return state, limits


@pytest.mark.django_db
class TestPeriodicRiskCheck:
    def test_periodic_risk_check_records_metrics(self):
        _setup_portfolio()
        RiskManagementService.periodic_risk_check(1)
        assert RiskMetricHistory.objects.filter(portfolio_id=1).count() >= 1

    def test_periodic_risk_check_auto_halts_on_drawdown(self):
        state, limits = _setup_portfolio(equity=7000.0, peak=10000.0)
        limits.max_portfolio_drawdown = 0.2  # 20% limit, current is 30%
        limits.save()
        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "auto_halted"
        state.refresh_from_db()
        assert state.is_halted is True

    def test_periodic_risk_check_auto_halts_on_daily_loss(self):
        state, limits = _setup_portfolio(equity=10000.0, daily_pnl=-600.0)
        limits.max_daily_loss = 0.05  # 5% limit, current is 6%
        limits.save()
        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "auto_halted"
        state.refresh_from_db()
        assert state.is_halted is True

    def test_periodic_risk_check_warns_at_80_pct(self):
        # 18% drawdown with 20% limit = 90% of limit (> 80% threshold)
        state, limits = _setup_portfolio(equity=8200.0, peak=10000.0)
        limits.max_portfolio_drawdown = 0.2
        limits.save()
        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "warning"
        assert "warning" in result

    def test_periodic_risk_check_no_double_halt(self):
        state, limits = _setup_portfolio(equity=7000.0, peak=10000.0)
        state.is_halted = True
        state.halt_reason = "Already halted"
        state.save()
        limits.max_portfolio_drawdown = 0.2
        limits.save()
        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "halted"
        # Should not create additional halt alerts
        halt_alerts = AlertLog.objects.filter(event_type="risk_auto_halt").count()
        assert halt_alerts == 0

    def test_periodic_risk_check_healthy(self):
        _setup_portfolio(equity=9900.0, peak=10000.0)
        result = RiskManagementService.periodic_risk_check(1)
        assert result["status"] == "ok"


@pytest.mark.django_db
class TestRiskMonitoringExecutor:
    def test_risk_monitoring_executor(self):
        from core.services.task_registry import TASK_REGISTRY
        _setup_portfolio()
        executor = TASK_REGISTRY["risk_monitoring"]
        result = executor({}, lambda p, m: None)
        assert result["status"] == "completed"
        assert result["portfolios_checked"] == 1

    def test_risk_monitoring_in_registry(self):
        from core.services.task_registry import TASK_REGISTRY
        assert "risk_monitoring" in TASK_REGISTRY
