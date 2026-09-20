from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "leadpulse",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.workers.tasks.campaigns", "app.workers.tasks.enrichment"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    task_routes={
        "leadpulse.dispatch_email_action": {"queue": "outreach"},
        "leadpulse.queue_due_actions": {"queue": "maintenance"},
        "leadpulse.run_enrichment": {"queue": "enrichment"},
    },
    beat_schedule={
        "queue-due-outreach-actions": {
            "task": "leadpulse.queue_due_actions",
            "schedule": 30.0,
        }
    },
)
