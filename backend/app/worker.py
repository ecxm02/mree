from celery import Celery
from celery.schedules import crontab
import os
from .config import settings

# Initialize Celery app
celery_app = Celery(
    "mree_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_routes={
        'app.tasks.download_song': {'queue': 'downloads'},
        'app.tasks.process_audio': {'queue': 'processing'},
    },
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Connection retry settings for Celery 6.0+ compatibility
    broker_connection_retry_on_startup=settings.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
    broker_connection_retry=settings.CELERY_BROKER_CONNECTION_RETRY,
    broker_connection_max_retries=settings.CELERY_BROKER_CONNECTION_MAX_RETRIES,
    # Worker settings for better reliability
    worker_disable_rate_limits=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Celery Beat schedule for periodic tasks
    beat_schedule={
        'daily-backup': {
            'task': 'app.tasks.daily_backup',
            'schedule': crontab(hour=settings.BACKUP_SCHEDULE_HOUR, minute=0),
        },
        'cleanup-failed-downloads': {
            'task': 'app.tasks.cleanup_failed_downloads',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
        },
    },
)

# Add image cleanup schedule if enabled
if settings.IMAGE_CLEANUP_ENABLED:
    celery_app.conf.beat_schedule['cleanup-unused-images'] = {
        'task': 'app.tasks.cleanup_unused_images',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    }

# Add metrics update schedule if enabled
if settings.METRICS_ENABLED:
    celery_app.conf.beat_schedule['update-metrics'] = {
        'task': 'app.tasks.update_metrics',
        'schedule': settings.METRICS_UPDATE_INTERVAL,  # Every X seconds from config
    }

# Optional: Configure result expiration
celery_app.conf.result_expires = 3600  # Results expire after 1 hour
