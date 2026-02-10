"""
Platform status service — checks framework availability, data summary, active jobs.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import BackgroundJob
from app.services.platform_bridge import (
    get_platform_config_path,
    get_processed_dir,
)

logger = logging.getLogger("platform_status")


class PlatformStatusService:
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def get_framework_status() -> list[dict]:
        """Check which trading frameworks are installed."""
        frameworks = []

        # VectorBT
        try:
            import vectorbt as vbt
            frameworks.append({"name": "VectorBT", "installed": True, "version": vbt.__version__})
        except ImportError:
            frameworks.append({"name": "VectorBT", "installed": False, "version": None})

        # Freqtrade
        try:
            import freqtrade
            ver = getattr(freqtrade, "__version__", "installed")
            frameworks.append({"name": "Freqtrade", "installed": True, "version": ver})
        except ImportError:
            frameworks.append({"name": "Freqtrade", "installed": False, "version": None})

        # NautilusTrader
        try:
            import nautilus_trader
            ver = getattr(nautilus_trader, "__version__", "installed")
            frameworks.append({"name": "NautilusTrader", "installed": True, "version": ver})
        except ImportError:
            frameworks.append({"name": "NautilusTrader", "installed": False, "version": None})

        # ccxt (always needed)
        try:
            import ccxt
            frameworks.append({"name": "CCXT", "installed": True, "version": ccxt.__version__})
        except ImportError:
            frameworks.append({"name": "CCXT", "installed": False, "version": None})

        # pandas / numpy (core)
        try:
            import pandas as pd
            frameworks.append({"name": "Pandas", "installed": True, "version": pd.__version__})
        except ImportError:
            frameworks.append({"name": "Pandas", "installed": False, "version": None})

        return frameworks

    @staticmethod
    def get_data_summary() -> dict:
        """Count Parquet files and summarize data."""
        processed = get_processed_dir()
        files = list(processed.glob("*.parquet"))
        return {
            "data_files": len(files),
            "data_dir": str(processed),
        }

    async def get_active_jobs(self) -> int:
        result = await self._session.execute(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.status.in_(["pending", "running"])
            )
        )
        return result.scalar_one()

    async def get_full_status(self) -> dict:
        frameworks = self.get_framework_status()
        data = self.get_data_summary()
        active_jobs = await self.get_active_jobs()
        return {
            "frameworks": frameworks,
            "data_files": data["data_files"],
            "active_jobs": active_jobs,
        }

    @staticmethod
    def get_platform_config() -> dict:
        """Read platform_config.yaml as dict."""
        config_path = get_platform_config_path()
        if not config_path.exists():
            return {"error": "platform_config.yaml not found"}
        try:
            import yaml
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback: return raw text
            return {"raw": config_path.read_text()[:5000]}
