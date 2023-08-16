import logging.config
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings
from aiogram import Bot, Dispatcher, Router
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool


class Config(BaseSettings):
    BOT_TOKEN: str = Field(...)
    TELEGRAM_SECURITY_TOKEN: str = Field(...)
    GOOGLE_SECURITY_TOKEN: str = Field(...)
    ADMIN_IDS: List = Field(...)
    EMAIL: str = Field(...)
    DB_NAME: str = Field(...)
    APP_BASE_URL: str = Field(...)
    PROJECT_FIELD: str = Field(...)
    USERNAME_FIELD: str = Field(...)
    EXPIRES_DAYS: int = Field(...)
    RABBITMQ_USER: str = Field(...)
    RABBITMQ_PASS: str = Field(...)
    RABBITMQ_VHOST: str = Field(...)

    @property
    def RABBITMQ_URL(self):
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@rabbitmq:5672/{self.RABBITMQ_VHOST}"


config = Config(_env_file=".env", _env_file_encoding="utf-8")

engine = create_async_engine(
    f"sqlite+aiosqlite:///./{config.DB_NAME}.sqlite3",
    future=True,
    poolclass=NullPool,
)
async_sessionmaker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dispatcher = Dispatcher()

logging_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "file_formatter": {
            "format": "{asctime} — {levelname} — {name} — {module}:{funcName}:{lineno} — {message}",
            "datefmt": "[%d/%m/%Y] — %H:%M:%S",
            "style": "{",
        },
        "console_formatter": {
            "format": "{asctime} — {levelname} — {name} — {message}",
            "datefmt": "[%d/%m/%Y] — %H:%M",
            "style": "{",
        },
        "telegram_formatter": {
            "format": "{levelname} — {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console_formatter",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "server.log",
            "formatter": "file_formatter",
        },
        "telegram": {
            "level": "WARNING",
            "class": "aiolog.telegram.Handler",
            "formatter": "telegram_formatter",
            "timeout": 10,  # 60 by default
            "queue_size": 100,  # 1000 by default
            "token": config.BOT_TOKEN,
            "chats": ", ".join([str(e) for e in config.ADMIN_IDS]),
        },
    },
    "loggers": {
        "app_logger": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file", "telegram"],
    },
}
logging.config.dictConfig(logging_dict)
