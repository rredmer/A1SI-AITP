#!/usr/bin/env bash
set -euo pipefail
# Clean old background jobs, audit logs, and news articles
# Usage: bash scripts/clean_data.sh [days]
#        make clean-data
# Default: 30 days

DAYS=${1:-30}

echo "=== Data Cleanup (older than ${DAYS} days) ==="
docker compose exec -T backend python manage.py shell -c "
from django.utils import timezone
from datetime import timedelta
cutoff = timezone.now() - timedelta(days=${DAYS})

from analysis.models import BackgroundJob
from core.models import AuditLog
from market.models import NewsArticle

deleted_jobs = BackgroundJob.objects.filter(created_at__lt=cutoff, status__in=['completed', 'failed']).delete()
deleted_audit = AuditLog.objects.filter(created_at__lt=cutoff).delete()
deleted_news = NewsArticle.objects.filter(published_at__lt=cutoff).delete()
print(f'Cleaned: {deleted_jobs[0]} jobs, {deleted_audit[0]} audit logs, {deleted_news[0]} news articles')
"
echo "=== Cleanup complete ==="
