from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "dropify",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.matching", "app.tasks.reports", "app.tasks.radar"],
)

# Make this the app that bare @shared_task binds to — without it, .delay()
# calls from the FastAPI process fall back to Celery's implicit default app
# (AMQP on localhost) and silently run inline instead of being queued.
celery_app.set_default()

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Warsaw",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=200,
    broker_connection_retry_on_startup=True,
    broker_connection_timeout=4,   # keep a failed producer publish short
    # Tests set CELERY_TASK_ALWAYS_EAGER=1 to run tasks in-process, no broker.
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=False,
)

celery_app.conf.beat_schedule = {
    "daily-summary": {
        "task": "app.tasks.reports.daily_summary",
        "schedule": crontab(hour=7, minute=0),
    },
    "referral-commissions": {
        "task": "app.tasks.reports.process_referral_commissions",
        "schedule": crontab(hour=3, minute=15),
    },
    "auto-release-milestones": {
        "task": "app.tasks.reports.auto_release_milestones",
        "schedule": crontab(minute="*/30"),
    },
    "process-payouts": {
        "task": "app.tasks.reports.process_payouts",
        "schedule": crontab(hour=4, minute=0),
    },
    "auto-complete-overdue": {
        "task": "app.tasks.reports.auto_complete_overdue",
        "schedule": crontab(hour=0, minute=30),
    },
    "portal-radar-scan": {
        "task": "app.tasks.radar.scan_all_sources",
        "schedule": crontab(minute=0, hour=f"*/{max(1, settings.RADAR_SCAN_INTERVAL_HOURS)}"),
    },
}
