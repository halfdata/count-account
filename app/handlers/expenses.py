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
from utils import __, back_button
from utils import DBUser


class ExpensesState(StatesGroup):
    category = State()
    amount = State()


class Expenses:
    """Handlers for expenses workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.expenses_message, F.text.regexp("^[\-\+]{0,1}\d+\.{0,1}\d*$"))
        router.callback_query.register(self.categories_callback, ExpensesState.category)

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(text='Invalid request.')

    async def expenses_message(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        amount = round(float(message.text), 2)
        dbuser = DBUser(self.db, message.from_user)
        book = dbuser.active_book()
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        if not amount:
            await message.answer(
                text=__(
                    text_dict=messages.EXPENSES_ZERO_AMOUNT,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        await state.update_data(amount=amount)
        await state.update_data(category=0)
        await message.answer(
            text=__(
                text_dict=messages.EXPENSES_ADD_AMOUNT,
                lang=dbuser.user_options['hl']
            ).format(
                amount='{:.2f}'.format(amount),
                currency=book.currency,
                book_title=book.title
            ),
        )
        await self.categories(message, state, message.from_user)

    async def categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(ExpensesState.category)
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
                    text=__(messages.BUTTON_SUBMIT, lang=dbuser.user_options['hl']),
                    callback_data='/submit'
                ),
                back_button(dbuser.user_options['hl']),
            ])
            keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
            await message.answer(
                text=__(
                    text_dict=messages.EXPENSES_CATEGORY_SELECT_CATEGORY,
                    lang=dbuser.user_options['hl']
                ).format(category_title=parent_category.title),
                reply_markup=keyboard_inline,
            )
        else:
            button_groups.append([
                InlineKeyboardButton(
                    text=__(messages.BUTTON_SUBMIT, lang=dbuser.user_options['hl']),
                    callback_data='/submit'
                ),
            ])
            keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
            await message.answer(
                text=__(
                    text_dict=messages.EXPENSES_ROOT_SELECT_CATEGORY,
                    lang=dbuser.user_options['hl']
                ),
                reply_markup=keyboard_inline,
            )

    async def categories_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        dbuser = DBUser(self.db, call.from_user)
        book = dbuser.active_book()
        if not book:
            await call.message.answer(
                text=__(
                    text_dict=messages.ACTIVE_BOOK_REQUIRED,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
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
                        lang=dbuser.user_options['hl']
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
                        lang=dbuser.user_options['hl']
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
            await self.categories(call.message, state, call.from_user)
            return

        category_id = int(call.data)
        category = self.db.get_category_by(
            book_id=book.id,
            id=category_id,
            deleted=False
        )
        if not category:
            await self._invalid_request(call.message, state)
            return
        await state.update_data(category=category_id)
        await self.categories(call.message, state, call.from_user)
