import asyncio

from celery import Celery
from celery.schedules import crontab

from src.config import config

celery_event_loop = asyncio.new_event_loop()

celery_app = Celery(
    main="telegram_bot",
    broker=config.RABBITMQ_URL,
    broker_connection_retry_on_startup=True,
)
celery_app.autodiscover_tasks()
celery_app.conf.beat_schedule = {
    "add-every-15-minutes": {
        "task": "src.worker.tasks.test_task",
        "schedule": crontab(minute="*/15", hour="6-23"),
    },
    "add-every-monday-clear-old-reports": {
        "task": "src.worker.tasks.clear_old_forms_task",
        "schedule": crontab(minute="0", hour="0", day_of_week="1"),
    },
}
celery_app.conf.update(timezone=config.TIMEZONE)
