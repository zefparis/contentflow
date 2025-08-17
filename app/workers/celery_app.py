from __future__ import annotations
import os
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "contentflow",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

# Autodiscover tasks in app.workers package
celery_app.autodiscover_tasks(["app.workers"])  # expects modules with @celery_app.task

@celery_app.task
def ping() -> str:
    return "pong"
