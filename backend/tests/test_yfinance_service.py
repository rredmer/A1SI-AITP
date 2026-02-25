"""Tests for YFinanceService — wraps yfinance for equity/forex data."""

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from market.services.yfinance_service import YFinanceService


class TestYFinanceServiceFetchTicker:
    @pytest.mark.asyncio
    async def test_fetch_ticker_delegates_to_adapter(self):
        expected = {
            "symbol": "AAPL",
            "price": 175.0,
            "volume_24h": 50_000_000,
            "change_24h": 1.2,
        }
        with patch(
            "core.platform_bridge.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.yfinance_adapter.fetch_ticker_yfinance",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            service = YFinanceService()
            result = await service.fetch_ticker("AAPL", "equity")
            assert result["symbol"] == "AAPL"
            assert result["price"] == 175.0

    @pytest.mark.asyncio
    async def test_fetch_ticker_default_asset_class(self):
        expected = {"symbol": "MSFT", "price": 400.0}
        with patch(
            "core.platform_bridge.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.yfinance_adapter.fetch_ticker_yfinance",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_fetch:
            service = YFinanceService()
            await service.fetch_ticker("MSFT")
            mock_fetch.assert_called_once_with("MSFT", "equity")


class TestYFinanceServiceFetchTickers:
    @pytest.mark.asyncio
    async def test_fetch_tickers_with_symbols(self):
        expected = [
            {"symbol": "AAPL", "price": 175.0},
            {"symbol": "GOOG", "price": 140.0},
        ]
        with patch(
            "core.platform_bridge.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.yfinance_adapter.fetch_tickers_yfinance",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_fetch:
            service = YFinanceService()
            result = await service.fetch_tickers(["AAPL", "GOOG"], "equity")
            assert len(result) == 2
            mock_fetch.assert_called_once_with(["AAPL", "GOOG"], "equity")

    @pytest.mark.asyncio
    async def test_fetch_tickers_none_symbols_uses_watchlist(self):
        expected = [{"symbol": "AAPL", "price": 175.0}]
        with patch(
            "core.platform_bridge.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.yfinance_adapter.fetch_tickers_yfinance",
            new_callable=AsyncMock,
            return_value=expected,
        ), patch(
            "common.data_pipeline.pipeline._DEFAULT_WATCHLISTS",
            {"equity": ["AAPL", "GOOG", "MSFT"]},
        ):
            service = YFinanceService()
            result = await service.fetch_tickers(None, "equity")
            assert isinstance(result, list)


class TestYFinanceServiceFetchOHLCV:
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_returns_formatted_candles(self):
        index = pd.date_range("2024-01-01", periods=3, freq="1D", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [105.0, 106.0, 107.0],
                "low": [98.0, 99.0, 100.0],
                "close": [103.0, 104.0, 105.0],
                "volume": [1000.0, 1100.0, 1200.0],
            },
            index=index,
        )
        with patch(
            "core.platform_bridge.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.yfinance_adapter.fetch_ohlcv_yfinance",
            new_callable=AsyncMock,
            return_value=df,
        ):
            service = YFinanceService()
            result = await service.fetch_ohlcv("AAPL", "1d", 3, "equity")
            assert isinstance(result, list)
            assert len(result) == 3
            assert "timestamp" in result[0]
            assert "open" in result[0]
            assert "close" in result[0]
            assert result[0]["close"] == 103.0

    @pytest.mark.asyncio
    async def test_fetch_ohlcv_empty_df_returns_empty_list(self):
        empty_df = pd.DataFrame()
        with patch(
            "core.platform_bridge.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.yfinance_adapter.fetch_ohlcv_yfinance",
            new_callable=AsyncMock,
            return_value=empty_df,
        ):
            service = YFinanceService()
            result = await service.fetch_ohlcv("INVALID", "1d", 100, "equity")
            assert result == []


class TestYFinanceServiceClose:
    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        service = YFinanceService()
        # Should not raise
        await service.close()
