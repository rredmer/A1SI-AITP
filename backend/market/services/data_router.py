"""Unified data routing: directs requests to the correct data service by asset class."""

import logging

logger = logging.getLogger(__name__)


class DataServiceRouter:
    """Routes data requests to ExchangeService (crypto) or YFinanceService (equity/forex)."""

    async def fetch_ticker(self, symbol: str, asset_class: str = "crypto") -> dict:
        if asset_class in ("equity", "forex"):
            from market.services.yfinance_service import YFinanceService

            service = YFinanceService()
            return await service.fetch_ticker(symbol, asset_class)

        from market.services.exchange import ExchangeService

        service = ExchangeService()
        try:
            return await service.fetch_ticker(symbol)
        finally:
            await service.close()

    async def fetch_tickers(
        self, symbols: list[str] | None, asset_class: str = "crypto",
    ) -> list[dict]:
        if asset_class in ("equity", "forex"):
            from market.services.yfinance_service import YFinanceService

            service = YFinanceService()
            return await service.fetch_tickers(symbols, asset_class)

        from market.services.exchange import ExchangeService

        service = ExchangeService()
        try:
            return await service.fetch_tickers(symbols)
        finally:
            await service.close()

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        asset_class: str = "crypto",
    ) -> list[dict]:
        if asset_class in ("equity", "forex"):
            from market.services.yfinance_service import YFinanceService

            service = YFinanceService()
            return await service.fetch_ohlcv(symbol, timeframe, limit, asset_class)

        from market.services.exchange import ExchangeService

        service = ExchangeService()
        try:
            return await service.fetch_ohlcv(symbol, timeframe, limit)
        finally:
            await service.close()
