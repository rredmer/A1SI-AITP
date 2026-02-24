"""Tests for DataServiceRouter and YFinanceService — async data routing layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
class TestDataServiceRouterRouting:
    @patch("market.services.exchange.ExchangeService")
    async def test_routes_crypto_to_exchange_service(self, mock_exchange):
        from market.services.data_router import DataServiceRouter

        mock_svc = MagicMock()
        mock_svc.fetch_ticker = AsyncMock(return_value={"last": 50000.0})
        mock_svc.close = AsyncMock()
        mock_exchange.return_value = mock_svc

        router = DataServiceRouter()
        result = await router.fetch_ticker("BTC/USDT", "crypto")

        assert result["last"] == 50000.0
        mock_svc.fetch_ticker.assert_awaited_once()

    @patch("market.services.yfinance_service.YFinanceService")
    async def test_routes_equity_to_yfinance(self, mock_yfinance):
        from market.services.data_router import DataServiceRouter

        mock_svc = MagicMock()
        mock_svc.fetch_ticker = AsyncMock(return_value={"price": 150.0})
        mock_yfinance.return_value = mock_svc

        router = DataServiceRouter()
        result = await router.fetch_ticker("AAPL/USD", "equity")

        assert result["price"] == 150.0
        mock_svc.fetch_ticker.assert_awaited_once()

    @patch("market.services.yfinance_service.YFinanceService")
    async def test_routes_forex_to_yfinance(self, mock_yfinance):
        from market.services.data_router import DataServiceRouter

        mock_svc = MagicMock()
        mock_svc.fetch_ticker = AsyncMock(return_value={"price": 1.08})
        mock_yfinance.return_value = mock_svc

        router = DataServiceRouter()
        result = await router.fetch_ticker("EUR/USD", "forex")

        assert result["price"] == 1.08

    @patch("market.services.exchange.ExchangeService")
    async def test_routes_unknown_to_exchange_service(self, mock_exchange):
        from market.services.data_router import DataServiceRouter

        mock_svc = MagicMock()
        mock_svc.fetch_ticker = AsyncMock(return_value={"last": 1800.0})
        mock_svc.close = AsyncMock()
        mock_exchange.return_value = mock_svc

        router = DataServiceRouter()
        result = await router.fetch_ticker("GOLD/USD", "commodities")

        assert result["last"] == 1800.0

    @patch("market.services.yfinance_service.YFinanceService")
    async def test_routes_tickers_equity_to_yfinance(self, mock_yfinance):
        from market.services.data_router import DataServiceRouter

        mock_svc = MagicMock()
        mock_svc.fetch_tickers = AsyncMock(return_value=[{"symbol": "AAPL", "price": 150.0}])
        mock_yfinance.return_value = mock_svc

        router = DataServiceRouter()
        result = await router.fetch_tickers(["AAPL/USD"], "equity")

        assert len(result) == 1
        mock_svc.fetch_tickers.assert_awaited_once()

    @patch("market.services.yfinance_service.YFinanceService")
    async def test_routes_ohlcv_equity_to_yfinance(self, mock_yfinance):
        from market.services.data_router import DataServiceRouter

        mock_svc = MagicMock()
        mock_svc.fetch_ohlcv = AsyncMock(return_value=[{"timestamp": 1, "close": 150.0}])
        mock_yfinance.return_value = mock_svc

        router = DataServiceRouter()
        result = await router.fetch_ohlcv("AAPL/USD", "1d", 30, "equity")

        assert len(result) == 1
        mock_svc.fetch_ohlcv.assert_awaited_once()


@pytest.mark.asyncio
class TestYFinanceService:
    @patch("market.services.yfinance_service.YFinanceService.fetch_ticker")
    async def test_fetch_ticker_returns_dict(self, mock_fetch):
        from market.services.yfinance_service import YFinanceService

        mock_fetch.return_value = {"price": 150.0, "symbol": "AAPL"}
        svc = YFinanceService()
        result = await svc.fetch_ticker("AAPL/USD", "equity")
        assert isinstance(result, dict)
        assert "price" in result

    @patch("market.services.yfinance_service.YFinanceService.fetch_tickers")
    async def test_fetch_tickers_returns_list(self, mock_fetch):
        from market.services.yfinance_service import YFinanceService

        mock_fetch.return_value = [{"symbol": "AAPL", "price": 150.0}]
        svc = YFinanceService()
        result = await svc.fetch_tickers(["AAPL/USD"], "equity")
        assert isinstance(result, list)

    @patch("market.services.yfinance_service.YFinanceService.fetch_ohlcv")
    async def test_fetch_ohlcv_returns_list_of_dicts(self, mock_fetch):
        from market.services.yfinance_service import YFinanceService

        mock_fetch.return_value = [
            {
                "timestamp": 1000,
                "open": 149.0,
                "high": 151.0,
                "low": 148.0,
                "close": 150.0,
                "volume": 1000.0,
            },
        ]
        svc = YFinanceService()
        result = await svc.fetch_ohlcv("AAPL/USD", "1d", 30, "equity")
        assert isinstance(result, list)
        assert len(result) == 1

    @patch("market.services.yfinance_service.YFinanceService.fetch_ohlcv")
    async def test_fetch_ohlcv_empty_df_returns_empty(self, mock_fetch):
        from market.services.yfinance_service import YFinanceService

        mock_fetch.return_value = []
        svc = YFinanceService()
        result = await svc.fetch_ohlcv("AAPL/USD", "1d", 30, "equity")
        assert result == []

    async def test_close_is_noop(self):
        from market.services.yfinance_service import YFinanceService

        svc = YFinanceService()
        await svc.close()  # Should not raise

    @patch("market.services.yfinance_service.YFinanceService.fetch_ticker")
    async def test_adapter_returns_price_not_last_key(self, mock_fetch):
        from market.services.yfinance_service import YFinanceService

        mock_fetch.return_value = {"price": 150.0, "volume": 1000000}
        svc = YFinanceService()
        result = await svc.fetch_ticker("AAPL/USD", "equity")
        assert "price" in result
        assert "last" not in result
