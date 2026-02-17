from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    settings.PROJECT_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Basic, safe defaults for the skeleton
celery.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"]) 
