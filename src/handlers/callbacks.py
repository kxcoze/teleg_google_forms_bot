import typing
import logging
from contextlib import suppress

from aiogram import Router, types, F, Bot
from aiogram.filters.exception import ExceptionMessageFilter

from src.config import async_sessionmaker
from src.classes.pagination import Pagination, FormCallbackData

callback_router = Router()


@callback_router.callback_query(
    FormCallbackData.filter(F.action.in_({"prev", "main", "next"}))
)
async def query_show_initial_page(
    query: types.CallbackQuery, callback_data: FormCallbackData, bot: Bot, **kwargs
):
    cur_page: int = callback_data.page_num
    reports_pagination = Pagination(async_sessionmaker)
    text, markup = await reports_pagination.show_page(cur_page)
    await query.message.edit_text(
        text=text,
        reply_markup=markup,
    )
    await query.answer()


@callback_router.callback_query(FormCallbackData.filter(F.action == "view"))
async def query_show_report_info(
    query: types.CallbackQuery, callback_data: FormCallbackData, bot: Bot, **kwargs
):
    cur_page: int = callback_data.page_num
    form_id: int = callback_data.form_id
    pos: int = callback_data.pos
    user_book = Pagination(async_sessionmaker)

    try:
        text, markup = await user_book.view_data_element(cur_page, form_id, pos)
        with suppress(ExceptionMessageFilter("MessageNotModified")):
            await query.message.edit_text(text, reply_markup=markup)
        await query.answer()
    except:
        logging.exception(
            "Something went wrong with showing report info"
            f"user ID:[{query.message.chat.id}]"
        )
        await query.answer("Произошла непредвиденная ошибка.")
