from rest_framework import serializers

from core.models import AuditLog, NotificationPreferences


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreferences
        fields = [
            "portfolio_id",
            "telegram_enabled",
            "webhook_enabled",
            "on_order_submitted",
            "on_order_filled",
            "on_order_cancelled",
            "on_risk_halt",
            "on_trade_rejected",
            "on_daily_summary",
        ]
        read_only_fields = ["portfolio_id"]
