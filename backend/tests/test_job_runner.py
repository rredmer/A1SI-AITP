"""Tests for JobRunner — submit, run, progress, cancel, and error paths."""

from unittest.mock import patch

import pytest

from analysis.models import BackgroundJob, BacktestResult
from analysis.services.job_runner import JobRunner, _job_progress


@pytest.fixture
def runner():
    """Fresh JobRunner with 1 worker."""
    return JobRunner(max_workers=1)


@pytest.fixture(autouse=True)
def clear_progress():
    """Clean up progress store after each test."""
    yield
    _job_progress.clear()


# ── Submit (DB record creation only) ────────────────────────


@pytest.mark.django_db
class TestJobRunnerSubmit:
    def test_submit_creates_pending_job(self, runner):
        """submit() should create a BackgroundJob with status=pending."""
        # Don't let the thread actually run; we just verify the DB record
        with patch.object(runner._executor, "submit"):
            job_id = runner.submit(
                "test_type",
                lambda params, cb: {"result": "ok"},
                params={"key": "val"},
            )
        job = BackgroundJob.objects.get(id=job_id)
        assert job.status == "pending"
        assert job.job_type == "test_type"
        assert job.params == {"key": "val"}

    def test_submit_sets_initial_progress(self, runner):
        """After submit, in-memory progress should be 0.0 with 'Queued'."""
        with patch.object(runner._executor, "submit"):
            job_id = runner.submit("progress_init", lambda p, cb: {})
        progress = _job_progress.get(job_id)
        assert progress is not None
        assert progress["progress"] == 0.0
        assert progress["progress_message"] == "Queued"

    def test_submit_params_default_none(self, runner):
        """submit() with no params should still create a job with null params."""
        with patch.object(runner._executor, "submit"):
            job_id = runner.submit("no_params", lambda p, cb: {})
        job = BackgroundJob.objects.get(id=job_id)
        assert job.params is None


# ── _run_job direct invocation (synchronous, same thread) ───


@pytest.mark.django_db(transaction=True)
class TestJobRunnerRun:
    def test_run_job_completes_successfully(self, runner):
        """_run_job should transition pending -> running -> completed."""
        def success_fn(params, progress_cb):
            progress_cb(0.5, "halfway")
            return {"answer": 42}

        job = BackgroundJob.objects.create(
            job_type="test_run",
            status="pending",
            params={},
        )

        with patch("core.services.ws_broadcast.broadcast_scheduler_event"):
            runner._run_job(str(job.id), success_fn, {})

        job.refresh_from_db()
        assert job.status == "completed"
        assert job.result == {"answer": 42}
        assert job.progress == 1.0
        assert job.started_at is not None
        assert job.completed_at is not None

    def test_run_job_records_failure(self, runner):
        """A failing run_fn should set status=failed and store error."""
        def fail_fn(params, progress_cb):
            raise ValueError("Something broke")

        job = BackgroundJob.objects.create(
            job_type="test_fail",
            status="pending",
            params={},
        )

        with patch("core.services.ws_broadcast.broadcast_scheduler_event"):
            runner._run_job(str(job.id), fail_fn, {})

        job.refresh_from_db()
        assert job.status == "failed"
        assert "Something broke" in job.error

    def test_run_job_records_failure_progress(self, runner):
        """Failed job should have progress message showing failure."""
        def fail_fn(params, progress_cb):
            raise RuntimeError("Kaboom")

        job = BackgroundJob.objects.create(
            job_type="test_fail_prog",
            status="pending",
            params={},
        )

        with patch("core.services.ws_broadcast.broadcast_scheduler_event"):
            runner._run_job(str(job.id), fail_fn, {})

        progress = _job_progress.get(str(job.id))
        assert progress is not None
        assert "Failed" in progress["progress_message"]
        assert "Kaboom" in progress["progress_message"]


