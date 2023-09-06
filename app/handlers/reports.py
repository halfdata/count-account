import calendar
from datetime import datetime, date, time, timedelta
from io import BytesIO
from typing import Any, Optional

from aiogram import Dispatcher, Router
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
from utils import __, DBUser
from utils import MONTH_LABELS


class Reports:
    """Handlers for reports workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.today, Command('today'))
        dp.message.register(self.yesterday, Command('yesterday'))
        dp.message.register(self.current_month, Command('current_month'))

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(text='Invalid request.')

    async def today(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Today's expenses."""
        await state.clear()
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
        """Yesterday's expenses."""
        await state.clear()
        yesterday_time = datetime.utcnow() - timedelta(days=1)
        await self.per_category_report(
            message,
            state,
            from_date=datetime.combine(yesterday_time, time.min),
            to_date=datetime.combine(yesterday_time, time.max),
            from_user=from_user
        )

    async def current_month(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses for the current month."""
        await state.clear()
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        ct = datetime.utcnow()
        _, last_day = calendar.monthrange(ct.year, ct.month)
        period_label = '{month}, {year}'.format(
            month=__(MONTH_LABELS[ct.month], dbuser.user_options['hl']),
            year=ct.year
        )
        await self.per_category_report(
            message,
            state,
            from_date=datetime.combine(date(ct.year, ct.month, 1), time.min),
            to_date=datetime.combine(date(ct.year, ct.month, last_day), time.max),
            from_user=from_user,
            period_label=period_label
        )
        await self.per_day_report(
            message,
            state,
            year=ct.year,
            month=ct.month,
            from_user=from_user,
            period_label=period_label
        )

    async def per_category_report(
        self,
        message: Message,
        state: FSMContext,
        from_date: datetime,
        to_date: datetime,
        from_user: Optional[User] = None,
        period_label: Optional[str] = None
    ) -> None:
        """Per category expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=dbuser.user_options['hl']
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
                    categories.append(record.category_title)
                else:
                    categories.append('Uncategorized')
                amounts.append(record.amount)
        if not categories:
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        total_amount = sum(amounts)
        max_amount = max(amounts)
        if period_label is None:
            period = (from_date_str if from_date_str == to_date_str else f'{from_date_str} ... {to_date_str}')
        else:
            period = period_label
        fig, ax = plt.subplots()
        bars = ax.barh(categories, amounts, label=categories)
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=dbuser.user_options['hl']
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period
            )
        )
        ax.set_title(f'Total: {total_amount:.2f} {book.currency}', fontweight='bold')
        low_values = [f'{v:.2f}' if v < 0.15 * max_amount else '' for v in amounts]
        nonlow_values = [f'{v:.2f}' if v >= 0.15 * max_amount else '' for v in amounts]
        ax.bar_label(bars, nonlow_values,
                     label_type='center', color='white')
        ax.bar_label(bars, low_values,
                     label_type='edge', color='grey', padding=3)
        ax.set_xlabel(book.currency)
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        await message.answer_photo(
            photo=BufferedInputFile(file=image_png, filename='report.png')
        )

    async def per_day_report(
        self,
        message: Message,
        state: FSMContext,
        year: int,
        month: int,
        from_user: Optional[User] = None,
        period_label: Optional[str] = None
    ) -> None:
        """Per day expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        records = self.db.get_expenses_per_day(
            book_id=book.id, year=year, month=month)
        _, last_day = calendar.monthrange(year, month)
        days = [day for day in range(1, last_day + 1)]
        amounts = [0]*last_day
        for record in records:
            amounts[record.day-1] = record.amount

        total_amount = sum(amounts)
        max_amount = max(amounts)
        if period_label is None:
            period = f'{year}-{month}'
        else:
            period = period_label
        fig, ax = plt.subplots()
        bars = ax.bar(days, amounts, label=days, align='center')
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=dbuser.user_options['hl']
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period
            )
        )
        ax.set_title(f'Total: {total_amount:.2f} {book.currency}', fontweight='bold')

        low_values = [f'{v:.2f}' if v < 0.15 * max_amount else '' for v in amounts]
        nonlow_values = [f'{v:.2f}' if v >= 0.15 * max_amount else '' for v in amounts]
        ax.bar_label(bars, nonlow_values, size='8', color='white',
                     label_type='center', rotation='vertical')
        ax.bar_label(bars, low_values, size='8', color='gray',
                     label_type='edge', rotation='vertical', padding=5)
        ax.set_xlim(0.5, last_day + 0.5)
        ax.set_ylabel(book.currency)
        ax.set_xlabel(period)
        plt.xticks(days, size='8')
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        await message.answer_photo(
            photo=BufferedInputFile(file=image_png, filename='report.png')
        )
