import logging
from typing import Any, List

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound

from src.utils.decorators import admin_authentication
from src.classes.pagination import Pagination

from db.models import Chat, User

router = Router()


@router.message(Command(commands=["start"]))
async def command_start(message: Message, db_session: sessionmaker):
    async with db_session() as session:
        user: User = await session.get(User, message.chat.id)
        additional_message = ""
        if user and user.is_staff:
            additional_message = "<b>Вы админ данного бота!\n</b>"

    await message.answer(
        f"""Привет!\nВаш айди: <b>{message.chat.id}</b>\n{additional_message}"""
    )


@router.message(Command(commands=["help"]))
@admin_authentication
async def command_last_report(message: Message, db_session: sessionmaker, **kwargs):
    await message.answer(
        "<b><em>Список всех команд</em></b>\n"
        "/admins - посмотреть ID админов \n"
        "/groups - посмотреть группы, где состоит бот \n"
        "/reports - интерфейс для просмотра последних отчетов (до 300-х отчетов) \n"
    )


@router.message(Command(commands=["admins"]))
@admin_authentication
async def command_check_admin(message: Message, db_session: sessionmaker, **kwargs):
    async with db_session() as session:
        rows = await session.execute(select(User).where(User.is_staff))
        admins = rows.scalars().all()
    msg = ["<em>Список админов</em>"]
    for ind, admin in enumerate(admins, start=1):
        msg.append(
            f"№{ind} Админ: <b>{admin.id}</b> {'<em>(Вы)</em>' if admin.id == message.chat.id else ''}"
        )
    await message.answer("\n".join(msg))


@router.message(Command(commands=["groups"]))
@admin_authentication
async def command_last_report(message: Message, db_session: sessionmaker, **kwargs):
    async with db_session() as session:
        rows = await session.execute(select(Chat))
        chats: List[Chat] = rows.scalars().all()
    msg = ["<em>Мои группы</em>"]
    for ind, chat in enumerate(chats, start=1):
        msg.append(f'№{ind} <a href="{chat.link}">{chat.name}</a>')
    await message.answer("\n".join(msg))


@router.message(Command(commands=["reports"]))
@admin_authentication
async def command_last_report(message: Message, db_session: sessionmaker, **kwargs):
    reports_pagination = Pagination(db_session)
    text, markup = await reports_pagination.show_page()
    await message.answer(
        text=text,
        reply_markup=markup,
    )


@router.message(F.new_chat_member | F.group_chat_created)
async def joined_chat_handler(
    message: Message, bot: Bot, db_session: sessionmaker
) -> Any:
    if hasattr(message, 'new_chat_member') and message.new_chat_member["id"] != bot.id:
        return

    chat_id = message.chat.id
    chat_title = message.chat.title
    if message.chat.type == "supergroup":
        chat_link = f"https://t.me/c/{str(chat_id)[4:]}"
    else:
        chat_link = f"https://t.me/c/{chat_id}"

    async with db_session() as session:
        await session.merge(Chat(id=chat_id, name=chat_title, link=chat_link))
        await session.commit()
    logging.warning(f"Зашёл в чат <{chat_title}> с айди: {chat_id}")


@router.message(F.left_chat_member)
async def left_chat_handler(
    message: Message, bot: Bot, db_session: sessionmaker
) -> Any:
    if hasattr(message, "left_chat_member") and message.left_chat_member.id != bot.id:
        return

    chat_id = message.chat.id
    chat_title = message.chat.title

    async with db_session() as session:
        try:
            row = await session.execute(select(Chat).where(Chat.id == chat_id))
            row = row.scalar_one()
            await session.delete(row)
            await session.commit()
            logging.warning(f"Покинул чат <{chat_title}> с айди: {chat_id}")
        except NoResultFound:
            logging.error(
                f"В базе данных нет информации о групповом чате <{chat_title}> с айди: {chat_id}, "
                f"пропускаем удаление информации о чате."
            )


@router.message(F.new_chat_title)
async def new_chat_handler(
    message: Message, bot: Bot, db_session: sessionmaker
) -> Any:

    chat_id = message.chat.id
    chat_title = message.chat.title

    async with db_session() as session:
        try:
            row = await session.execute(select(Chat).where(Chat.id == chat_id))
            chat = row.scalar_one()
            logging.warning(f"Группа <{chat.name}> с айди: {chat_id} поменяла название на <{message.new_chat_title}>")
            chat.name = message.new_chat_title
            await session.commit()
        except NoResultFound:
            logging.error(
                f"В базе данных нет информации о групповом чате с айди: {chat_id}, поменявшем название на "
                f"<{message.new_chat_title}>, странно, на всякий случай добавим эту группу в базу данных."
            )
            if message.chat.type == "supergroup":
                chat_link = f"https://t.me/c/{str(chat_id)[4:]}"
            else:
                chat_link = f"https://t.me/c/{chat_id}"
            await session.merge(Chat(id=chat_id, name=chat_title, link=chat_link))
            await session.commit()


@router.message(F.migrate_to_chat_id)
async def migration_to_supergroup_handler(message: Message, bot: Bot, db_session: sessionmaker):
    old_chat_id = message.chat.id
    new_chat_id = message.migrate_to_chat_id
    async with db_session() as session:
        try:
            chat = await session.get(Chat, old_chat_id)
            chat.id = new_chat_id
            logging.warning(f"Группа <{chat.name}> была повышена до супергруппы, её прошлый айди: {old_chat_id} теперь "
                            f"недействителен, меняем на новый айди: {new_chat_id}")
            await session.commit()
        except NoResultFound:
            logging.error(
                f"В базе данных нет информации об этом групповом чате <{chat.name}> с айди: {old_chat_id}, "
                f"странно, на всякий случай добавим эту группу в базу данных под новым айди: {new_chat_id}"
            )
            chat_link = f"https://t.me/c/{str(new_chat_id)[4:]}"
            await session.merge(Chat(id=new_chat_id, name=message.chat.title, link=chat_link))
            await session.commit()


@router.my_chat_member(F.new_chat_member.status == 'left')
async def another_left_chat_handler(chat_member: ChatMemberUpdated, bot: Bot, db_session: sessionmaker):
    if chat_member.new_chat_member.user.id != bot.id:
        return

    chat_id = chat_member.chat.id
    chat_title = chat_member.chat.title

    async with db_session() as session:
        try:
            row = await session.execute(select(Chat).where(Chat.id == chat_id))
            row = row.scalar_one()
            await session.delete(row)
            await session.commit()
            logging.warning(f"Покинул чат <{chat_title}> с айди: {chat_id}")
        except NoResultFound:
            logging.error(
                f"В базе данных нет информации о групповом чате <{chat_title}> с айди: {chat_id}, "
                f"пропускаем удаление информации о чате."
            )

