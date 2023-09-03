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


class SettingsState(StatesGroup):
    parameter = State()
    language = State()


class Settings:
    """Handlers for /books workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.settings, Command('settings'))
        router.callback_query.register(self.settings_callback, SettingsState.parameter)
        router.callback_query.register(self.languages_callback, SettingsState.language)

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(text='Invalid request.')

    def _back_button(self):
        return InlineKeyboardButton(text='Back', callback_data='/back')

    async def settings(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.clear()
        await state.set_state(SettingsState.parameter)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        button_groups = [
            [
                InlineKeyboardButton(
                    text='Edit Language',
                    callback_data='/language'
                ),
            ]
        ]
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.SETTINGS_WELCOME,
                lang=dbuser.user_options['hl']
            ).format(language=LANGUAGES[dbuser.user_options['hl']]),
            reply_markup=keyboard_inline,
        )

    async def settings_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        if call.data == '/language':
            await self.languages(call.message, state, call.from_user)
            return
        await self._invalid_request(call.message, state)

    async def languages(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(SettingsState.language)
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
        button_groups.append([
            self._back_button(),
        ])
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.SETTINGS_SELECT_LANGUAGE,
                lang=dbuser.user_options['hl']
            ).format(language=LANGUAGES[dbuser.user_options['hl']]),
            reply_markup=keyboard_inline,
        )

    async def languages_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        dbuser = DBUser(self.db, call.from_user)
        if call.data in LANGUAGES:
            dbuser.update_language(call.data)
            await call.message.answer(
                text=__(
                    text_dict=messages.SETTINGS_LANGUAGE_UPDATED,
                    lang=dbuser.user_options['hl']
                ).format(language=LANGUAGES[dbuser.user_options['hl']]),
            )
            await self.settings(call.message, state, call.from_user)
            return
        if call.data == '/back':
            await self.settings(call.message, state, call.from_user)
            return
        await self._invalid_request(call.message, state)
