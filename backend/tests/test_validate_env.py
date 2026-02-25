"""Tests for the validate_env management command."""

import os
from unittest.mock import patch

import pytest
from django.core.management import call_command


@pytest.mark.django_db
class TestValidateEnvCommand:
    def test_passes_when_all_set(self, capsys):
        env = {
            "DJANGO_SECRET_KEY": "test-secret-key-value",
            "DJANGO_ENCRYPTION_KEY": "test-encryption-key-value",
            "EXCHANGE_API_KEY": "test-api-key",
            "NEWSAPI_KEY": "test-news-key",
            "BACKUP_ENCRYPTION_KEY": "test-backup-key",
            "TELEGRAM_BOT_TOKEN": "test-telegram-token",
        }
        with patch.dict(os.environ, env):
            call_command("validate_env")

    def test_fails_when_required_missing(self):
        modified_env = os.environ.copy()
        modified_env.pop("DJANGO_SECRET_KEY", None)
        modified_env.pop("DJANGO_ENCRYPTION_KEY", None)
        with patch.dict(os.environ, modified_env, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                call_command("validate_env")
            assert exc_info.value.code == 1

    def test_warns_on_recommended_missing(self, capsys):
        env = {
            "DJANGO_SECRET_KEY": "test-secret-key-value",
            "DJANGO_ENCRYPTION_KEY": "test-encryption-key-value",
        }
        modified_env = os.environ.copy()
        modified_env.update(env)
        # Remove recommended keys
        for k in ("EXCHANGE_API_KEY", "NEWSAPI_KEY", "BACKUP_ENCRYPTION_KEY", "TELEGRAM_BOT_TOKEN"):
            modified_env.pop(k, None)
        with patch.dict(os.environ, modified_env, clear=True):
            call_command("validate_env")
            captured = capsys.readouterr()
            assert "RECOMMENDED" in captured.err

    def test_reports_all_missing_vars(self, capsys):
        modified_env = os.environ.copy()
        modified_env.pop("DJANGO_SECRET_KEY", None)
        modified_env.pop("DJANGO_ENCRYPTION_KEY", None)
        with patch.dict(os.environ, modified_env, clear=True):
            with pytest.raises(SystemExit):
                call_command("validate_env")
            captured = capsys.readouterr()
            assert "DJANGO_SECRET_KEY" in captured.err
            assert "DJANGO_ENCRYPTION_KEY" in captured.err

    def test_rejects_changeme_placeholder(self, capsys):
        env = {
            "DJANGO_SECRET_KEY": "changeme",
            "DJANGO_ENCRYPTION_KEY": "test-encryption-key-value",
        }
        with patch.dict(os.environ, env):
            with pytest.raises(SystemExit) as exc_info:
                call_command("validate_env")
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "DJANGO_SECRET_KEY" in captured.err

    def test_rejects_placeholder_secret_key(self, capsys):
        env = {
            "DJANGO_SECRET_KEY": "your-secret-key-here",
            "DJANGO_ENCRYPTION_KEY": "test-encryption-key-value",
        }
        with patch.dict(os.environ, env):
            with pytest.raises(SystemExit) as exc_info:
                call_command("validate_env")
            assert exc_info.value.code == 1
