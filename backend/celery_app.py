"""
Celery configuration for the Audio Drama FX Engine
"""

from celery import Celery
from .config import settings

# Create Celery app
celery_app = Celery(
    "audio_drama_fx",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.tasks.audio_processing",
        "backend.tasks.whisperx_tasks",
        "backend.tasks.effects_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "backend.tasks.audio_processing.*": {"queue": "audio_processing"},
        "backend.tasks.whisperx_tasks.*": {"queue": "whisperx"},
        "backend.tasks.effects_tasks.*": {"queue": "effects"},
    },
    task_annotations={
        "*": {"rate_limit": "10/s"},
        "backend.tasks.audio_processing.process_audio_file": {"rate_limit": "2/s"},
    },
)

# Optional configuration for development
if settings.environment == "development":
    celery_app.conf.update(
        task_always_eager=False,  # Set to True for testing
        task_eager_propagates=True,
    )
