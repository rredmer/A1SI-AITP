"""Tests for DataPipelineService — wraps common.data_pipeline for the web app."""

from unittest.mock import patch

import pandas as pd


class TestDataPipelineServiceListAvailable:
    def test_list_available_no_files(self, tmp_path):
        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "analysis.services.data_pipeline.get_processed_dir",
            return_value=tmp_path,
        ):
            from analysis.services.data_pipeline import DataPipelineService

            service = DataPipelineService()
            service._processed_dir = tmp_path
            result = service.list_available_data()
            assert result == []

    def test_list_available_with_parquet_file(self, tmp_path):
        # Create a fake parquet file with proper naming
        index = pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC")
        df = pd.DataFrame(
            {"open": range(10), "close": range(10)},
            index=index,
        )
        df.to_parquet(tmp_path / "binance_BTC_USDT_1h.parquet")

        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "analysis.services.data_pipeline.get_processed_dir",
            return_value=tmp_path,
        ):
            from analysis.services.data_pipeline import DataPipelineService

            service = DataPipelineService()
            service._processed_dir = tmp_path
            result = service.list_available_data()
            assert len(result) == 1
            assert result[0]["exchange"] == "binance"
            assert result[0]["symbol"] == "BTC/USDT"
            assert result[0]["timeframe"] == "1h"
            assert result[0]["rows"] == 10


class TestDataPipelineServiceGetDataInfo:
    def test_get_data_info_file_exists(self, tmp_path):
        index = pd.date_range("2024-01-01", periods=5, freq="1h", tz="UTC")
        df = pd.DataFrame(
            {
                "open": range(5),
                "high": range(5),
                "low": range(5),
                "close": range(5),
                "volume": range(5),
            },
            index=index,
        )
        df.to_parquet(tmp_path / "binance_BTC_USDT_1h.parquet")

        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "analysis.services.data_pipeline.get_processed_dir",
            return_value=tmp_path,
        ):
            from analysis.services.data_pipeline import DataPipelineService

            service = DataPipelineService()
            service._processed_dir = tmp_path
            result = service.get_data_info("BTC/USDT", "1h", "binance")
            assert result is not None
            assert result["rows"] == 5
            assert result["symbol"] == "BTC/USDT"
            assert "columns" in result
            assert "file_size_mb" in result

    def test_get_data_info_file_missing(self, tmp_path):
        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "analysis.services.data_pipeline.get_processed_dir",
            return_value=tmp_path,
        ):
            from analysis.services.data_pipeline import DataPipelineService

            service = DataPipelineService()
            service._processed_dir = tmp_path
            result = service.get_data_info("NONEXISTENT/PAIR", "1h", "binance")
            assert result is None


class TestDataPipelineServiceDownload:
    def test_download_caps_symbols(self):
        """Symbols list is capped at 50."""
        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.fetch_ohlcv",
            return_value=pd.DataFrame(),
        ), patch(
            "common.data_pipeline.pipeline.save_ohlcv",
        ):
            from analysis.services.data_pipeline import DataPipelineService

            symbols = [f"SYM{i}/USDT" for i in range(100)]
            progress_calls = []

            def progress_cb(pct, msg):
                progress_calls.append((pct, msg))

            result = DataPipelineService.download_data(
                {"symbols": symbols, "timeframes": ["1h"]},
                progress_cb,
            )
            # Should only process 50 symbols
            assert result["total"] == 50

    def test_download_handles_errors(self):
        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.fetch_ohlcv",
            side_effect=Exception("API error"),
        ):
            from analysis.services.data_pipeline import DataPipelineService

            result = DataPipelineService.download_data(
                {"symbols": ["BTC/USDT"], "timeframes": ["1h"]},
                lambda pct, msg: None,
            )
            assert result["downloads"]["BTC/USDT_1h"]["status"] == "error"


class TestDataPipelineServiceGenerateSample:
    def test_generate_sample_data(self, tmp_path):
        with patch(
            "analysis.services.data_pipeline.ensure_platform_imports",
        ), patch(
            "common.data_pipeline.pipeline.save_ohlcv",
            return_value=tmp_path / "sample.parquet",
        ):
            from analysis.services.data_pipeline import DataPipelineService

            progress_calls = []

            def progress_cb(pct, msg):
                progress_calls.append((pct, msg))

            result = DataPipelineService.generate_sample_data(
                {"symbols": ["BTC/USDT"], "timeframes": ["1h"], "days": 10},
                progress_cb,
            )
            assert "generated" in result
            assert "BTC/USDT_1h" in result["generated"]
            assert result["generated"]["BTC/USDT_1h"]["status"] == "ok"
            assert result["generated"]["BTC/USDT_1h"]["rows"] > 0
            assert len(progress_calls) > 0
