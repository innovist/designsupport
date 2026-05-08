"""Celery application configuration for Design Support SaaS."""
import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('designsupport')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')


# Celery Beat schedule for periodic tasks
# Implements REQ-02-CRAWL-002: Scheduled crawling of active TrendSource entries
app.conf.beat_schedule = {
    # Crawl active trend sources every 6 hours
    'crawl-active-trend-sources': {
        'task': 'apps.trend_knowledge.infrastructure.tasks.crawl_active_sources',
        'schedule': timedelta(hours=6),  # Every 6 hours
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        },
    },
    # Alternative: Use crontab for specific times (e.g., 2 AM and 8 PM daily)
    # 'crawl-active-trend-sources': {
    #     'task': 'apps.trend_knowledge.infrastructure.tasks.crawl_active_sources',
    #     'schedule': crontab(hour='2,20', minute='0'),  # 2 AM and 8 PM UTC
    # },
}
