import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types.bot_command import BotCommand

import models
from handlers.books import Books
from handlers.expenses import Expenses
from handlers.reports import Reports
from handlers.settings import Settings
from handlers.start import Start

DB_PATH = getenv('DB_PATH', '../db')
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    exit('Please make sure that you set TELEGRAM_TOKEN as environment varaible.')

db = models.DB(f'sqlite:///{DB_PATH}/db.sqlite3')


async def main():
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
    await bot.set_my_commands([
        BotCommand(command='start', description='About Count Account'),
        BotCommand(command='books', description='Manage books'),
        BotCommand(command='today', description='Today\'s expenses'),
        BotCommand(command='yesterday', description='Yesterday\'s expenses'),
        BotCommand(command='current_month', description='Expenses for the current month'),
        BotCommand(command='settings', description='Settings'),
    ])
    dp = Dispatcher()
    form_router = Router()
    start_handler = Start(db, dp, form_router)
    settings_handler = Settings(db, dp, form_router)
    books_handler = Books(db, dp, form_router)
    reports_handler = Reports(db, dp, form_router)
    expenses_handler = Expenses(db, dp, form_router)
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
