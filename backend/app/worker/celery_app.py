from celery import Celery

from ..core.config import get_settings
from ..core.logging_config import (
    configure_logging,
)


settings = get_settings()

configure_logging(settings.log_level)

celery_app = Celery(
    "automation_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.app.worker.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_deduplicate_successful_tasks=True,
    worker_hijack_root_logger=False,
)