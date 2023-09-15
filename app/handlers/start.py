"""Handlers for /start workflow."""

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers import HandlerBase
from utils import messages
from utils import models
from utils import __


class Start(HandlerBase):
    """Handler class for /start workflow."""

    def __init__(self, db: models.DB, dp: Dispatcher) -> None:
        super().__init__(db)
        dp.message.register(self.start, Command('start'))

    async def start(
        self,
        message: Message,
        state: FSMContext
    ) -> None:
        """Entrypoint for /start' command."""
        await state.clear()
        await message.answer(
            text=__(
                text_dict=messages.START,
                lang=message.from_user.language_code
            ),
        )
