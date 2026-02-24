import uuid

from django.db import models

from market.constants import AssetClass


class BackgroundJob(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    job_type = models.CharField(max_length=50, db_index=True)
    status = models.CharField(max_length=20, default="pending", db_index=True)
    progress = models.FloatField(default=0.0)
    progress_message = models.CharField(max_length=200, default="", blank=True)
    params = models.JSONField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job({self.id[:8]}... {self.job_type} {self.status})"


class BacktestResult(models.Model):
    job = models.ForeignKey(
        BackgroundJob,
        on_delete=models.CASCADE,
        related_name="backtest_results",
    )
    framework = models.CharField(max_length=20)
    asset_class = models.CharField(
        max_length=10,
        choices=AssetClass.choices,
        default=AssetClass.CRYPTO,
    )
    strategy_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10)
    timerange = models.CharField(max_length=50, default="", blank=True)
    metrics = models.JSONField(null=True, blank=True)
    trades = models.JSONField(null=True, blank=True)
    config = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Backtest({self.strategy_name} {self.symbol} {self.timeframe})"


# ── Workflow models ──────────────────────────────────────────


class Workflow(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(default="", blank=True)
    asset_class = models.CharField(
        max_length=10,
        choices=AssetClass.choices,
        default=AssetClass.CRYPTO,
    )
    is_template = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    schedule_interval_seconds = models.IntegerField(null=True, blank=True)
    schedule_enabled = models.BooleanField(default=False)
    params = models.JSONField(default=dict, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    run_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Workflow({self.id}: {self.name})"


class WorkflowStep(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="steps")
    order = models.IntegerField()
    name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=50)
    params = models.JSONField(default=dict, blank=True)
    condition = models.CharField(max_length=200, default="", blank=True)
    timeout_seconds = models.IntegerField(default=300)

    class Meta:
        ordering = ["order"]
        unique_together = [("workflow", "order")]

    def __str__(self):
        return f"Step({self.workflow_id}/{self.order}: {self.name})"


class WorkflowRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    TRIGGER_CHOICES = [
        ("manual", "Manual"),
        ("scheduled", "Scheduled"),
        ("api", "API"),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="runs")
    job = models.OneToOneField(
        BackgroundJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_run",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default="manual")
    params = models.JSONField(default=dict, blank=True)
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"WorkflowRun({self.id[:8]}... {self.workflow_id} {self.status})"


class WorkflowStepRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    workflow_run = models.ForeignKey(
        WorkflowRun, on_delete=models.CASCADE, related_name="step_runs",
    )
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name="runs")
    order = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    input_data = models.JSONField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    condition_met = models.BooleanField(default=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"StepRun({self.workflow_run_id[:8]}... step {self.order} {self.status})"


class ScreenResult(models.Model):
    job = models.ForeignKey(BackgroundJob, on_delete=models.CASCADE, related_name="screen_results")
    symbol = models.CharField(max_length=20)
    asset_class = models.CharField(
        max_length=10,
        choices=AssetClass.choices,
        default=AssetClass.CRYPTO,
    )
    timeframe = models.CharField(max_length=10)
    strategy_name = models.CharField(max_length=50)
    top_results = models.JSONField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)
    total_combinations = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Screen({self.strategy_name} {self.symbol} {self.timeframe})"
