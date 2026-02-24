"""Tests for workflow models (Workflow, WorkflowStep, WorkflowRun, WorkflowStepRun)."""

import pytest
from django.db import IntegrityError

from analysis.models import (
    BackgroundJob,
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepRun,
)


@pytest.mark.django_db
class TestWorkflowModel:
    def test_create_workflow(self):
        wf = Workflow.objects.create(
            id="test_pipeline",
            name="Test Pipeline",
            description="A test workflow",
            asset_class="crypto",
        )
        assert wf.id == "test_pipeline"
        assert wf.is_active is True
        assert wf.is_template is False
        assert wf.run_count == 0

    def test_workflow_str(self):
        wf = Workflow(id="test", name="Test")
        assert "Test" in str(wf)

    def test_workflow_default_params(self):
        wf = Workflow.objects.create(id="defaults", name="Defaults")
        assert wf.params == {}
        assert wf.schedule_enabled is False


@pytest.mark.django_db
class TestWorkflowStepModel:
    def test_create_step(self):
        wf = Workflow.objects.create(id="step_test", name="Step Test")
        step = WorkflowStep.objects.create(
            workflow=wf,
            order=1,
            name="Data Refresh",
            step_type="data_refresh",
        )
        assert step.order == 1
        assert step.timeout_seconds == 300

    def test_step_unique_order(self):
        wf = Workflow.objects.create(id="unique_test", name="Unique Test")
        WorkflowStep.objects.create(workflow=wf, order=1, name="Step 1", step_type="data_refresh")
        with pytest.raises(IntegrityError):
            WorkflowStep.objects.create(
                workflow=wf, order=1, name="Step 1b",
                step_type="news_fetch",
            )

    def test_steps_ordered(self):
        wf = Workflow.objects.create(id="order_test", name="Order Test")
        WorkflowStep.objects.create(workflow=wf, order=3, name="Third", step_type="alert_evaluate")
        WorkflowStep.objects.create(workflow=wf, order=1, name="First", step_type="data_refresh")
        WorkflowStep.objects.create(
            workflow=wf, order=2, name="Second", step_type="regime_detection",
        )
        steps = list(wf.steps.values_list("name", flat=True))
        assert steps == ["First", "Second", "Third"]


@pytest.mark.django_db
class TestWorkflowRunModel:
    def test_create_run(self):
        wf = Workflow.objects.create(id="run_test", name="Run Test")
        run = WorkflowRun.objects.create(workflow=wf, trigger="manual")
        assert run.status == "pending"
        assert run.current_step == 0

    def test_run_with_job(self):
        wf = Workflow.objects.create(id="job_test", name="Job Test")
        job = BackgroundJob.objects.create(job_type="workflow_job_test")
        run = WorkflowRun.objects.create(workflow=wf, job=job)
        assert run.job.id == job.id

    def test_run_str(self):
        wf = Workflow.objects.create(id="str_test", name="Str")
        run = WorkflowRun(id="abcdefgh-1234", workflow=wf, status="running")
        assert "running" in str(run)


@pytest.mark.django_db
class TestWorkflowStepRunModel:
    def test_create_step_run(self):
        wf = Workflow.objects.create(id="sr_test", name="SR Test")
        step = WorkflowStep.objects.create(
            workflow=wf, order=1, name="S1", step_type="data_refresh",
        )
        run = WorkflowRun.objects.create(workflow=wf)
        sr = WorkflowStepRun.objects.create(workflow_run=run, step=step, order=1)
        assert sr.status == "pending"
        assert sr.condition_met is True

    def test_step_run_result(self):
        wf = Workflow.objects.create(id="result_test", name="Result")
        step = WorkflowStep.objects.create(workflow=wf, order=1, name="S1", step_type="news_fetch")
        run = WorkflowRun.objects.create(workflow=wf)
        sr = WorkflowStepRun.objects.create(
            workflow_run=run, step=step, order=1,
            status="completed", result={"articles": 5},
        )
        assert sr.result["articles"] == 5
