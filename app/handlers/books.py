import asyncio
import logging
import sys
import re
from os import getenv
from typing import Any, Dict

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

class BookState(StatesGroup):
    book = State()
    action = State()
    title = State()
    currency = State()


class Books:
    """Handlers for /books workflow."""
    db: models.DB
    router: Router

    def __init__(self, db: models.DB, router: Router) -> None:
        self.db = db
        self.router = router
        router.message.register(self.book, Command('books'))
        router.callback_query.register(self.book_callback, BookState.book)
        router.callback_query.register(self.action_callback, BookState.action)
        router.message.register(self.title_message, BookState.title)
        router.callback_query.register(self.currency_callback, BookState.currency)
        router.message.register(self.join, Command('join'))

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            text=__(
                text_dict=messages.INVALID_REQUEST,
                lang=message.from_user.language_code
            )
        )

    def _back_button(self):
        return InlineKeyboardButton(text='Back', callback_data='/back')

    async def book(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.clear()
        await state.set_state(BookState.book)
        from_user = from_user or message.from_user
        books = self.db.get_books_by(
            user_id=from_user.id,
            deleted=False
        )
        button_groups = []
        buttons = [
            InlineKeyboardButton(
                text=book.title.capitalize(),
                callback_data=str(book.id)
            ) for book in books
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 2:
                button_groups.append([])
            button_groups[-1].append(button)
        button_groups.append([InlineKeyboardButton(text="+ Add Book", callback_data='/new')])
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_WELCOME,
                lang=from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def book_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        if call.data == '/new':
            await state.update_data(book='/new')
            await self.title(call.message, state, call.from_user)
        else:
            book_id = int(call.data)
            await state.update_data(book=book_id)
            await self.action(call.message, state, call.from_user)

    async def action(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(BookState.action)
        from_user = from_user or message.from_user
        data = await state.get_data()
        book_id = int(data['book'])
        book = self.db.get_book_by(
            user_id=from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            await self._invalid_request(message, state)
            return
        button_groups = [
            [
                InlineKeyboardButton(text='Update Title', callback_data='/update_title'),
                InlineKeyboardButton(text='Update Currency', callback_data='/update_currency'),
            ],
            [
                InlineKeyboardButton(text='Join', callback_data='/join'),
                InlineKeyboardButton(text='Remove', callback_data='/delete'),
            ],
            [
                self._back_button(),
            ]
        ]
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_SELECTED,
                lang=message.from_user.language_code
            ).format(title=book.title.capitalize(), currency=book.currency, book_uid=book.book_uid),
            reply_markup=keyboard_inline,
        )

    async def action_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        data = await state.get_data()
        book_id = int(data['book'])
        book = self.db.get_book_by(
            user_id=call.from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            await self._invalid_request(call.message, state)
            return
        if call.data == '/back':
            await self.book(call.message, state, call.from_user)
            return
        if call.data == '/update_title':
            await self.title(call.message, state, call.from_user)
            return
        if call.data == '/update_currency':
            await self.currency(call.message, state, call.from_user)
            return
        if call.data == '/join':
            await state.clear()
            dbuser = DBUser(self.db, call.from_user)
            dbuser.update_active_book(book_id)
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_CONNECTED,
                    lang=call.from_user.language_code
                ).format(title=book.title.capitalize(), currency=book.currency),
            )
            return
        if call.data == '/delete':
            await state.clear()
            dbuser = DBUser(self.db, call.from_user)
            self.db.update_book(id=book.id, deleted=True)
            if dbuser.user_options['active_book'] == book.id:
                dbuser.update_active_book(0)
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_DELETED,
                    lang=call.from_user.language_code
                ).format(title=book.title.capitalize(), currency=book.currency),
            )
            await self.book(call.message, state, call.from_user)
            return
        await self._invalid_request(call.message, state)

    async def title(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(BookState.title)
        from_user = from_user or message.from_user
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_ADD_TITLE,
                lang=from_user.language_code
            ),
        )

    async def title_message(self, message: Message, state: FSMContext) -> None:
        title = re.sub('\s{2,}', ' ', message.text.strip().lower())
        if len(title) > 31:
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_TITLE_TOO_LONG,
                    lang=message.from_user.language_code
                ),
            )
            return
        if len(title) < 2:
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_TITLE_TOO_SHORT,
                    lang=message.from_user.language_code
                ),
            )
            return
        if title.startswith('/'):
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_TITLE_AVOID_SLASH,
                    lang=message.from_user.language_code
                ),
            )
            return
        book = self.db.get_book_by(
            user_id=message.from_user.id,
            title=title,
            deleted=False
        )
        if book:
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_ALREADY_EXISTS,
                    lang=message.from_user.language_code
                ),
            )
            return
        data = await state.get_data()
        if data['book'] == '/new':
            await state.update_data(title=title)
            await self.currency(message, state, message.from_user)
            return
        book_id = int(data['book'])
        book = self.db.get_book_by(
            user_id=message.from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            await self._invalid_request(message, state)
            return
        self.db.update_book(id=book_id, title=title)       
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_TITLE_UPDATED,
                lang=message.from_user.language_code
            ),
        )
        await self.action(message, state, message.from_user)

    async def currency(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(BookState.currency)
        button_groups = []
        buttons = [
            InlineKeyboardButton(
                text=currency,
                callback_data=currency
            ) for currency in settings.CURRENCIES
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 3:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_SET_CURRENCY,
                lang=message.from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def currency_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        currency = call.data
        if currency not in settings.CURRENCIES:
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_CURRENCY_invalid_request,
                    lang=call.from_user.language_code
                ),
            )
            return
        await state.update_data(currency=currency)
        data = await state.get_data()
        if data['book'] == '/new':
            await state.clear()
            book_ids = self.db.add_book(
                user_id=call.from_user.id,
                title=data['title'],
                currency=currency,
                created=datetime.utcnow(),
            )    
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_SUCCESSFULLY_CREATED,
                    lang=call.from_user.language_code
                ).format(title=data['title'].capitalize(), currency=data['currency'], book_uid=book_ids['book_uid']),
            )
            await self.book(call.message, state, call.from_user)
            return
        book_id = int(data['book'])
        book = self.db.get_book_by(
            user_id=call.from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            await self._invalid_request(call.message, state)
            return
        self.db.update_book(id=book_id, currency=currency)       
        await call.message.answer(
            text=__(
                text_dict=messages.BOOKS_CURRENCY_UPDATED,
                lang=call.from_user.language_code
            ),
        )
        await self.action(call.message, state, call.from_user)

    async def join(self, message: Message, state: FSMContext) -> None:
        """Join current user to the book."""
        request = re.sub('\s{2,}', ' ', message.text.strip()).split()
        if len(request) != 2:
            await self._invalid_request(message, state)
            return
        book_uid = request[1]
        book = self.db.get_book_by(book_uid=book_uid, deleted=False)
        if not book:
            await self._invalid_request(message, state)
            return
        dbuser = DBUser(self.db, message.from_user)
        dbuser.update_active_book(book.id)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_CONNECTED,
                lang=message.from_user.language_code
            ).format(title=book.title.capitalize(), currency=book.currency),
        )
