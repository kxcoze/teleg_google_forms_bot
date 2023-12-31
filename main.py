import logging
import logging.config

import aiolog
from aiohttp.web import run_app
from aiohttp.web_app import Application
from aiogram import Bot
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import BotCommand
from aiogram.types.bot_command_scope_default import BotCommandScopeDefault

from src.handlers.commands import router
from src.handlers.callbacks import callback_router
from src.handlers.routes import receive_form_data_handler
from src.config import config, engine, async_sessionmaker, bot, dispatcher
from db.models import Base, User


async def on_startup(bot: Bot, base_url: str):
    await bot.set_webhook(
        f"{base_url}/webhook", secret_token=config.TELEGRAM_SECURITY_TOKEN
    )


async def db_init():
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
        )

    async with async_sessionmaker() as session:
        for admin_id in config.ADMIN_IDS:
            user: User = await session.get(User, admin_id)
            if user and not user.is_staff:
                continue
            await session.merge(User(id=admin_id, is_staff=True))
            await session.commit()


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="help", description="Проcмотр всех доcтупных команд"),
        BotCommand(command="admins", description="Просмотр всех администраторов бота"),
        BotCommand(command="groups", description="Просмотр групп, где состоит бот"),
        BotCommand(
            command="reports", description="Интерфейс для просмотра последних отчетов"
        ),
    ]

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())


async def notify_admins():
    for admin in config.ADMIN_IDS:
        await bot.send_message(admin, "<code>Бот запущен</code>")


async def main():
    await db_init()

    dispatcher["db_session"] = async_sessionmaker
    dispatcher["base_url"] = config.APP_BASE_URL
    dispatcher.startup.register(on_startup)

    dispatcher.include_routers(router, callback_router)
    await set_bot_commands(bot)

    app = Application()
    app["bot"] = bot
    app["db_session"] = async_sessionmaker

    app.router.add_post("/form", receive_form_data_handler)
    SimpleRequestHandler(
        dispatcher=dispatcher, bot=bot, secret_token=config.TELEGRAM_SECURITY_TOKEN
    ).register(app, path="/webhook")

    aiolog.setup_aiohttp(app)
    logging.error("Бот запущен и готов к получению форм!")
    setup_application(app, dispatcher, bot=bot)

    return app


if __name__ == "__main__":
    try:
        run_app(main(), host="bot", port=8081)
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