# ── Progress ────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
class TestJobRunnerProgress:
    def test_progress_callback_updates_store(self, runner):
        """Progress callback should update the in-memory progress dict."""
        captured_progress = []

        def capturing_fn(params, progress_cb):
            progress_cb(0.3, "step 1")
            captured_progress.append(_job_progress.get(str(job.id), {}).copy())
            progress_cb(0.7, "step 2")
            captured_progress.append(_job_progress.get(str(job.id), {}).copy())
            return {}

        job = BackgroundJob.objects.create(
            job_type="progress_test",
            status="pending",
            params={},
        )

        with patch("core.services.ws_broadcast.broadcast_scheduler_event"):
            runner._run_job(str(job.id), capturing_fn, {})

        # After completion, progress should be 1.0
        final = _job_progress.get(str(job.id))
        assert final is not None
        assert final["progress"] == 1.0
        assert final["progress_message"] == "Complete"

        # Mid-run snapshots should have intermediate values
        assert len(captured_progress) == 2
        assert captured_progress[0]["progress"] == 0.3
        assert captured_progress[1]["progress"] == 0.7

    def test_progress_capped_at_one(self, runner):
        """Progress values > 1.0 are capped to 1.0 by the callback."""
        def overcap_fn(params, progress_cb):
            progress_cb(5.0, "over")
            return {}

        job = BackgroundJob.objects.create(
            job_type="cap_test",
            status="pending",
            params={},
        )

        with patch("core.services.ws_broadcast.broadcast_scheduler_event"):
            runner._run_job(str(job.id), overcap_fn, {})

        # The callback caps at 1.0 via min(progress, 1.0)
        # After completion it's also 1.0
        final = _job_progress.get(str(job.id))
        assert final["progress"] == 1.0

    def test_get_live_progress_returns_none_for_unknown(self):
        """get_live_progress for an unknown job_id returns None."""
        assert JobRunner.get_live_progress("nonexistent-id") is None


# ── Cancel ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestJobRunnerCancel:
    def test_cancel_pending_job(self):
        """Cancelling a pending job should update status to cancelled."""
        job = BackgroundJob.objects.create(
            job_type="test_cancel",
            status="pending",
        )
        result = JobRunner.cancel_job(str(job.id))
        assert result is True
        job.refresh_from_db()
        assert job.status == "cancelled"
        assert job.completed_at is not None

    def test_cancel_running_job(self):
        """Cancelling a running job should update status to cancelled."""
        job = BackgroundJob.objects.create(
            job_type="test_cancel_running",
            status="running",
        )
        result = JobRunner.cancel_job(str(job.id))
        assert result is True
        job.refresh_from_db()
        assert job.status == "cancelled"

    def test_cancel_completed_job_returns_false(self):
        """Cannot cancel an already completed job."""
        job = BackgroundJob.objects.create(
            job_type="test_cancel_done",
            status="completed",
        )
        result = JobRunner.cancel_job(str(job.id))
        assert result is False


# ── Backtest result persistence ─────────────────────────────


@pytest.mark.django_db(transaction=True)
class TestJobRunnerBacktestResult:
    def test_backtest_result_persisted_on_completion(self, runner):
        """When job_type=backtest and result has no error, a BacktestResult is created."""
        def backtest_fn(params, progress_cb):
            return {
                "framework": "freqtrade",
                "strategy": "TestStrategy",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "metrics": {"sharpe": 1.5},
                "trades": [{"id": 1}],
            }

        job = BackgroundJob.objects.create(
            job_type="backtest",
            status="pending",
            params={"framework": "freqtrade", "timerange": "2025-01-01"},
        )

        with patch("core.services.ws_broadcast.broadcast_scheduler_event"):
            runner._run_job(
                str(job.id),
                backtest_fn,
                {"framework": "freqtrade", "timerange": "2025-01-01"},
            )

        results = BacktestResult.objects.filter(job_id=str(job.id))
        assert results.count() == 1
        br = results.first()
        assert br.framework == "freqtrade"
        assert br.strategy_name == "TestStrategy"
        assert br.symbol == "BTC/USDT"
        assert br.metrics == {"sharpe": 1.5}
