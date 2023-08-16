from datetime import datetime

from multidict import MultiDict


def reformat_str(string):
    # Изменить строку, чтобы парсер телеграма не ругался.
    return string.replace("<", "&lt;").replace(">", "&gt;").strip()


def create_message_text(form_data):
    """
    Парсер данных формы
    """
    form_data = MultiDict(form_data)
    created_at = datetime.fromtimestamp(int(form_data["created_at"]) / 1e3)
    del form_data["created_at"]

    msg = ["<b>Отчет</b>", f"Отметка времени: <b>{created_at.strftime('%H:%M:%S')}</b>"]
    for key, value in form_data.items():
        key, value = reformat_str(key), reformat_str(value)
        msg.append(f"{key}: {f'<b>{value}</b>' if value else '<em>Пусто</em>'}")
    return "\n".join(msg)
