"""Tests for ScreenerService — wraps VectorBT screener for the web app."""

from unittest.mock import patch

import pandas as pd
import pytest

from analysis.services.screening import STRATEGY_TYPES, ScreenerService


class TestScreenerServiceStrategyTypes:
    def test_strategy_types_list(self):
        assert isinstance(STRATEGY_TYPES, list)
        assert len(STRATEGY_TYPES) > 0
        names = [s["name"] for s in STRATEGY_TYPES]
        assert "sma_crossover" in names
        assert "rsi_mean_reversion" in names


class TestScreenerServiceRunFullScreen:
    def test_returns_error_when_no_data(self):
        with patch(
            "analysis.services.screening.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=pd.DataFrame(),
        ):
            progress_calls = []

            def progress_cb(pct, msg):
                progress_calls.append((pct, msg))

            result = ScreenerService.run_full_screen(
                {"symbol": "BTC/USDT", "timeframe": "1h", "exchange": "binance"},
                progress_cb,
            )
            assert "error" in result

    def test_handles_vectorbt_not_installed(self):
        """When VectorBT is not installed, strategies report import error."""
        import numpy as np

        index = pd.date_range("2024-01-01", periods=500, freq="1h", tz="UTC")
        prices = 50000 + np.cumsum(np.random.normal(0, 100, 500))
        df = pd.DataFrame(
            {
                "open": prices * 0.999,
                "high": prices * 1.01,
                "low": prices * 0.99,
                "close": prices,
                "volume": np.random.uniform(100, 10000, 500),
            },
            index=index,
        )

        def mock_sma(series, period):
            return series.rolling(period).mean()

        def mock_ema(series, period):
            return series.ewm(span=period).mean()

        def mock_rsi(series, period):
            return pd.Series(50.0, index=series.index)

        with patch(
            "analysis.services.screening.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=df,
        ), patch(
            "common.indicators.technical.sma",
            side_effect=mock_sma,
        ), patch(
            "common.indicators.technical.ema",
            side_effect=mock_ema,
        ), patch(
            "common.indicators.technical.rsi",
            side_effect=mock_rsi,
        ), patch.dict(
            "sys.modules",
            {"vectorbt": None},
        ):
            result = ScreenerService.run_full_screen(
                {"symbol": "BTC/USDT", "timeframe": "1h"},
                lambda pct, msg: None,
            )
            assert "strategies" in result
            # Each strategy should report import error
            for _strategy_name, strategy_result in result["strategies"].items():
                assert "error" in strategy_result

    def test_progress_callback_called(self):
        with patch(
            "analysis.services.screening.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.load_ohlcv",
            return_value=pd.DataFrame(),
        ):
            progress_calls = []

            def progress_cb(pct, msg):
                progress_calls.append((pct, msg))

            ScreenerService.run_full_screen(
                {"symbol": "BTC/USDT"},
                progress_cb,
            )
            assert len(progress_calls) > 0
            assert progress_calls[0][0] == pytest.approx(0.05)
