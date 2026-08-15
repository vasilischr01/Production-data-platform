from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "production_data_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)