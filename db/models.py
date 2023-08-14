from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy_utils.types.choice import ChoiceType


Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    is_staff = Column(Boolean, default=False)


class Chat(Base):
    __tablename__ = "chat"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    name = Column(String(64), index=True)
    link = Column(String(64), unique=True)


class StatusType(Enum):
    received = 0  # Принято - триггер сработал и данные формы были получены сервером
    sent = 1  # Отправлено - сервер успешно отправил в групповой чат сообщение
    error = -1  # Ошибка - при отправке сообщения произошла ошибка


StatusType.received.label = "получено"
StatusType.sent.label = "отправлено"
StatusType.error.label = "ошибка"


class Form(Base):
    __tablename__ = "form"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(ChoiceType(StatusType, impl=Integer()))
    content = Column(String)
    username = Column(String(64))
    destination = Column(String(64), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    telegram_message_id = Column(BigInteger, unique=True)
