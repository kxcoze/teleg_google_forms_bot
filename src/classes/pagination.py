import re
from typing import List

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from async_property import async_property
from sqlalchemy import select

from db.models import User, Form


class ListCallbackData(CallbackData, prefix="page"):
    name: str
    id: str | int
    page_num: int
    action: str
    # page:<name>:<id>:<page_num>:<action>


class Pagination:
    WIDTH = 5

    def __init__(self, db_session):
        self.db_session = db_session

    async def search_nonempty_page(self, left, right, cur_page=0):
        searched_page = cur_page
        pages = (await self.pages)[left:right]
        while searched_page > 0 and pages:
            right -= self.WIDTH
            left -= self.WIDTH
            searched_page -= 1

        return left, right, searched_page

    async def check_existing_data(self, checked_data: List, ind):
        last_index = -1
        pages = await self.pages
        for index, data in enumerate(pages):
            if data == checked_data:
                if index == ind:
                    return ind
                last_index = index

        return last_index

    @async_property
    async def pages(self):
        async with self.db_session() as session:
            rows = await session.execute(select(Form)
                                         .where(Form.status == 1)
                                         .order_by(Form.created_at.desc())
                                         .limit(300)
                                         )
            forms: List[Form] = rows.scalars().all()
        return forms

    # @abstractmethod
    # async def append_data(self, data1, data2, pos=0):
    #     pass

    async def show_page(self, cur_page=0):

        menu = []
        left = cur_page * self.WIDTH
        right = cur_page * self.WIDTH + self.WIDTH
        pages = (await self.pages)[left:right]
        if not pages:
            left, right, cur_page = await self.search_nonempty_page(
                left, right, cur_page
            )
        if cur_page > 0:
            # Added button for back listing
            menu.append(
                types.InlineKeyboardButton(
                    text="«",
                    callback_data=ListCallbackData(
                        name="reports", id="-", page_num=cur_page - 1, action="prev"
                    ).pack(),
                )
            )
        pages = await self.pages
        if pages:
            text = "<b>Отчеты</b>\n"
            reports = pages[left:right]
            for ind, form in enumerate(reports, start=left + 1):
                text += (
                    f"№ {ind}\n"
                    f"ФИО: <b>{form.username}</b>\n"
                    f"Проект: <b>{form.destination}</b>\n"
                    f"Отметка времени: <b>{form.created_at.strftime('%H:%M:%S, %d.%m.%Y')}</b>\n\n"
                )
                menu.append(
                    types.InlineKeyboardButton(
                        text=str(ind),
                        callback_data=ListCallbackData(
                            name="reports", id=form.id, page_num=cur_page, action="view"
                        ).pack(),
                    )
                )
        else:
            text = "Список отчетов пуст."

        if right < len(pages):
            # Added button for forward listing
            menu.append(
                types.InlineKeyboardButton(
                    text="»",
                    callback_data=ListCallbackData(
                        name="reports", id="-", page_num=cur_page + 1, action="next"
                    ).pack(),
                )
            )

        markup = types.InlineKeyboardMarkup(inline_keyboard=[menu])

        return text, markup

    async def view_data_element(self, cur_page, ind):
        pages = await self.pages
        form = pages[ind]
        text = "".join(
            f"№ {ind + 1}\n"
            f"{form.content}"
        )

        button = types.InlineKeyboardButton(
            text="« Вернуться назад",
            callback_data=ListCallbackData(
                name="reports", id="-", page_num=cur_page, action="main"
            ).pack(),
        )

        markup = types.InlineKeyboardMarkup(inline_keyboard=[button])
        return text, markup

    # @abstractmethod
    # async def delete_data_element_by_num(self, ind):
    #     pass
    #
    # @abstractmethod
    # async def delete_data_element_by_info(self, data, ind):
    #     pass

    @staticmethod
    def back_to_main(cur_page, book):
        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                text="« Вернуться назад",
                callback_data=ListCallbackData(
                    name=book, id="-", page_num=cur_page, action="main"
                ).pack(),
            ),
        )
        return markup
