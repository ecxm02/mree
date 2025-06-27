from celery import Celery
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
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Optional: Configure result expiration
celery_app.conf.result_expires = 3600  # Results expire after 1 hour
