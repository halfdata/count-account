import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types.bot_command import BotCommand

import models
from handlers.books import Books
from handlers.categories import Categories
from handlers.expenses import Expenses
from handlers.reports import Reports
from handlers.settings import Settings

DB_PATH = getenv('DB_PATH', '../db')
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    exit('Please make sure that you set TELEGRAM_TOKEN as environment varaible.')

db = models.DB(f'sqlite:///{DB_PATH}/db.sqlite3')
form_router = Router()

settings_handler = Settings(db, form_router)
books_handler = Books(db, form_router)
categories_handler = Categories(db, form_router)
reports_handler = Reports(db, form_router)
expenses_handler = Expenses(db, form_router)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
    await bot.set_my_commands([
        BotCommand(command='books', description='Manage books'),
        BotCommand(command='categories', description='Manage categories'),
        BotCommand(command='today', description='Today\'s expenses'),
        BotCommand(command='yesterday', description='Yesterday\'s expenses'),
        BotCommand(command='current_month', description='Expenses for the current month'),
        BotCommand(command='settings', description='Settings'),
    ])
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
