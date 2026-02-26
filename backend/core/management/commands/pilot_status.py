"""Daily status report for the live trading pilot.

Sections: paper trading performance, risk metrics, data quality, system health,
regime state. Overall status: healthy / warning / critical.

Usage: manage.py pilot_status [--json] [--portfolio-id N] [--days N]
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


def _paper_trading_section(portfolio_id: int, date_from: str) -> dict[str, Any]:
    """Paper trading performance over the date window."""
    from trading.services.performance import TradingPerformanceService

    return TradingPerformanceService.get_summary(
        portfolio_id=portfolio_id,
        mode="paper",
        date_from=date_from,
    )


def _risk_section(portfolio_id: int) -> dict[str, Any]:
    """Current risk metrics from RiskManagementService."""
    from risk.services.risk import RiskManagementService

    return RiskManagementService.get_status(portfolio_id)


def _data_quality_section() -> dict[str, Any]:
    """Data pipeline quality summary."""
    try:
        from core.platform_bridge import ensure_platform_imports

        ensure_platform_imports()
        from common.data_pipeline.pipeline import validate_all_data

        reports = validate_all_data()
    except Exception as exc:
        return {"error": str(exc), "total_files": 0, "stale": 0, "gaps": 0}

    stale = sum(1 for r in reports if r.is_stale)
    gaps = sum(len(r.gaps) for r in reports)
    return {
        "total_files": len(reports),
        "stale": stale,
        "gaps": gaps,
        "passed": sum(1 for r in reports if r.passed),
    }


def _system_health_section(portfolio_id: int) -> dict[str, Any]:
    """Scheduler, alerts, circuit breakers."""
    from risk.models import AlertLog

    try:
        from core.services.scheduler import get_scheduler

        scheduler_running = get_scheduler().running
    except Exception:
        scheduler_running = False

    critical_alerts = AlertLog.objects.filter(
        portfolio_id=portfolio_id, severity="critical",
    ).count()
    warning_alerts = AlertLog.objects.filter(
        portfolio_id=portfolio_id, severity="warning",
    ).count()

    from market.services.circuit_breaker import get_all_breakers

    breakers = get_all_breakers()
    open_breakers = [b["exchange_id"] for b in breakers if b["state"] == "open"]

    return {
        "scheduler_running": scheduler_running,
        "critical_alerts": critical_alerts,
        "warning_alerts": warning_alerts,
        "open_breakers": open_breakers,
    }


def _regime_section() -> dict[str, Any]:
    """Current regime detection on BTC/USDT (graceful skip on import error)."""
    try:
        from core.platform_bridge import ensure_platform_imports

        ensure_platform_imports()
        from common.data_pipeline.pipeline import load_ohlcv
        from common.regime.regime_detector import RegimeDetector

        df = None
        for eid in ("binance", "kraken", "coinbase", "kucoin", "bybit"):
            df = load_ohlcv("BTC/USDT", "1h", exchange_id=eid)
            if df is not None and not df.empty:
                break
        if df is None or df.empty:
            return {"regime": "unknown", "detail": "No BTC/USDT data available"}

        detector = RegimeDetector()
        state = detector.detect(df)
        return {
            "regime": state.regime.value if hasattr(state.regime, "value") else str(state.regime),
            "confidence": round(state.confidence, 3),
            "adx": round(state.adx_value, 2),
        }
    except ImportError:
        return {"regime": "unavailable", "detail": "Regime detector not importable"}
    except Exception as exc:
        return {"regime": "error", "detail": str(exc)}


def _compute_overall(
    risk: dict[str, Any],
    health: dict[str, Any],
) -> str:
    """Determine overall pilot status: healthy / warning / critical."""
    if risk.get("is_halted"):
        return "critical"
    if health.get("open_breakers"):
        return "critical"
    if health.get("critical_alerts", 0) > 0:
        return "critical"
    drawdown = risk.get("drawdown", 0)
    if drawdown > 0.10:
        return "warning"
    if health.get("warning_alerts", 0) > 5:
        return "warning"
    if not health.get("scheduler_running"):
        return "warning"
    return "healthy"


class Command(BaseCommand):
    help = "Generate a daily status report for the live trading pilot"

    def add_arguments(self, parser):
        parser.add_argument(
            "--json", action="store_true", help="Output as JSON",
        )
        parser.add_argument(
            "--portfolio-id", type=int, default=1, help="Portfolio ID (default: 1)",
        )
        parser.add_argument(
            "--days", type=int, default=1, help="Lookback window in days (default: 1)",
        )

    def handle(self, *args, **options):
        portfolio_id: int = options["portfolio_id"]
        days: int = options["days"]
        as_json: bool = options["json"]

        date_from = (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()

        performance = _paper_trading_section(portfolio_id, date_from)
        risk = _risk_section(portfolio_id)
        data_quality = _data_quality_section()
        health = _system_health_section(portfolio_id)
        regime = _regime_section()
        overall = _compute_overall(risk, health)

        report = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "portfolio_id": portfolio_id,
            "days": days,
            "overall_status": overall,
            "paper_trading": performance,
            "risk": risk,
            "data_quality": data_quality,
            "system_health": health,
            "regime": regime,
        }

        if as_json:
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            self._print_report(report)

    def _print_report(self, report: dict) -> None:
        overall = report["overall_status"]
        if overall == "healthy":
            status_tag = self.style.SUCCESS(f"[{overall.upper()}]")
        elif overall == "warning":
            status_tag = self.style.WARNING(f"[{overall.upper()}]")
        else:
            status_tag = self.style.ERROR(f"[{overall.upper()}]")

        self.stdout.write(f"\n  Pilot Status Report — {status_tag}")
        pid = report["portfolio_id"]
        days = report["days"]
        self.stdout.write(f"  Portfolio: {pid}  |  Window: {days} day(s)")
        self.stdout.write("")

        # Paper Trading
        perf = report["paper_trading"]
        self.stdout.write("  Paper Trading Performance")
        self.stdout.write(f"    Trades: {perf['total_trades']}")
        self.stdout.write(f"    Win rate: {perf['win_rate']}%")
        self.stdout.write(f"    P&L: {perf['total_pnl']}")
        pf = perf["profit_factor"]
        self.stdout.write(f"    Profit factor: {pf if pf is not None else 'N/A'}")
        self.stdout.write("")

        # Risk
        risk = report["risk"]
        self.stdout.write("  Risk Metrics")
        self.stdout.write(f"    Equity: ${risk['equity']:,.2f}")
        self.stdout.write(f"    Drawdown: {risk['drawdown']:.2%}")
        self.stdout.write(f"    Daily P&L: {risk['daily_pnl']}")
        halted = risk["is_halted"]
        if halted:
            self.stdout.write(self.style.ERROR(f"    HALTED: {risk['halt_reason']}"))
        else:
            self.stdout.write("    Halt status: active")
        self.stdout.write("")

        # Data Quality
        dq = report["data_quality"]
        if "error" in dq:
            self.stdout.write(f"  Data Quality: error — {dq['error']}")
        else:
            self.stdout.write("  Data Quality")
            self.stdout.write(f"    Files: {dq['total_files']} ({dq['passed']} passed)")
            self.stdout.write(f"    Stale: {dq['stale']}, Gaps: {dq['gaps']}")
        self.stdout.write("")

        # System Health
        sh = report["system_health"]
        self.stdout.write("  System Health")
        sched = "running" if sh["scheduler_running"] else "stopped"
        self.stdout.write(f"    Scheduler: {sched}")
        crit = sh["critical_alerts"]
        warn = sh["warning_alerts"]
        self.stdout.write(f"    Alerts: {crit} critical, {warn} warning")
        if sh["open_breakers"]:
            breakers = ", ".join(sh["open_breakers"])
            self.stdout.write(self.style.ERROR(f"    Open breakers: {breakers}"))
        else:
            self.stdout.write("    Breakers: all closed")
        self.stdout.write("")

        # Regime
        reg = report["regime"]
        self.stdout.write("  Market Regime")
        self.stdout.write(f"    Regime: {reg.get('regime', 'unknown')}")
        if "confidence" in reg:
            self.stdout.write(f"    Confidence: {reg['confidence']}")
        if "detail" in reg:
            self.stdout.write(f"    Detail: {reg['detail']}")
        self.stdout.write("")
