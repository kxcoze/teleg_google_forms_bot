import logging

from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound

from db.models import Chat, Form
from src.utils.form_parser import create_message_text
from src.utils.decorators import api_authentication
from src.config import config


@api_authentication
async def receive_form_data_handler(request: Request):
    """
    Консумер данных форм, которые приходят из Google Forms
    """
    bot: Bot = request.app["bot"]
    db_session: sessionmaker = request.app["db_session"]

    data = await request.post()

    create_message_text(data)
    project_name = data[config.PROJECT_FIELD].strip()
    username = data[config.USERNAME_FIELD].strip()
    msg = create_message_text(data)

    async with db_session() as session:
        try:
            row = await session.execute(
                select(Chat.id).where(Chat.name == project_name)
            )
            chat_id = row.scalar_one()
        except (
            NoResultFound
        ):  # Указана недействительная группа, либо же бот не добавлен в чат
            await session.merge(
                Form(
                    status=-1, username=username, destination=project_name, content=msg
                )
            )
            await session.commit()
            logging.error(
                f"Такой группы нет <{project_name}> для отправки сообщения пользователя {username}."
            )
            return json_response(
                {"ok": False, "err": f"There is no such group for sending messages."},
                status=400,
            )

        try:
            # Попытка отправить сообщение в чат
            sent_message = await bot.send_message(text=msg, chat_id=chat_id)
        except Exception as e:  # При попытке отправить в чат произошла ошибка
            await session.merge(
                Form(
                    status=-1, username=username, destination=project_name, content=msg
                )
            )
            await session.commit()
            logging.error(
                f"Не могу завершить отправку сообщения пользователя <{username}> из-за данной ошибки: {e}"
            )
            return json_response(
                {"ok": False, "err": f"Cannot complete the request because: {e}"},
                status=500,
            )
        # Сообщение успешно отправлено, фиксируем изменения
        await session.merge(
            Form(
                status=1,
                username=username,
                destination=project_name,
                content=msg,
                telegram_message_id=sent_message.message_id,
            )
        )
        await session.commit()
    logging.warning(
        f"Отчет пользователя <{username}> был успешно отправлен в <{project_name}>!"
    )
    return json_response({"ok": True}, status=200)

