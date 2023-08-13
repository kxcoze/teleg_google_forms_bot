import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.worker.celery import celery_app as app
from src.worker.celery import celery_event_loop
from src.config import bot, async_sessionmaker as db_session
from db.models import Form, Chat


async def send_not_delivered_messages():
    logging.info('Doing some business here...')
    async with db_session() as session:
        rows_msg = await session.execute(select(Form).where(Form.status.in_((-1, 0))))
        messages = rows_msg.scalars().all()
        for message in messages:
            await asyncio.sleep(2)
            try:
                row_chat_id = await session.execute(
                    select(Chat.id).where(Chat.name == message.destination))
                chat_id = row_chat_id.scalar_one()
            except NoResultFound:  # Указана недействительная группа, либо же бот не добавлен в чат
                logging.error(
                    f"There is still no such group with name <{message.destination}> so message with id: {message.id} "
                    f"cannot be sent!")
                continue
            try:
                sent_message = await bot.send_message(text=message.content, chat_id=chat_id)
            except Exception as e:  # При попытке отправить в чат произошла ошибка
                logging.error(f"Cannot complete messaging to group with name <{message.destination}> for message with "
                              f"id:{message.id} because: {e}")
                continue

            # Сообщение успешно отправлено.
            message.status = 1
            message.telegram_message_id = sent_message.message_id
            await session.merge(message)
            await session.commit()
            logging.warning(
                f"Message with id: {message.id} has been successfully sent to the group <{message.destination}>")

    logging.info('Work has been ended.')


@app.task
def test_task() -> None:
    celery_event_loop.run_until_complete(send_not_delivered_messages())