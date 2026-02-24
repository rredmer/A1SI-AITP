"""Backtest CSV export tests."""
import pytest

from analysis.models import BackgroundJob, BacktestResult


def _create_result(framework="vectorbt", asset_class="crypto", strategy_name="SMA",
                   symbol="BTC/USDT", timeframe="1h", timerange="20250101-20260101",
                   metrics=None):
    job = BackgroundJob.objects.create(job_type="backtest", status="completed")
    return BacktestResult.objects.create(
        job=job,
        framework=framework,
        asset_class=asset_class,
        strategy_name=strategy_name,
        symbol=symbol,
        timeframe=timeframe,
        timerange=timerange,
        metrics=metrics or {"total_return": 0.15, "sharpe_ratio": 1.2, "max_drawdown": -0.1},
    )


@pytest.mark.django_db
class TestBacktestExport:
    def _login(self, client, django_user_model):
        user = django_user_model.objects.create_user(username="export_user", password="pass")
        client.force_login(user)

    def test_export_returns_csv(self, client, django_user_model):
        self._login(client, django_user_model)
        resp = client.get("/api/backtest/export/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_export_has_content_disposition(self, client, django_user_model):
        self._login(client, django_user_model)
        resp = client.get("/api/backtest/export/")
        assert "Content-Disposition" in resp
        assert "backtest_results.csv" in resp["Content-Disposition"]

    def test_export_includes_headers(self, client, django_user_model):
        self._login(client, django_user_model)
        resp = client.get("/api/backtest/export/")
        content = resp.content.decode()
        lines = content.strip().split("\n")
        assert len(lines) >= 1
        header = lines[0]
        assert "id" in header
        assert "strategy_name" in header
        assert "total_return" in header

    def test_export_includes_data(self, client, django_user_model):
        self._login(client, django_user_model)
        _create_result(strategy_name="TestStrat", symbol="BTC/USDT")
        resp = client.get("/api/backtest/export/")
        content = resp.content.decode()
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
        assert "TestStrat" in lines[1]
        assert "BTC/USDT" in lines[1]

    def test_export_filter_by_asset_class(self, client, django_user_model):
        self._login(client, django_user_model)
        _create_result(asset_class="crypto")
        _create_result(asset_class="equity")
        resp = client.get("/api/backtest/export/?asset_class=crypto")
        content = resp.content.decode()
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 crypto row

    def test_export_filter_by_framework(self, client, django_user_model):
        self._login(client, django_user_model)
        _create_result(framework="vectorbt")
        _create_result(framework="freqtrade")
        resp = client.get("/api/backtest/export/?framework=vectorbt")
        content = resp.content.decode()
        lines = content.strip().split("\n")
        assert len(lines) == 2

    def test_export_empty_returns_headers_only(self, client, django_user_model):
        self._login(client, django_user_model)
        resp = client.get("/api/backtest/export/")
        content = resp.content.decode()
        lines = content.strip().split("\n")
        assert len(lines) == 1  # Just the header row
        assert "id" in lines[0]
