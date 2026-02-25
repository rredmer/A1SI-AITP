"""Dashboard KPI aggregation service."""

import logging
from datetime import datetime, timezone

from core.platform_bridge import get_processed_dir

logger = logging.getLogger(__name__)


class DashboardService:
    """Aggregates KPIs from portfolio, trading, risk, and platform services."""

    @staticmethod
    def get_kpis(asset_class: str | None = None) -> dict:
        from core.services.metrics import timed

        with timed("dashboard_kpi_latency_seconds"):
            portfolio_data = DashboardService._get_portfolio_kpis(asset_class)
            trading_data = DashboardService._get_trading_kpis(asset_class)
            risk_data = DashboardService._get_risk_kpis()
            platform_data = DashboardService._get_platform_kpis()

            return {
                "portfolio": portfolio_data,
                "trading": trading_data,
                "risk": risk_data,
                "platform": platform_data,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    @staticmethod
    def _get_portfolio_kpis(asset_class: str | None = None) -> dict:
        try:
            from portfolio.models import Portfolio
            from portfolio.services.analytics import PortfolioAnalyticsService

            portfolio = Portfolio.objects.order_by("id").first()
            if not portfolio:
                return {
                    "count": 0,
                    "total_value": 0.0,
                    "total_cost": 0.0,
                    "unrealized_pnl": 0.0,
                    "pnl_pct": 0.0,
                }

            summary = PortfolioAnalyticsService.get_portfolio_summary(portfolio.id)
            return {
                "count": summary.get("holding_count", 0),
                "total_value": summary.get("total_value", 0.0),
                "total_cost": summary.get("total_cost", 0.0),
                "unrealized_pnl": summary.get("unrealized_pnl", 0.0),
                "pnl_pct": summary.get("pnl_pct", 0.0),
            }
        except Exception as e:
            logger.warning("Failed to get portfolio KPIs: %s", e)
            return {
                "count": 0,
                "total_value": 0.0,
                "total_cost": 0.0,
                "unrealized_pnl": 0.0,
                "pnl_pct": 0.0,
            }

    @staticmethod
    def _get_trading_kpis(asset_class: str | None = None) -> dict:
        try:
            from portfolio.models import Portfolio
            from trading.models import Order, OrderStatus
            from trading.services.performance import TradingPerformanceService

            portfolio = Portfolio.objects.order_by("id").first()
            if portfolio:
                summary = TradingPerformanceService.get_summary(
                    portfolio.id, asset_class=asset_class,
                )
            else:
                summary = {}
            open_orders = Order.objects.filter(
                status__in=[
                    OrderStatus.PENDING,
                    OrderStatus.SUBMITTED,
                    OrderStatus.OPEN,
                    OrderStatus.PARTIAL_FILL,
                ],
            ).count()
            return {
                "total_trades": summary.get("total_trades", 0),
                "win_rate": summary.get("win_rate", 0.0),
                "total_pnl": summary.get("total_pnl", 0.0),
                "profit_factor": summary.get("profit_factor"),
                "open_orders": open_orders,
            }
        except Exception as e:
            logger.warning("Failed to get trading KPIs: %s", e)
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "profit_factor": None,
                "open_orders": 0,
            }

    @staticmethod
    def _get_risk_kpis() -> dict:
        try:
            from portfolio.models import Portfolio
            from risk.services.risk import RiskManagementService

            portfolio = Portfolio.objects.order_by("id").first()
            if not portfolio:
                return {
                    "equity": 0.0,
                    "drawdown": 0.0,
                    "daily_pnl": 0.0,
                    "is_halted": False,
                    "open_positions": 0,
                }

            status = RiskManagementService.get_status(portfolio.id)
            return {
                "equity": status.get("equity", 0.0),
                "drawdown": status.get("drawdown", 0.0),
                "daily_pnl": status.get("daily_pnl", 0.0),
                "is_halted": status.get("is_halted", False),
                "open_positions": status.get("open_positions", 0),
            }
        except Exception as e:
            logger.warning("Failed to get risk KPIs: %s", e)
            return {
                "equity": 0.0,
                "drawdown": 0.0,
                "daily_pnl": 0.0,
                "is_halted": False,
                "open_positions": 0,
            }

    @staticmethod
    def _get_platform_kpis() -> dict:
        try:
            from analysis.models import BackgroundJob

            processed = get_processed_dir()
            data_files = len(list(processed.glob("*.parquet")))
            active_jobs = BackgroundJob.objects.filter(
                status__in=["pending", "running"],
            ).count()
            framework_count = sum(
                1
                for fw in _get_framework_list()
                if fw["installed"]
            )
            return {
                "data_files": data_files,
                "active_jobs": active_jobs,
                "framework_count": framework_count,
            }
        except Exception as e:
            logger.warning("Failed to get platform KPIs: %s", e)
            return {
                "data_files": 0,
                "active_jobs": 0,
                "framework_count": 0,
            }


def _get_framework_list() -> list[dict]:
    """Lightweight framework check — reuses core.views logic."""
    from core.views import _get_framework_status

    return _get_framework_status()
