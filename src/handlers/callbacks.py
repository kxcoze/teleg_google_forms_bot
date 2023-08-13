import typing
import logging
from contextlib import suppress

from aiogram import types, Dispatcher
from aiogram.filters.exception import ExceptionMessageFilter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from src.config import async_sessionmaker
from src.classes.pagination import Pagination


async def query_show_initial_page(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str], **kwargs
):
    cur_page: int = callback_data["page_num"]
    reports_pagination = Pagination(async_sessionmaker)
    text, markup = await reports_pagination.show_page(cur_page)
    await query.message.edit_text(
        text=text,
        reply_markup=markup,
    )
    await query.answer()


async def query_show_report_info(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str], **kwargs
):
    cur_page: int = callback_data["page_num"]
    report_id: int = callback_data["id"]
    user_book = Pagination(async_sessionmaker)

    try:
        text, markup = await user_book.view_data_element(cur_page, report_id)
        with suppress(ExceptionMessageFilter('MessageNotModified')):
            await query.message.edit_text(text, reply_markup=markup)
        await query.answer()
    except:
        logging.exception(
            "Something went wrong with showing link"
            f"user ID:[{query.message.chat.id}]"
        )
        await query.answer("Произошла непредвиденная ошибка.")
