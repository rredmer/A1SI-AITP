"""Tests for IndicatorService — wraps common.indicators.technical for the web app."""

from unittest.mock import patch

import numpy as np
import pandas as pd

from market.services.indicators import IndicatorService


class TestIndicatorServiceListAvailable:
    def test_returns_list_of_strings(self):
        result = IndicatorService.list_available()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(i, str) for i in result)

    def test_contains_common_indicators(self):
        result = IndicatorService.list_available()
        assert "sma_50" in result
        assert "rsi_14" in result
        assert "macd" in result
        assert "bb_upper" in result
        assert "atr_14" in result


class TestIndicatorServiceCompute:
    def _make_ohlcv_df(self, periods=200):
        """Create a minimal OHLCV DataFrame for testing."""
        np.random.seed(42)
        timestamps = pd.date_range("2024-01-01", periods=periods, freq="1h", tz="UTC")
        prices = 50000 + np.cumsum(np.random.normal(0, 100, periods))
        return pd.DataFrame(
            {
                "open": prices * 0.999,
                "high": prices * 1.01,
                "low": prices * 0.99,
                "close": prices,
                "volume": np.random.uniform(100, 10000, periods),
            },
            index=timestamps,
        )

    def test_compute_returns_error_for_missing_data(self):
        with patch(
            "market.services.indicators.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=pd.DataFrame(),
        ):
            result = IndicatorService.compute("MISSING/PAIR", "1h", "binance")
            assert "error" in result
            assert result["data"] == []

    def test_compute_returns_data_with_indicators(self):
        df = self._make_ohlcv_df(200)

        def mock_add_all_indicators(df_in):
            """Simulate adding indicator columns."""
            result = df_in.copy()
            result["sma_50"] = result["close"].rolling(50).mean()
            result["rsi_14"] = 50.0  # simplified
            return result

        with patch(
            "market.services.indicators.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=df,
        ), patch(
            "common.indicators.technical.add_all_indicators",
            side_effect=mock_add_all_indicators,
        ):
            result = IndicatorService.compute("BTC/USDT", "1h", "binance", limit=50)
            assert result["symbol"] == "BTC/USDT"
            assert result["timeframe"] == "1h"
            assert result["count"] == 50
            assert len(result["data"]) == 50
            # Check each record has timestamp
            assert "timestamp" in result["data"][0]

    def test_compute_filters_specific_indicators(self):
        df = self._make_ohlcv_df(100)

        def mock_add_all_indicators(df_in):
            result = df_in.copy()
            result["sma_50"] = result["close"].rolling(50).mean()
            result["rsi_14"] = 50.0
            result["macd"] = 0.0
            return result

        with patch(
            "market.services.indicators.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=df,
        ), patch(
            "common.indicators.technical.add_all_indicators",
            side_effect=mock_add_all_indicators,
        ):
            result = IndicatorService.compute(
                "BTC/USDT", "1h", "binance",
                indicators=["sma_50"],
                limit=10,
            )
            assert "columns" in result
            # Should include base cols + requested indicator
            assert "sma_50" in result["columns"]
            assert "open" in result["columns"]

    def test_compute_handles_nan_values(self):
        df = self._make_ohlcv_df(100)

        def mock_add_all_indicators(df_in):
            result = df_in.copy()
            # SMA will have NaN for first N-1 rows
            result["sma_50"] = result["close"].rolling(50).mean()
            return result

        with patch(
            "market.services.indicators.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=df,
        ), patch(
            "common.indicators.technical.add_all_indicators",
            side_effect=mock_add_all_indicators,
        ):
            result = IndicatorService.compute(
                "BTC/USDT", "1h", "binance",
                indicators=["sma_50"],
                limit=100,
            )
            # First rows should have None for sma_50 (NaN converted to None)
            first_record = result["data"][0]
            assert first_record["sma_50"] is None
