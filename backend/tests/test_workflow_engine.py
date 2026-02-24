"""Tests for the workflow engine (analysis/services/workflow_engine.py)."""

from unittest.mock import MagicMock, patch

import pytest

from analysis.models import (
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepRun,
)
from analysis.services.workflow_engine import (
    WorkflowEngine,
    _evaluate_condition,
    execute_workflow,
)


class TestEvaluateCondition:
    def test_empty_condition_returns_true(self):
        assert _evaluate_condition("", {}) is True

    def test_none_condition_returns_true(self):
        assert _evaluate_condition(None, {}) is True

    def test_string_equality(self):
        assert _evaluate_condition('result.status == "completed"', {"status": "completed"}) is True

    def test_string_inequality(self):
        assert _evaluate_condition('result.status == "completed"', {"status": "failed"}) is False

    def test_numeric_greater_than(self):
        assert _evaluate_condition("result.score > 0.5", {"score": 0.8}) is True
        assert _evaluate_condition("result.score > 0.5", {"score": 0.3}) is False

    def test_numeric_less_than(self):
        assert _evaluate_condition("result.count < 10", {"count": 5}) is True

    def test_numeric_equality(self):
        assert _evaluate_condition("result.value == 0", {"value": 0}) is True

    def test_not_equal(self):
        assert _evaluate_condition('result.status != "error"', {"status": "completed"}) is True

    def test_greater_equal(self):
        assert _evaluate_condition("result.score >= 0.5", {"score": 0.5}) is True

    def test_less_equal(self):
        assert _evaluate_condition("result.count <= 3", {"count": 3}) is True

    def test_missing_field_returns_false(self):
        assert _evaluate_condition('result.missing == "x"', {}) is False

    def test_invalid_syntax_returns_true(self):
        assert _evaluate_condition("invalid condition", {}) is True


