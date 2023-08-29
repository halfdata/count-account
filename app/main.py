import asyncio
import logging
import sys
import re
from os import getenv
from typing import Any, Dict

import messages
import models
import settings
from handlers.books import Books
from handlers.categories import Categories
from handlers.expenses import Expenses


from datetime import datetime
from itertools import islice

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonCommands,
)
from aiogram.types.bot_command import BotCommand

DB_PATH = getenv('DB_PATH', '../db')
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    exit('Please make sure that you set TELEGRAM_TOKEN as environment varaible.')

db = models.DB(f'sqlite:///{DB_PATH}/db.sqlite3')

form_router = Router()

book_handler = Books(db, form_router)
categories_handler = Categories(db, form_router)
expenses_handler = Expenses(db, form_router)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
    await bot.set_my_commands([
        BotCommand(command='books', description='Manage books'),
        BotCommand(command='categories', description='Manage categories'),
    ])
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())