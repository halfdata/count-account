"""Handlers for telegram bot events."""

import json
import functools
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.types.user import User

from utils import messages
from utils import models
from utils import __


DEFAULT_USER_OPTIONS = {
    'active_book': 0,
    'hl': 'en',
}


class DBUser:
    """Works with user data in DB."""
    db: models.DB
    from_user: User
    user: Any
    user_options: dict[str, Any] = {}

    def __init__(self, db: models.DB, from_user: User) -> None:
        self.db = db
        self.from_user = from_user
        self.user = self.db.get_user_by(id=self.from_user.id)
        if not self.user:
            self.db.add_user(
                id=self.from_user.id,
                username=self.from_user.username,
                full_name=self.from_user.full_name,
                language=self.from_user.language_code,
                options=json.dumps(DEFAULT_USER_OPTIONS),
            )
            self.user = self.db.get_user_by(id=from_user.id)
        self.user_options = {key: DEFAULT_USER_OPTIONS[key] for key in DEFAULT_USER_OPTIONS}
        self.user_options.update(json.loads(self.user.options))

    def active_book(self) -> Any:
        """Returns active book for the user."""
        if not self.user_options['active_book']:
            return False
        book = self.db.get_book_by(
            id=self.user_options['active_book'],
            deleted=False
        )
        if not book:
            return False
        if book.user_id == self.from_user.id:
            return book
        shared_book = self.db.get_shared_book_by(
            book_id=self.user_options['active_book'],
            user_id=self.from_user.id,
            disabled=False,
            deleted=False
        )
        if shared_book:
            return book
        return False

    def update_active_book(self, book_id: int):
        """Update active book for current user."""
        self.user_options['active_book'] = book_id
        self.db.update_user(id=self.user.id, options=json.dumps(self.user_options))

    def update_language(self, language: str):
        """Update language for current user."""
        self.user_options['hl'] = language
        self.db.update_user(id=self.user.id, options=json.dumps(self.user_options))


class HandlerBase:
    """Base class for handlers."""
    db: models.DB

    def __init__(self, db: models.DB) -> None:
        self.db = db

    def active_book_required(func) -> Any:
        """Decorator that checks if current user has active book."""
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            message_call = args[0]
            if not(isinstance(message_call, CallbackQuery) or isinstance(message_call, Message)):
                exit('Invalid decorator usage.')
            state = kwargs['state']
            if 'from_user' in kwargs:
                from_user = kwargs['from_user']
            else:
                from_user = message_call.from_user
            dbuser = DBUser(self.db, from_user)
            book = dbuser.active_book()
            if not book:
                await state.clear()
                if isinstance(message_call, CallbackQuery):
                    message = message_call.message
                    await message.edit_reply_markup(reply_markup=None)
                else:
                    message = message_call
                await message.answer(
                    text=__(
                        text_dict=messages.ACTIVE_BOOK_REQUIRED,
                        lang=from_user.language_code
                    ),
                )
                return
            kwargs['book'] = book
            result = await func(self, *args, **kwargs)
            return result
        return wrapper

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        """Shows 'Invalid request' message."""
        await state.clear()
        await message.answer(text='Invalid request.')

    def back_button(self, hl: str = 'en') -> InlineKeyboardButton:
        """Returns 'back' button."""
        return InlineKeyboardButton(
            text=__(messages.BUTTON_BACK, lang=hl),
            callback_data='/back'
        )
