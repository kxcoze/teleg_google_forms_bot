from datetime import datetime

import pytz
from multidict import MultiDict

from src.config import config


def reformat_str(string):
    # Изменить строку, чтобы парсер телеграма не ругался.
    return string.replace("<", "&lt;").replace(">", "&gt;").strip()


def create_message_text(form_data):
    """
    Парсер данных формы
    """
    form_data = MultiDict(form_data)
    created_at = datetime.fromtimestamp(
        int(form_data["created_at"]) / 1e3, pytz.timezone(config.TIMEZONE)
    )
    del form_data["created_at"]

    msg = [
        "<b>Отчет</b>",
        f"Отметка времени: <b>{created_at.strftime('%H:%M:%S, %d/%m/%Y')}</b>",
    ]
    for key, value in form_data.items():
        if not value.strip():
            continue
        key, value = reformat_str(key), reformat_str(value)
        msg.append(f"{key}: {f'<b>{value}</b>' if value else '<em>Пусто</em>'}")
    return "\n".join(msg)
