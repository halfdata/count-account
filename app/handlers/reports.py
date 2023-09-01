from datetime import datetime, time, timedelta
from io import BytesIO
from typing import Any, Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.types.user import User
from aiogram.types.input_file import BufferedInputFile
import matplotlib.pyplot as plt

import messages
import models
from handlers.user import DBUser
from utils import __


class Reports:
    """Handlers for reports workflow."""
    db: models.DB
    router: Router

    def __init__(self, db: models.DB, router: Router) -> None:
        self.db = db
        self.router = router
        router.message.register(self.today, Command('today'))
        router.message.register(self.yesterday, Command('yesterday'))

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            text=__(
                text_dict=messages.INVALID_REQUEST,
                lang=message.from_user.language_code
            )
        )

    def _active_book(self, from_user: User) -> Any:
        """Returns active book for current user."""
        dbuser = DBUser(self.db, from_user)
        if not dbuser.user_options['active_book']:
            return False
        book_id = int(dbuser.user_options['active_book'])
        book = self.db.get_book_by(
            id=book_id,
            deleted=False
        )
        if not book:
            return False
        return book

    async def today(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Report for today's expenses."""
        current_time = datetime.utcnow()
        await self.per_category_report(
            message,
            state,
            from_date=datetime.combine(current_time, time.min),
            to_date=datetime.combine(current_time, time.max),
            from_user=from_user
        )

    async def yesterday(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Report for yesterday's expenses."""
        yesterday_time = datetime.utcnow() - timedelta(days=1)
        await self.per_category_report(
            message,
            state,
            from_date=datetime.combine(yesterday_time, time.min),
            to_date=datetime.combine(yesterday_time, time.max),
            from_user=from_user
        )

    async def per_category_report(
        self,
        message: Message,
        state: FSMContext,
        from_date: datetime,
        to_date: datetime,
        from_user: Optional[User] = None
    ) -> None:
        from_user = from_user or message.from_user
        book = self._active_book(from_user)
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_ACTIVE_BOOK_REQUIRED,
                    lang=from_user.language_code
                ),
            )
            return
        records = self.db.get_expenses_per_category(
            book_id=book.id,
            from_date=from_date,
            to_date=to_date
        )
        from_date_str = f'{from_date.year}-{from_date.month:02}-{from_date.day:02}'
        to_date_str = f'{to_date.year}-{to_date.month:02}-{to_date.day:02}'
 
        categories = []
        amounts = []
        for record in records:
            if record.amount:
                if record.category_title:
                    categories.append(record.category_title.capitalize())
                else:
                    categories.append('Uncategorized')
                amounts.append(record.amount)
        if not categories:
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=from_user.language_code
                ),
            )
            return
        total_amount = sum(amounts)
        fig, ax = plt.subplots()
        bars = ax.barh(categories, amounts, label=categories)
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_PER_CATEGORY_TITLE,
                lang=message.from_user.language_code
            ).format(
                book_title=book.title.capitalize(),
                currency=book.currency,
                period=(from_date_str if from_date_str == to_date_str else f'{from_date_str} ... {to_date_str}')
            )
        )
        ax.set_title(f'Total: {total_amount:.2f} {book.currency}', fontweight='bold')
        ax.bar_label(bars, label_type='center', fmt='{:.2f}', color='lightgray')
        ax.set_xlabel(book.currency)
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        await message.answer_photo(
            photo=BufferedInputFile(file=image_png, filename='report.png')
        )
