import logging

from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiogram.types import Message
from sqlalchemy.orm import sessionmaker

from src.config import config


def api_authentication(func):
    async def wrapped(*args, **kwargs):
        request: Request = args[0]
        if request.headers['security_token'] != config.GOOGLE_SECURITY_TOKEN:
            logging.error('Someone trying to bypass API authentication!')
            return json_response({"ok": False, "err": "Unauthorized"}, status=401)

        return await func(*args, **kwargs)

    return wrapped


def admin_authentication(func):
    async def wrapped(*args, **kwargs):
        message: Message = args[0]
        if message.chat.id not in config.ADMIN_IDS:
            return
        return await func(*args, **kwargs)
    return wrapped
