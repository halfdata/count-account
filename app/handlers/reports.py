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


class MonthReportState(StatesGroup):
    report_type = State()
    year = State()
    month = State()
    day = State()


class Reports:
    """Handlers for reports workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.today, Command('today'))
        dp.message.register(self.yesterday, Command('yesterday'))
        dp.message.register(self.current_month, Command('current_month'))
        dp.message.register(self.month, Command('month'))
        dp.message.register(self.day, Command('day'))
        router.callback_query.register(self.selector_year_callback, MonthReportState.year)
        router.callback_query.register(self.selector_month_callback, MonthReportState.month)
        router.callback_query.register(self.selector_day_callback, MonthReportState.day)

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
        ct = datetime.utcnow()
        await self.per_category_report(
            message,
            state,
            from_user=from_user,
            year=ct.year,
            month=ct.month,
            day=ct.day
        )

    async def yesterday(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Yesterday's expenses."""
        await state.clear()
        ct = datetime.utcnow() - timedelta(days=1)
        await self.per_category_report(
            message,
            state,
            from_user=from_user,
            year=ct.year,
            month=ct.month,
            day=ct.day
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
        ct = datetime.utcnow()
        await self.per_category_report(
            message,
            state,
            from_user=from_user,
            year=ct.year,
            month=ct.month
        )
        await self.per_day_report(
            message,
            state,
            from_user=from_user,
            year=ct.year,
            month=ct.month
        )

    async def month(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses for the specified month."""
        await state.clear()
        from_user = from_user or message.from_user
        await state.update_data(report_type='month')
        await self.selector_year(message, state, from_user)

    async def day(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses for the specified day."""
        await state.clear()
        from_user = from_user or message.from_user
        await state.update_data(report_type='day')
        await self.selector_year(message, state, from_user)

    async def selector_year(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=from_user.language_code
                ),
            )
            return
        records = self.db.get_expenses_per_year(book.id)
        if not records:
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=from_user.language_code
                ),
            )
            return
        if len(records) == 1:
            await state.update_data(year=records[0].year)
            await self.selector_month(message, state, from_user)
            return
        await state.set_state(MonthReportState.year)
        button_groups = []
        buttons = []
        for record in records:
            buttons.append(
                InlineKeyboardButton(text=f'{record.year}', callback_data=f'{record.year}')
            )
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 3:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.REPORTS_SELECT_YEAR,
                lang=from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def selector_year_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        year = int(call.data)
        await state.update_data(year=year)
        await self.selector_month(call.message, state, call.from_user)

    async def selector_month(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=from_user.language_code
                ),
            )
            return
        data = await state.get_data()
        year = int(data['year'])
        records = self.db.get_expenses_per_month(book.id, year)
        if not records:
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=from_user.language_code
                ),
            )
            return
        if len(records) == 1:
            await state.update_data(month=records[0].month)
            if data['report_type'] == 'month':
                await self._month(message, state, from_user)
            elif data['report_type'] == 'day':
                await self.selector_day(message, state, from_user)
            else:
                self._invalid_request(message, state)
            return
        await state.set_state(MonthReportState.month)
        button_groups = []
        buttons = []
        for record in records:
            buttons.append(
                InlineKeyboardButton(
                    text=__(MONTH_LABELS[record.month], from_user.language_code),
                    callback_data=f'{record.month}'
                )
            )
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 3:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.REPORTS_SELECT_MONTH,
                lang=from_user.language_code
            ).format(year=year),
            reply_markup=keyboard_inline,
        )

    async def selector_month_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        month = int(call.data)
        if month < 1 or month > 12:
            self._invalid_request(call.message, state)
            return
        await state.update_data(month=month)
        data = await state.get_data()
        if data['report_type'] == 'month':
            await self._month(call.message, state, call.from_user)
            return
        elif data['report_type'] == 'day':
            await self.selector_day(call.message, state, call.from_user)
            return
        else:
            self._invalid_request(call.message, state)
            return

    async def _month(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses."""
        data = await state.get_data()
        await state.clear()
        await self.per_category_report(
            message,
            state,
            from_user=from_user,
            year=data['year'],
            month=data['month']
        )
        await self.per_day_report(
            message,
            state,
            from_user=from_user,
            year=data['year'],
            month=data['month']
        )

    async def selector_day(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=from_user.language_code
                ),
            )
            return
        data = await state.get_data()
        year = int(data['year'])
        month = int(data['month'])
        records = self.db.get_expenses_per_day(book.id, year, month)
        if not records:
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=from_user.language_code
                ),
            )
            return
        if len(records) == 1:
            await state.update_data(day=records[0].day)
            await self._day(message, state, from_user)
            return
        await state.set_state(MonthReportState.day)
        button_groups = []
        buttons = []
        for record in records:
            buttons.append(
                InlineKeyboardButton(
                    text=f'{record.day}',
                    callback_data=f'{record.day}'
                )
            )
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 5:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.REPORTS_SELECT_DAY,
                lang=from_user.language_code
            ).format(year=year, month=__(MONTH_LABELS[month], from_user.language_code)),
            reply_markup=keyboard_inline,
        )

    async def _day(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Expenses."""
        data = await state.get_data()
        await state.clear()
        await self.per_category_report(
            message,
            state,
            from_user=from_user,
            year=data['year'],
            month=data['month'],
            day=data['day']
        )

    async def selector_day_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        day = int(call.data)
        await state.update_data(day=day)
        await self._day(call.message, state, call.from_user)

    async def per_category_report(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None
    ) -> None:
        """Per category expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=from_user.language_code
                ),
            )
            return
        if year is not None and month is not None and day is not None:
            period = f'{year}-{month:02}-{day:02}'
        elif year is not None and month is not None:
            period = '{month}, {year}'.format(
                month=__(MONTH_LABELS[month], from_user.language_code),
                year=year
            )
        elif year is not None:
            period = f'{year}'
        else:
            self._invalid_request(message, state)
            return
        records = self.db.get_expenses_per_category(
            book_id=book.id,
            year=year,
            month=month,
            day=day
        )
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
                    lang=from_user.language_code
                ),
            )
            return
        total_amount = sum(amounts)
        max_amount = max(amounts)

        fig, ax = plt.subplots()
        bars = ax.barh(categories, amounts, label=categories)
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=from_user.language_code
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period
            )
        )
        total_label = __(messages.TOTAL, lang=from_user.language_code)
        ax.set_title(f'{total_label}: {total_amount:.2f} {book.currency}', fontweight='bold')
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
        from_user: User,
        year: int,
        month: int
    ) -> None:
        """Per day expenses."""
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=from_user.language_code
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
        period = '{month}, {year}'.format(
            month=__(MONTH_LABELS[month], from_user.language_code),
            year=year
        )
        fig, ax = plt.subplots()
        bars = ax.bar(days, amounts, label=days, align='center')
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=from_user.language_code
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period
            )
        )
        total_label = __(messages.TOTAL, lang=from_user.language_code)
        ax.set_title(f'{total_label}: {total_amount:.2f} {book.currency}', fontweight='bold')

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