@pytest.mark.django_db
class TestWorkflowEngine:
    def _create_workflow_with_steps(self, wf_id="test_wf", steps=None):
        wf = Workflow.objects.create(id=wf_id, name="Test WF")
        if steps is None:
            steps = [
                {"order": 1, "name": "Step 1", "step_type": "sentiment_aggregate"},
                {"order": 2, "name": "Step 2", "step_type": "alert_evaluate"},
            ]
        for s in steps:
            WorkflowStep.objects.create(workflow=wf, **s)
        return wf

    @patch("analysis.services.step_registry.STEP_REGISTRY", {
        "sentiment_aggregate": lambda p, cb: {"status": "completed", "signal": 0.5},
        "alert_evaluate": lambda p, cb: {"status": "completed", "alerts_triggered": 0},
    })
    def test_trigger_creates_run_and_job(self):
        wf = self._create_workflow_with_steps()
        run_id, job_id = WorkflowEngine.trigger(wf.id)
        assert run_id
        assert job_id
        run = WorkflowRun.objects.get(id=run_id)
        assert run.status == "pending"
        assert run.total_steps == 2

    def test_trigger_empty_workflow_raises(self):
        wf = Workflow.objects.create(id="empty", name="Empty")
        with pytest.raises(ValueError, match="no steps"):
            WorkflowEngine.trigger(wf.id)

    @patch("analysis.services.step_registry.STEP_REGISTRY", {
        "sentiment_aggregate": lambda p, cb: {"status": "completed", "signal": 0.5},
        "alert_evaluate": lambda p, cb: {"status": "completed", "alerts_triggered": 0},
    })
    def test_execute_workflow_success(self):
        wf = self._create_workflow_with_steps("exec_test")
        run = WorkflowRun.objects.create(workflow=wf, total_steps=2)
        steps = list(wf.steps.order_by("order"))
        for s in steps:
            WorkflowStepRun.objects.create(workflow_run=run, step=s, order=s.order)

        step_info = [
            {"step_id": s.id, "order": s.order, "name": s.name,
             "step_type": s.step_type, "params": {}, "condition": "", "timeout_seconds": 300}
            for s in steps
        ]

        result = execute_workflow(
            {"workflow_run_id": str(run.id), "steps": step_info},
            lambda p, m: None,
        )
        assert result["status"] == "completed"
        assert result["completed_steps"] == 2

        run.refresh_from_db()
        assert run.status == "completed"

    @patch("analysis.services.step_registry.STEP_REGISTRY", {
        "data_refresh": lambda p, cb: {"status": "completed"},
        "failing_step": MagicMock(side_effect=RuntimeError("boom")),
    })
    def test_execute_workflow_step_failure(self):
        wf = Workflow.objects.create(id="fail_test", name="Fail Test")
        WorkflowStep.objects.create(workflow=wf, order=1, name="OK", step_type="data_refresh")
        WorkflowStep.objects.create(workflow=wf, order=2, name="Fail", step_type="failing_step")

        run = WorkflowRun.objects.create(workflow=wf, total_steps=2)
        steps = list(wf.steps.order_by("order"))
        for s in steps:
            WorkflowStepRun.objects.create(workflow_run=run, step=s, order=s.order)

        step_info = [
            {"step_id": s.id, "order": s.order, "name": s.name,
             "step_type": s.step_type, "params": {}, "condition": "", "timeout_seconds": 300}
            for s in steps
        ]

        result = execute_workflow(
            {"workflow_run_id": str(run.id), "steps": step_info},
            lambda p, m: None,
        )
        assert result["status"] == "error"
        assert result["failed_step"] == 2

        run.refresh_from_db()
        assert run.status == "failed"

    @patch("analysis.services.step_registry.STEP_REGISTRY", {
        "data_refresh": lambda p, cb: {"status": "completed"},
        "alert_evaluate": lambda p, cb: {"status": "completed", "alerts": []},
    })
    def test_execute_workflow_condition_skip(self):
        wf = Workflow.objects.create(id="cond_test", name="Cond Test")
        WorkflowStep.objects.create(
            workflow=wf, order=1, name="Refresh", step_type="data_refresh",
        )
        WorkflowStep.objects.create(
            workflow=wf, order=2, name="Alert", step_type="alert_evaluate",
            condition='result.status == "error"',  # Won't match "completed"
        )

        run = WorkflowRun.objects.create(workflow=wf, total_steps=2)
        steps = list(wf.steps.order_by("order"))
        for s in steps:
            WorkflowStepRun.objects.create(workflow_run=run, step=s, order=s.order)

        step_info = [
            {"step_id": s.id, "order": s.order, "name": s.name,
             "step_type": s.step_type, "params": s.params, "condition": s.condition,
             "timeout_seconds": s.timeout_seconds}
            for s in steps
        ]

        result = execute_workflow(
            {"workflow_run_id": str(run.id), "steps": step_info},
            lambda p, m: None,
        )
        assert result["status"] == "completed"
        # Only 1 step completed (the other was skipped)
        assert result["completed_steps"] == 1

        step_runs = list(WorkflowStepRun.objects.filter(workflow_run=run).order_by("order"))
        assert step_runs[0].status == "completed"
        assert step_runs[1].status == "skipped"

    @patch("analysis.services.step_registry.STEP_REGISTRY", {
        "data_refresh": lambda p, cb: {"status": "completed", "count": 5},
        "alert_evaluate": lambda p, cb: {
            "status": "completed",
            "prev_count": p.get("_prev_result", {}).get("count", 0),
        },
    })
    def test_execute_workflow_passes_prev_result(self):
        wf = Workflow.objects.create(id="prev_test", name="Prev Test")
        WorkflowStep.objects.create(workflow=wf, order=1, name="Refresh", step_type="data_refresh")
        WorkflowStep.objects.create(workflow=wf, order=2, name="Alert", step_type="alert_evaluate")

        run = WorkflowRun.objects.create(workflow=wf, total_steps=2)
        steps = list(wf.steps.order_by("order"))
        for s in steps:
            WorkflowStepRun.objects.create(workflow_run=run, step=s, order=s.order)

        step_info = [
            {"step_id": s.id, "order": s.order, "name": s.name,
             "step_type": s.step_type, "params": {}, "condition": "", "timeout_seconds": 300}
            for s in steps
        ]

        result = execute_workflow(
            {"workflow_run_id": str(run.id), "steps": step_info},
            lambda p, m: None,
        )
        assert result["status"] == "completed"
        # The second step should have received the first step's result
        step2_run = WorkflowStepRun.objects.get(workflow_run=run, order=2)
        assert step2_run.result["prev_count"] == 5

    @patch("analysis.services.step_registry.STEP_REGISTRY", {})
    def test_execute_unknown_step_type_fails(self):
        wf = Workflow.objects.create(id="unknown_test", name="Unknown")
        WorkflowStep.objects.create(workflow=wf, order=1, name="Bad", step_type="nonexistent")

        run = WorkflowRun.objects.create(workflow=wf, total_steps=1)
        step = wf.steps.first()
        WorkflowStepRun.objects.create(workflow_run=run, step=step, order=1)

        result = execute_workflow(
            {"workflow_run_id": str(run.id), "steps": [
                {"step_id": step.id, "order": 1, "name": "Bad", "step_type": "nonexistent",
                 "params": {}, "condition": "", "timeout_seconds": 300},
            ]},
            lambda p, m: None,
        )
        assert result["status"] == "error"
        assert "Unknown step type" in result["error"]

    def test_cancel_running_workflow(self):
        wf = Workflow.objects.create(id="cancel_test", name="Cancel")
        run = WorkflowRun.objects.create(workflow=wf, status="running")
        assert WorkflowEngine.cancel(str(run.id)) is True
        run.refresh_from_db()
        assert run.status == "cancelled"

    def test_cancel_completed_workflow_fails(self):
        wf = Workflow.objects.create(id="cancel_done", name="Done")
        run = WorkflowRun.objects.create(workflow=wf, status="completed")
        assert WorkflowEngine.cancel(str(run.id)) is False

    def test_cancel_nonexistent_returns_false(self):
        assert WorkflowEngine.cancel("nonexistent-id") is False
