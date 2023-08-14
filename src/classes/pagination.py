import pytz
from typing import List

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from async_property import async_property
from sqlalchemy import select

from db.models import Form


class FormCallbackData(CallbackData, prefix="page"):
    name: str
    form_id: int | None
    page_num: int
    pos: int | None
    action: str
    # page:<name>:<id>:<page_num>:<pos>:<action>


class Pagination:
    WIDTH = 5

    def __init__(self, db_session):
        self.db_session = db_session

    @async_property
    async def pages(self):
        async with self.db_session() as session:
            rows = await session.execute(
                select(Form)
                .where(Form.status == 1)
                .order_by(Form.created_at.desc())
                .limit(300)
            )
            forms: List[Form] = rows.scalars().all()
        return forms

    async def search_nonempty_page(self, left, right, cur_page=0):
        searched_page = cur_page
        pages = await self.pages
        while searched_page > 0 and not pages[left:right]:
            right -= self.WIDTH
            left -= self.WIDTH
            searched_page -= 1

        return left, right, searched_page

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
                    callback_data=FormCallbackData(
                        name="reports",
                        form_id=-1,
                        page_num=cur_page - 1,
                        pos=-1,
                        action="prev",
                    ).pack(),
                )
            )
        pages = await self.pages
        if pages:
            text = "<b>Отчеты</b>\n"
            forms = pages[left:right]
            for pos, form in enumerate(forms, start=left + 1):
                formatted_time = pytz.utc.localize(
                    form.created_at, is_dst=None
                ).astimezone(pytz.timezone("Europe/Moscow"))
                text += (
                    f"№ {pos}\n"
                    f"ФИО: <b>{form.username}</b>\n"
                    f"Проект: <b>{form.destination}</b>\n"
                    f"Отметка времени: <b>{formatted_time.strftime('%H:%M:%S, %d/%m/%Y')}</b>\n\n"
                )
                menu.append(
                    types.InlineKeyboardButton(
                        text=str(pos),
                        callback_data=FormCallbackData(
                            name="reports",
                            form_id=form.id,
                            page_num=cur_page,
                            pos=pos,
                            action="view",
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
                    callback_data=FormCallbackData(
                        name="reports",
                        form_id=-1,
                        page_num=cur_page + 1,
                        pos=-1,
                        action="next",
                    ).pack(),
                )
            )

        markup = types.InlineKeyboardMarkup(inline_keyboard=[menu])

        return text, markup

    async def view_data_element(self, cur_page: int, form_id: int, pos: int):
        async with self.db_session() as session:
            form = await session.get(Form, form_id)

        text = "".join(f"№ {pos}\n" f"{form.content}")

        button = types.InlineKeyboardButton(
            text="« Вернуться назад",
            callback_data=FormCallbackData(
                name="reports",
                form_id=form.id,
                page_num=cur_page,
                pos=pos,
                action="main",
            ).pack(),
        )

        markup = types.InlineKeyboardMarkup(inline_keyboard=[[button]])
        return text, markup

    @staticmethod
    def back_to_main(cur_page, book):
        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                text="« Вернуться назад",
                callback_data=FormCallbackData(
                    name=book, form_id=None, page_num=cur_page, pos=None, action="main"
                ).pack(),
            ),
        )
        return markup
