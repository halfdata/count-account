import asyncio
import logging
import sys
import re
from os import getenv
from typing import Any, Dict
import functools

import messages
import models
import settings
from utils import __


from datetime import datetime
from itertools import islice
from typing import Optional
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
)
from aiogram.types.user import User
from handlers.user import DBUser

class CategoriesState(StatesGroup):
    parent = State()
    category = State()
    title = State()


class Categories:
    """Handlers for /categories workflow."""
    db: models.DB
    router: Router

    def __init__(self, db: models.DB, router: Router) -> None:
        self.db = db
        self.router = router
        router.message.register(self.categories, Command('categories'))
        router.callback_query.register(self.categories_callback, CategoriesState.category)
        router.message.register(self.title_message, CategoriesState.title)

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
            user_id=from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            return False
        return book

    def _back_button(self):
        return InlineKeyboardButton(text='Back', callback_data='/back')

    async def categories(
        self,
        message: Message,
        state: FSMContext
    ) -> None:
        await state.update_data(parent='0')
        await self._categories(message, state, message.from_user)

    async def _categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(CategoriesState.category)
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
        data = await state.get_data()
        parent_category = None
        if 'parent' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent']),
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
                text=category.title.capitalize(),
                callback_data=str(category.id)
            ) for category in categories
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 2:
                button_groups.append([])
            button_groups[-1].append(button)
        button_groups.append([InlineKeyboardButton(text="+ Add Category", callback_data='/new')])
        if parent_category:
            button_groups.append([
                InlineKeyboardButton(text="Update Title", callback_data='/update_title'),
                InlineKeyboardButton(text="Remove", callback_data='/delete'),
            ])
            button_groups.append([
                self._back_button(),
            ])
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        if not parent_category:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_WELCOME,
                    lang=from_user.language_code
                ),
                reply_markup=keyboard_inline,
            )
        else:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_WELCOME_TO_CATEGORY,
                    lang=from_user.language_code
                ).format(title=parent_category.title.capitalize()),
                reply_markup=keyboard_inline,
            )

    async def categories_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        book = self._active_book(call.from_user)
        if not book:
            await call.message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_ACTIVE_BOOK_REQUIRED,
                    lang=call.from_user.language_code
                ),
            )
            return
        data = await state.get_data()
        parent_category = None
        if 'parent' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent']),
                deleted=False
            )

        if call.data == '/new':
            await state.update_data(category='/new')
            await self.title(call.message, state, call.from_user)
            return
        if call.data == '/update_title':
            await state.update_data(category=data['parent'])
            await self.title(call.message, state, call.from_user)
            return
        if call.data == '/delete':
            category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent']),
                deleted=False
            )
            if category:
                self.db.delete_category(category.id)
                await state.update_data(parent=category.parent_id)
                await call.message.answer(
                    text=__(
                        text_dict=messages.CATEGORIES_DELETED,
                        lang=call.from_user.language_code
                    ).format(title=category.title.capitalize()),
                )
            else:
                await state.update_data(parent=0)
            await self._categories(call.message, state, call.from_user)
            return
        if call.data == '/back':
            category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent']),
                deleted=False
            )
            if category:
                await state.update_data(parent=category.parent_id)
            else:
                await state.update_data(parent=0)
            await self._categories(call.message, state, call.from_user)
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
        await state.update_data(parent=category_id)
        await self._categories(call.message, state, call.from_user)

    async def title(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(CategoriesState.title)
        from_user = from_user or message.from_user
        await message.answer(
            text=__(
                text_dict=messages.CATEGORIES_ADD_TITLE,
                lang=from_user.language_code
            ),
        )

    async def title_message(self, message: Message, state: FSMContext) -> None:
        book = self._active_book(message.from_user)
        if not book:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_ACTIVE_BOOK_REQUIRED,
                    lang=message.from_user.language_code
                ),
            )
            return
        data = await state.get_data()
        title = re.sub('\s{2,}', ' ', message.text.strip().lower())
        if len(title) > 31:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_TITLE_TOO_LONG,
                    lang=message.from_user.language_code
                ),
            )
            return
        if len(title) < 2:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_TITLE_TOO_SHORT,
                    lang=message.from_user.language_code
                ),
            )
            return
        if title.startswith('/'):
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_TITLE_AVOID_SLASH,
                    lang=message.from_user.language_code
                ),
            )
            return
        parent_category = None
        if 'parent' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent']),
                deleted=False
            )
        category = self.db.get_category_by(
            book_id=book.id,
            parent_id=(0 if not parent_category else parent_category.id),
            title=title,
            deleted=False
        )
        if category:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_ALREADY_EXISTS,
                    lang=message.from_user.language_code
                ).format(title=title.capitalize()),
            )
            return
        await state.set_state(CategoriesState.parent)
        data = await state.get_data()
        if data['category'] == '/new':
            self.db.add_category(
                book_id=book.id,
                parent_id=(0 if not parent_category else parent_category.id),
                title=title,
                deleted=False
            )    
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_SUCCESSFULLY_CREATED,
                    lang=message.from_user.language_code
                ).format(title=title.capitalize()),
            )
            await self._categories(message, state, message.from_user)
            return
        category_id = int(data['category'])
        category = self.db.get_category_by(
            book_id=book.id,
            id=category_id,
            deleted=False
        )
        if not category:
            await self._invalid_request(message, state)
            return
        self.db.update_category(id=category_id, title=title)       
        await message.answer(
            text=__(
                text_dict=messages.CATEGORIES_TITLE_UPDATED,
                lang=message.from_user.language_code
            ),
        )
        await self._categories(message, state, message.from_user)
