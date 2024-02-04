"""Telegram bot that allows to track your expenses."""

import asyncio
import logging
import os
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types.bot_command import BotCommand

from google.oauth2 import service_account
from googleapiclient import discovery, http

from handlers.books import Books
from handlers.expenses import Expenses
from handlers.reports import Reports
from handlers.start import Start
from utils import models

DB_PATH = os.getenv(
    'DB_PATH',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_FILE = 'db.sqlite3'
ENABLE_BACKUP = os.getenv('ENABLE_BACKUP')
GOOGLE_CREDENTIALS_FILE = os.getenv(
    'GOOGLE_CREDENTIALS_FILE',
     os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'wrong-credentials.json'
     )
)
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    sys.exit('Please make sure that you set TELEGRAM_TOKEN as environment varaible.')

db = models.DB(f'sqlite:///{DB_PATH}/{DB_FILE}')

async def task_backup():
    """Task to backup DB into Google Drive."""
    if not ENABLE_BACKUP:
        return
    while True:
        try:
            credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE)
            scoped_credentials = credentials.with_scopes(scopes=['https://www.googleapis.com/auth/drive'])
            google_drive_service = discovery.build('drive', 'v3', credentials=scoped_credentials)
            ct = datetime.utcnow()
            timeshot = f'{ct.year}-{ct.month}-{ct.day}-{ct.hour}-{ct.minute}-{ct.second}'
            file_metadata = {'name': f'count-account-db-{timeshot}.sqlite3'}
            if GOOGLE_DRIVE_FOLDER_ID:
                file_metadata['parents'] = [GOOGLE_DRIVE_FOLDER_ID]
            media = http.MediaFileUpload(os.path.join(DB_PATH, DB_FILE))
            file = google_drive_service.files().create(body=file_metadata, media_body=media,
                fields='id').execute()
            print(f'File ID: {file.get("id")}')
        except Exception as error:
            print(f'An error occurred: {error}')
            file = None
        await asyncio.sleep(86400)

async def task_telegram():
    """Task to run telegram polling."""
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
    await bot.set_my_commands([
        BotCommand(command='start', description='About Count Account'),
        BotCommand(command='books', description='Manage books'),
        BotCommand(command='today', description='Today\'s report'),
        BotCommand(command='day', description='Report for the day'),
        BotCommand(command='month', description='Report for the month'),
        BotCommand(command='year', description='Report for the year'),
    ])
    await bot.set_my_commands([
        BotCommand(command='start', description='О боте'),
        BotCommand(command='books', description='Учетные книги'),
        BotCommand(command='today', description='Отчет за сегодня'),
        BotCommand(command='day', description='Отчет за день'),
        BotCommand(command='month', description='Отчет за месяц'),
        BotCommand(command='year', description='Отчет за год'),
    ], language_code='ru')
    dp = Dispatcher()
    form_router = Router()
    start_handler = Start(db, dp)
    books_handler = Books(db, dp, form_router)
    reports_handler = Reports(db, dp, form_router)
    expenses_handler = Expenses(db, dp, form_router)
    dp.include_router(form_router)

    await dp.start_polling(bot)

async def main():
    """Main method."""
    await asyncio.gather(task_backup(), task_telegram())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
