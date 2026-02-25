"""Tests for management commands."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from market.models import ExchangeConfig


@pytest.mark.django_db
class TestMigrateEnvCredentials:
    """Tests for the migrate_env_credentials management command."""

    @override_settings(
        EXCHANGE_ID="binance",
        EXCHANGE_API_KEY="test-key",
        EXCHANGE_API_SECRET="test-secret",
    )
    def test_migrate_creates_config(self):
        """Command should create ExchangeConfig when env vars are set."""
        out = StringIO()
        call_command("migrate_env_credentials", stdout=out)
        output = out.getvalue()

        assert "Created ExchangeConfig" in output
        config = ExchangeConfig.objects.get(exchange_id="binance")
        assert config.api_key == "test-key"
        assert config.api_secret == "test-secret"
        assert config.is_default is True

    @override_settings(
        EXCHANGE_ID="binance",
        EXCHANGE_API_KEY="test-key",
        EXCHANGE_API_SECRET="test-secret",
    )
    def test_migrate_skips_existing(self):
        """Command should skip if an ExchangeConfig with credentials already exists."""
        ExchangeConfig.objects.create(
            name="Existing",
            exchange_id="binance",
            api_key="existing-key",
            api_secret="existing-secret",
            is_active=True,
        )
        out = StringIO()
        call_command("migrate_env_credentials", stdout=out)
        output = out.getvalue()

        assert "already exists" in output
        assert ExchangeConfig.objects.filter(exchange_id="binance").count() == 1

    @override_settings(EXCHANGE_ID="binance", EXCHANGE_API_KEY="", EXCHANGE_API_SECRET="")
    def test_migrate_handles_missing_key(self):
        """Command should warn when no API key is configured."""
        out = StringIO()
        call_command("migrate_env_credentials", stdout=out)
        output = out.getvalue()

        assert "No EXCHANGE_API_KEY" in output
        assert ExchangeConfig.objects.filter(exchange_id="binance").count() == 0
