import asyncio

from celery import Celery, signals
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
    "add-every-minute": {
        "task": "src.worker.tasks.test_task",
        "schedule": crontab(),
    },
}
celery_app.conf.update(timezone="Europe/Moscow")
