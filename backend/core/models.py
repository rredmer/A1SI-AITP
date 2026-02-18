from django.db import models


class AuditLog(models.Model):
    user = models.CharField(max_length=150)
    action = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status_code = models.IntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at} {self.user} {self.action}"


class NotificationPreferences(models.Model):
    portfolio_id = models.IntegerField(unique=True)
    telegram_enabled = models.BooleanField(default=True)
    webhook_enabled = models.BooleanField(default=False)
    # Per-event toggles
    on_order_submitted = models.BooleanField(default=True)
    on_order_filled = models.BooleanField(default=True)
    on_order_cancelled = models.BooleanField(default=True)
    on_risk_halt = models.BooleanField(default=True)
    on_trade_rejected = models.BooleanField(default=True)
    on_daily_summary = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "notification preferences"

    def __str__(self):
        return f"NotificationPreferences(portfolio={self.portfolio_id})"
