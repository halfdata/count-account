from typing import Optional

from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.user import User

import messages
import models
from utils import __


class Start:
    """Handlers for /start workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.start, Command('start'))

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
        from_user = from_user or message.from_user
        await message.answer(
            text=__(
                text_dict=messages.START,
                lang=from_user.language_code
            ),
        )
