from typing import Optional

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

import messages
import models
from utils import __, DBUser, LANGUAGES


class StartState(StatesGroup):
    start = State()


class Start:
    """Handlers for /start workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.start, Command('start'))
        router.callback_query.register(self.start_callback, StartState.start)

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(text='Invalid request.')

    async def start(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.clear()
        await state.set_state(StartState.start)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        button_groups = []
        buttons = [
            InlineKeyboardButton(
                text=LANGUAGES[language], callback_data=language
            ) for language in LANGUAGES
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 3:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.START,
                lang=dbuser.user_options['hl']
            ),
            reply_markup=keyboard_inline,
        )

    async def start_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        dbuser = DBUser(self.db, call.from_user)
        if call.data in LANGUAGES:
            dbuser.update_language(call.data)
        await self.start(call.message, state, call.from_user)
