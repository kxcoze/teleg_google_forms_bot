import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.worker.celery import celery_app as app
from src.worker.celery import celery_event_loop
from src.config import bot, config, async_sessionmaker as db_session
from db.models import Form, Chat


async def send_error_message_admins(msg):
    msg = ''.join(['<code>ERROR — </code>', msg])
    for admin in config.ADMIN_IDS:
        await bot.send_message(admin, msg)


async def send_not_delivered_messages():
    async with db_session() as session:
        rows_msg = await session.execute(select(Form).where(Form.status.in_((-1, 0))))
        forms = rows_msg.scalars().all()
        for form in forms:
            try:
                row_chat_id = await session.execute(
                    select(Chat.id).where(Chat.name == form.destination)
                )
                chat_id = row_chat_id.scalar_one()
            except (
                NoResultFound
            ):  # Указана недействительная группа, либо же бот не добавлен в чат
                await send_error_message_admins(
                    f"При отправке отчета <b>{form.username}</b> произошла ошибка! \n"
                    f"Бот не добавлен в групповой чат <b>{form.destination}</b> \n"
                    f"Проверьте список групп бота с помощью команды: /groups \n"
                )
                logging.error(
                    f"There is still no such group with name <{form.destination}> so message with id: {form.id} "
                    f"cannot be sent!"
                )
                continue

            try:
                sent_message = await bot.send_message(
                    text=form.content, chat_id=chat_id
                )
                await asyncio.sleep(2)
            except Exception as e:  # При попытке отправить в чат произошла ошибка
                await send_error_message_admins(
                    f"При попытке отправить отчет <b>{form.username}</b>, в чат <b>{form.destination}</b> "
                    f"произошла ошибка! \nВот текст ошибки: {e} \n"
                )
                logging.error(
                    f"Cannot complete messaging to group with name <{form.destination}> for message with "
                    f"id:{form.id} because: {e}"
                )
                continue

            # Сообщение успешно отправлено.
            form.status = 1
            form.telegram_message_id = sent_message.message_id
            await session.merge(form)
            await session.commit()
            await send_error_message_admins(
                f"Отчет <b>{form.username}</b> был успешно отправлен в чат <b>{form.destination}</b>! \n"
            )
            logging.warning(
                f"Message with id: {form.id} has been successfully sent to the group <{form.destination}>"
            )


@app.task
def test_task() -> None:
    celery_event_loop.run_until_complete(send_not_delivered_messages())
