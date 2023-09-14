"""Handlers for telegram bot events."""

import functools
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton

import messages
import models
from utils import __, DBUser


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
