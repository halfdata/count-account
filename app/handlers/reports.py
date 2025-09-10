"""Handlers for reports workflow."""

import calendar
import json
from datetime import datetime, timedelta
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

from handlers import HandlerBase
from utils import CategoryType
from utils import messages
from utils import models
from utils import __
from utils import MONTH_LABELS


class ReportState(StatesGroup):
    """State for reports."""
    report_type = State()
    year = State()
    month = State()
    day = State()


class Reports(HandlerBase):
    """Handler class for reports workflow."""

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        super().__init__(db)
        dp.message.register(self.today, Command('today'))
        dp.message.register(self.year, Command('year'))
        dp.message.register(self.month, Command('month'))
        dp.message.register(self.day, Command('day'))
        router.callback_query.register(self.selector_year_callback, ReportState.year)
        router.callback_query.register(self.selector_month_callback, ReportState.month)
        router.callback_query.register(self.selector_day_callback, ReportState.day)

    @HandlerBase.active_book_required
    async def today(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None
    ) -> None:
        """Entrypoint for 'Today's expenses'."""
        await state.clear()
        ct = datetime.utcnow()
        income_exists = await self.per_category_report(
            message,
            state=state,
            from_user=message.from_user,
            book=book,
            category_type=CategoryType.INCOME,
            year=ct.year,
            month=ct.month,
            day=ct.day
        )
        expense_exists = await self.per_category_report(
            message,
            state=state,
            from_user=message.from_user,
            book=book,
            category_type=CategoryType.EXPENSE,
            year=ct.year,
            month=ct.month,
            day=ct.day
        )
        if not any((income_exists, expense_exists)):
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=message.from_user.language_code
                ),
            )

    @HandlerBase.active_book_required
    async def year(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Entrypoint for 'Expenses for the specified year'."""
        del book
        await state.clear()
        from_user = from_user or message.from_user
        await state.update_data(report_type='year')
        await self.selector_year(message, state=state, from_user=from_user)

    @HandlerBase.active_book_required
    async def month(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Entrypoint for 'Expenses for the specified month'."""
        del book
        await state.clear()
        from_user = from_user or message.from_user
        await state.update_data(report_type='month')
        await self.selector_year(message, state=state, from_user=from_user)

    @HandlerBase.active_book_required
    async def day(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Entrypoint for 'Expenses for the specified day'."""
        del book
        await state.clear()
        from_user = from_user or message.from_user
        await state.update_data(report_type='day')
        await self.selector_year(message, state=state, from_user=from_user)

    @HandlerBase.active_book_required
    async def selector_year(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Displays message with year selector."""
        from_user = from_user or message.from_user
        records = self.db.get_expenses_per_year(book.id, category_type=None)
        if not records:
            await message.answer(
                text=__(
                    text_dict=messages.REPORTS_NO_DATA,
                    lang=from_user.language_code
                ),
            )
            return
        data = await state.get_data()
        if len(records) == 1:
            await state.update_data(year=records[0].year)
            if data['report_type'] == 'year':
                await self._year(message, state=state, from_user=from_user)
            elif data['report_type'] in ('month', 'day'):
                await self.selector_month(message, state=state, from_user=from_user)
            else:
                self._invalid_request(message, state=state)
            return
        await state.set_state(ReportState.year)
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
        """Callback for year selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        year = int(call.data)
        await state.update_data(year=year)
        data = await state.get_data()
        if data['report_type'] == 'year':
            await self._year(call.message, state=state, from_user=call.from_user)
            return
        elif data['report_type'] in ('month', 'day'):
            await self.selector_month(call.message, state=state, from_user=call.from_user)
            return
        else:
            self._invalid_request(call.message, state=state)
            return

    @HandlerBase.active_book_required
    async def _year(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Report for the specified year."""
        data = await state.get_data()
        await state.clear()
        await self.per_category_report(
            message,
            state=state,
            from_user=from_user,
            book=book,
            category_type=CategoryType.INCOME,
            year=data['year']
        )
        await self.per_month_report(
            message,
            from_user=from_user,
            book=book,
            category_type=CategoryType.INCOME,
            year=data['year']
        )
        await self.per_category_report(
            message,
            state=state,
            from_user=from_user,
            book=book,
            category_type=CategoryType.EXPENSE,
            year=data['year']
        )
        await self.per_month_report(
            message,
            from_user=from_user,
            book=book,
            category_type=CategoryType.EXPENSE,
            year=data['year']
        )

    @HandlerBase.active_book_required
    async def selector_month(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Displays message with month selector."""
        from_user = from_user or message.from_user
        data = await state.get_data()
        year = int(data['year'])
        records = self.db.get_expenses_per_month(book.id, category_type=None, year=year)
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
                await self._month(message, state=state, from_user=from_user)
            elif data['report_type'] == 'day':
                await self.selector_day(message, state=state, from_user=from_user)
            else:
                self._invalid_request(message, state=state)
            return
        await state.set_state(ReportState.month)
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
        """Callback for month selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        month = int(call.data)
        if month < 1 or month > 12:
            self._invalid_request(call.message, state=state)
            return
        await state.update_data(month=month)
        data = await state.get_data()
        if data['report_type'] == 'month':
            await self._month(call.message, state=state, from_user=call.from_user)
            return
        elif data['report_type'] == 'day':
            await self.selector_day(call.message, state=state, from_user=call.from_user)
            return
        else:
            self._invalid_request(call.message, state=state)
            return

    @HandlerBase.active_book_required
    async def _month(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Report for the specified month."""
        data = await state.get_data()
        await state.clear()
        await self.per_category_report(
            message,
            state=state,
            from_user=from_user,
            book=book,
            category_type=CategoryType.INCOME,
            year=data['year'],
            month=data['month']
        )
        await self.per_day_report(
            message,
            from_user=from_user,
            book=book,
            category_type=CategoryType.INCOME,
            year=data['year'],
            month=data['month']
        )
        await self.per_category_report(
            message,
            state=state,
            from_user=from_user,
            book=book,
            category_type=CategoryType.EXPENSE,
            year=data['year'],
            month=data['month']
        )
        await self.per_day_report(
            message,
            from_user=from_user,
            book=book,
            category_type=CategoryType.EXPENSE,
            year=data['year'],
            month=data['month']
        )

    @HandlerBase.active_book_required
    async def selector_day(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Displays message with day selector."""
        from_user = from_user or message.from_user
        data = await state.get_data()
        year = int(data['year'])
        month = int(data['month'])
        records = self.db.get_expenses_per_day(book.id, category_type=None, year=year, month=month)
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
            await self._day(message, state=state, from_user=from_user)
            return
        await state.set_state(ReportState.day)
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

    @HandlerBase.active_book_required
    async def _day(
        self,
        message: Message,
        state: FSMContext,
        book: Optional[Any] = None,
        from_user: Optional[User] = None
    ) -> None:
        """Report for the specified day."""
        data = await state.get_data()
        await state.clear()
        await self.per_category_report(
            message,
            state=state,
            from_user=from_user,
            book=book,
            category_type=CategoryType.INCOME,
            year=data['year'],
            month=data['month'],
            day=data['day']
        )
        await self.per_category_report(
            message,
            state=state,
            from_user=from_user,
            book=book,
            category_type=CategoryType.EXPENSE,
            year=data['year'],
            month=data['month'],
            day=data['day']
        )

    async def selector_day_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for day selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        day = int(call.data)
        await state.update_data(day=day)
        await self._day(call.message, state=state, from_user=call.from_user)

    async def per_category_report(
        self,
        message: Message,
        state: FSMContext,
        from_user: User,
        book: Any,
        category_type: CategoryType,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None
    ) -> bool:
        """Per category expenses."""
        from_user = from_user or message.from_user
        monthly_report = False
        if year is not None and month is not None and day is not None:
            period = f'{year}-{month:02}-{day:02}'
        elif year is not None and month is not None:
            period = '{month}, {year}'.format(
                month=__(MONTH_LABELS[month], from_user.language_code),
                year=year
            )
            monthly_report = True
        elif year is not None:
            period = f'{year}'
        else:
            self._invalid_request(message, state=state)
            return False
        if category_type == CategoryType.INCOME:
            category_type_label = __(messages.REPORTS_INCOME, lang=from_user.language_code)
        else:
            category_type_label = __(messages.REPORTS_EXPENSE, lang=from_user.language_code)
        records = self.db.get_expenses_per_category(
            book_id=book.id,
            category_type=category_type,
            year=year,
            month=month,
            day=day
        )
        categories = []
        amounts = []
        colors = []
        for record in records:
            if record.amount:
                amounts.append(record.amount)
                if record.category_title:
                    categories.append(record.category_title)
                else:
                    categories.append('Uncategorized')
                category = self.db.get_category_by(
                    book_id = book.id,
                    id = record.category_id,
                )
                if monthly_report:
                    try:
                        options = json.loads(category.options)
                    except Exception:
                        options = {}
                    monthly_limit = options.get('monthly_limit')
                    if monthly_limit:
                        if record.amount > monthly_limit:
                            colors.append('#FC9272')
                        elif record.amount > monthly_limit * 0.8:
                            colors.append('#FFD98E')
                        else:
                            colors.append('#A1D99B')
                    else:
                        colors.append('#6BAED6')
                else:
                    colors.append('#6BAED6')

        if not categories:
            return False
        total_amount = sum(amounts)
        max_amount = max(amounts)

        fig, ax = plt.subplots()
        bars = ax.barh(categories, amounts, label=categories, color=colors)
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=from_user.language_code
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period,
                category_type=category_type_label
            )
        )
        total_label = __(messages.TOTAL, lang=from_user.language_code)
        ax.set_title(f'{total_label}: {total_amount:.2f} {book.currency}', fontweight='bold')
        if len(categories) < 10:
            label_size = 12
        elif len(categories) < 20:
            label_size = 10
        else:
            label_size = 8
        low_values = [f'{v:.2f}' if v < 0.15 * max_amount else '' for v in amounts]
        nonlow_values = [f'{v:.2f}' if v >= 0.15 * max_amount else '' for v in amounts]
        ax.bar_label(bars, nonlow_values, size=label_size,
                     label_type='center', color='white')
        ax.bar_label(bars, low_values, size=label_size,
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
        return True

    async def per_day_report(
        self,
        message: Message,
        from_user: User,
        book: Any,
        category_type: CategoryType,
        year: int,
        month: int
    ) -> None:
        """Per day expenses."""
        from_user = from_user or message.from_user
        records = self.db.get_expenses_per_day(
            book_id=book.id, category_type=category_type, year=year, month=month)
        if not records:
            return
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
        if category_type == CategoryType.INCOME:
            category_type_label = __(messages.REPORTS_INCOME, lang=from_user.language_code)
        else:
            category_type_label = __(messages.REPORTS_EXPENSE, lang=from_user.language_code)
        fig, ax = plt.subplots()
        bars = ax.bar(days, amounts, label=days, align='center', color='#6BAED6')
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=from_user.language_code
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period,
                category_type=category_type_label
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

    async def per_month_report(
        self,
        message: Message,
        from_user: User,
        book: Any,
        category_type: CategoryType,
        year: int
    ) -> None:
        """Per month expenses."""
        from_user = from_user or message.from_user
        records = self.db.get_expenses_per_month(book_id=book.id, category_type=category_type, year=year)
        if not records:
            return
        months = [month for month in range(1, 13)]
        month_labels = [__(MONTH_LABELS[month], from_user.language_code) for month in range(1, 13)]
        amounts = [0]*12
        for record in records:
            amounts[record.month-1] = record.amount

        total_amount = sum(amounts)
        max_amount = max(amounts)
        period = f'{year}'
        if category_type == CategoryType.INCOME:
            category_type_label = __(messages.REPORTS_INCOME, lang=from_user.language_code)
        else:
            category_type_label = __(messages.REPORTS_EXPENSE, lang=from_user.language_code)
        fig, ax = plt.subplots()
        bars = ax.bar(months, amounts, label=month_labels, align='center', color='#6BAED6')
        fig.suptitle(
            __(
                text_dict=messages.REPORTS_BOOK_AND_PERIOD,
                lang=from_user.language_code
            ).format(
                book_title=book.title,
                currency=book.currency,
                period=period,
                category_type=category_type_label
            )
        )
        total_label = __(messages.TOTAL, lang=from_user.language_code)
        ax.set_title(f'{total_label}: {total_amount:.2f} {book.currency}', fontweight='bold')

        low_values = [f'{v:.2f}' if v < 0.15 * max_amount else '' for v in amounts]
        nonlow_values = [f'{v:.2f}' if v >= 0.15 * max_amount else '' for v in amounts]
        ax.bar_label(bars, nonlow_values, color='white',
                     label_type='center', rotation='vertical')
        ax.bar_label(bars, low_values, color='gray',
                     label_type='edge', rotation='vertical', padding=5)
        ax.set_xlim(0.5, 12.5)
        ax.set_ylabel(book.currency)
        ax.set_xlabel(period)
        plt.xticks(months, month_labels, rotation='vertical')
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        await message.answer_photo(
            photo=BufferedInputFile(file=image_png, filename='report.png')
        )
