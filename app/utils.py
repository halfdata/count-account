import json
import models
import messages
from typing import Any
from aiogram.types import InlineKeyboardButton
from aiogram.types.user import User

LANGUAGES = {
    'en': 'English',
    'ru': 'Русский',
}

CURRENCIES = {
    'CAD': 'Canadian Dollar',
    'EUR': 'Euro',
    'PLN': 'Polish Zloty',
    'RUB': 'Russian Ruble',
    'SGD': 'Singaporean Dollar',
    'USD': 'US Dollar',
}

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


def back_button(hl: str = 'en'):
    return InlineKeyboardButton(
        text=__(messages.BUTTON_BACK, lang=hl),
        callback_data='/back'
    )

def __(text_dict: dict[str, str], lang: str = 'en'):
    """Get message text."""
    if lang in text_dict:
        return text_dict[lang]
    return text_dict['default']

