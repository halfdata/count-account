"""Handlers for expenses workflow."""

from datetime import datetime
from typing import Any, Optional

from aiogram import Dispatcher, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.types.user import User

import messages
import models
from handlers import HandlerBase
from utils import __
from utils import DBUser


class ExpensesState(StatesGroup):
    """State for expenses."""
    category = State()
    amount = State()


class Expenses(HandlerBase):
    """Handlers for expenses workflow."""

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        super().__init__(db)
        dp.message.register(self.expenses_message, F.text.regexp("^[\-\+]{0,1}\d+\.{0,1}\d*$"))
        router.callback_query.register(self.selector_categories_callback, ExpensesState.category)

    @HandlerBase.active_book_required
    async def expenses_message(
            self,
            message: Message,
            state: FSMContext,
            book: Any
    ) -> None:
        """Entrypoint for expenses."""
        await state.clear()
        amount = round(float(message.text), 2)
        if not amount:
            await message.answer(
                text=__(
                    text_dict=messages.EXPENSES_ZERO_AMOUNT,
                    lang=message.from_user.language_code
                ),
            )
            return
        await state.update_data(amount=amount)
        await state.update_data(category=0)
        await message.answer(
            text=__(
                text_dict=messages.EXPENSES_ADD_AMOUNT,
                lang=message.from_user.language_code
            ).format(
                amount='{:.2f}'.format(amount),
                currency=book.currency,
                book_title=book.title
            ),
        )
        await self.selector_categories(message, state=state, from_user=message.from_user)

    @HandlerBase.active_book_required
    async def selector_categories(
        self,
        message: Message,
        state: FSMContext,
        book: Any,
        from_user: Optional[User] = None
    ) -> None:
        """Displays message with category selector."""
        await state.set_state(ExpensesState.category)
        from_user = from_user or message.from_user
        data = await state.get_data()
        parent_category = None
        if 'category' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['category']),
                deleted=False,
            )
        categories = self.db.get_categories_by(
            book_id=book.id,
            parent_id=(0 if not parent_category else parent_category.id),
            deleted=False
        )
        button_groups = []
        buttons = [
            InlineKeyboardButton(
                text=category.title,
                callback_data=str(category.id)
            ) for category in categories
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 2:
                button_groups.append([])
            button_groups[-1].append(button)
        if parent_category:
            button_groups.append([
                InlineKeyboardButton(
                    text=__(messages.BUTTON_SUBMIT, lang=from_user.language_code),
                    callback_data='/submit'
                ),
                self.back_button(from_user.language_code),
            ])
            keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
            await message.answer(
                text=__(
                    text_dict=messages.EXPENSES_CATEGORY_SELECT_CATEGORY,
                    lang=from_user.language_code
                ).format(category_title=parent_category.title),
                reply_markup=keyboard_inline,
            )
        else:
            button_groups.append([
                InlineKeyboardButton(
                    text=__(messages.BUTTON_SUBMIT, lang=from_user.language_code),
                    callback_data='/submit'
                ),
            ])
            keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
            await message.answer(
                text=__(
                    text_dict=messages.EXPENSES_ROOT_SELECT_CATEGORY,
                    lang=from_user.language_code
                ),
                reply_markup=keyboard_inline,
            )

    @HandlerBase.active_book_required
    async def selector_categories_callback(
        self,
        call: CallbackQuery,
        state: FSMContext,
        book: Any
    ) -> None:
        """Callback for category selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        data = await state.get_data()
        category = self.db.get_category_by(
            book_id=book.id,
            id=int(data['category']),
            deleted=False
        )
        amount = round(float(data['amount']), 2)
        if call.data == '/submit':
            created = datetime.utcnow()
            self.db.add_expense(
                user_id=call.from_user.id,
                book_id=book.id,
                category_id=(0 if not category else category.id),
                amount=amount,
                year=created.year,
                month=created.month,
                day=created.day,
                created=created,
                deleted=False
            )
            await state.clear()
            if category:
                await call.message.answer(
                    text=__(
                        text_dict=messages.EXPENSES_SUCCESSFULLY_CREATED_IN_CATEGORY,
                        lang=call.from_user.language_code
                    ).format(
                        amount='{:.2f}'.format(amount),
                        currency=book.currency,
                        category_title=category.title,
                        book_title=book.title
                    )
                )
            else:
                await call.message.answer(
                    text=__(
                        text_dict=messages.EXPENSES_SUCCESSFULLY_CREATED,
                        lang=call.from_user.language_code
                    ).format(
                        amount='{:.2f}'.format(amount),
                        currency=book.currency,
                        book_title=book.title
                    )
                )
            return
        if call.data == '/back':
            if category:
                await state.update_data(category=category.parent_id)
            else:
                await state.update_data(category=0)
            await self.selector_categories(call.message, state=state, from_user=call.from_user)
            return

        category_id = int(call.data)
        category = self.db.get_category_by(
            book_id=book.id,
            id=category_id,
            deleted=False
        )
        if not category:
            await self._invalid_request(call.message, state=state)
            return
        await state.update_data(category=category_id)
        await self.selector_categories(call.message, state=state, from_user=call.from_user)
