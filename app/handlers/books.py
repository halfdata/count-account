"""Handlers for reports workflow."""

import re
from datetime import datetime
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

from handlers import HandlerBase, DBUser
from utils import messages
from utils import models
from utils import __, CURRENCIES, DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES
from utils import CategoryType


class BooksState(StatesGroup):
    """State for books."""
    book = State()
    action = State()
    shared_action = State()
    title = State()
    currency = State()
    import_categories = State()
    category_type = State()
    parent_category = State()
    category = State()
    category_title = State()


class Books(HandlerBase):
    """Handler class for /books workflow."""

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        super().__init__(db)
        dp.message.register(self.books, Command('books'))
        router.callback_query.register(self.books_callback, BooksState.book)
        router.callback_query.register(self.actions_callback, BooksState.action)
        router.callback_query.register(self.shared_actions_callback, BooksState.shared_action)
        router.message.register(self.title_message, BooksState.title)
        router.callback_query.register(self.currency_callback, BooksState.currency)
        router.callback_query.register(self.import_categories_callback, BooksState.import_categories)
        router.callback_query.register(self.category_type_callback, BooksState.category_type)
        router.callback_query.register(self.categories_callback, BooksState.category)
        router.message.register(self.category_title_message, BooksState.category_title)
        dp.message.register(self.join, Command('join'))

    async def books(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Entrypoint for '/book' command."""
        await state.clear()
        await state.set_state(BooksState.book)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        books = self.db.get_books_by(
            user_id=from_user.id,
            deleted=False
        )

        button_groups = []
        buttons = []
        for book in books:
            if book.id == dbuser.user_options['active_book']:
                selected_mark = '✅ '
            else:
                selected_mark = ''
            buttons.append(
                InlineKeyboardButton(
                    text=f'{selected_mark}{book.title}',
                    callback_data=str(book.id)
                )
            )
        shared_books = self.db.get_shared_books_by(
            user_id=from_user.id,
            disabled=False,
            deleted=False
        )
        for book in shared_books:
            if book.book_id == dbuser.user_options['active_book']:
                selected_mark = '✅ '
            else:
                selected_mark = ''
            buttons.append(
                InlineKeyboardButton(
                    text=f'{selected_mark}{book.title}',
                    callback_data=f'shared-{book.id}'
                )
            )
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 2:
                button_groups.append([])
            button_groups[-1].append(button)
        button_groups.append([
            InlineKeyboardButton(
                text=__(messages.BUTTON_ADD_BOOK, lang=from_user.language_code),
                callback_data='/new'
            )
        ])
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_WELCOME,
                lang=from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def books_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for ook selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        if call.data == '/new':
            await state.update_data(book='/new')
            await self.title(call.message, state, call.from_user)
        elif call.data.startswith('shared-'):
            shared_book_id = int(call.data.replace('shared-', ''))
            await state.update_data(book=shared_book_id)
            await self.shared_actions(call.message, state, call.from_user)
        else:
            book_id = int(call.data)
            await state.update_data(book=book_id)
            await self.actions(call.message, state, call.from_user)

    async def shared_actions(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays actions for shared book."""
        await state.set_state(BooksState.shared_action)
        from_user = from_user or message.from_user
        data = await state.get_data()
        shared_book_id = int(data['book'])
        shared_book = self.db.get_shared_book_by(
            id=shared_book_id,
            user_id=from_user.id,
            disabled=False,
            deleted=False
        )
        if not shared_book:
            await self._invalid_request(message, state)
            return
        button_groups = [
            [
                InlineKeyboardButton(
                    text=__(messages.BUTTON_JOIN, lang=from_user.language_code),
                    callback_data='/join'
                ),
                InlineKeyboardButton(
                    text=__(messages.BUTTON_DISCONNECT, lang=from_user.language_code),
                    callback_data='/disconnect'
                ),
                self.back_button(from_user.language_code),
            ],
        ]
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_SELECTED,
                lang=from_user.language_code
            ).format(
                title=shared_book.title,
                currency=shared_book.currency,
                book_uid=shared_book.book_uid
            ),
            reply_markup=keyboard_inline,
        )

    async def shared_actions_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for actions for shared book."""
        await call.message.edit_reply_markup(reply_markup=None)
        dbuser = DBUser(self.db, call.from_user)
        data = await state.get_data()
        shared_book_id = int(data['book'])
        shared_book = self.db.get_shared_book_by(
            id=shared_book_id,
            user_id=call.from_user.id,
            disabled=False,
            deleted=False
        )
        if not shared_book:
            await self._invalid_request(call.message, state)
            return
        if call.data == '/back':
            await self.books(call.message, state, call.from_user)
            return
        if call.data == '/join':
            await state.clear()
            dbuser = DBUser(self.db, call.from_user)
            dbuser.update_active_book(shared_book.book_id)
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_CONNECTED,
                    lang=call.from_user.language_code
                ).format(
                    title=shared_book.title,
                    currency=shared_book.currency
                ),
            )
            return
        if call.data == '/disconnect':
            await state.clear()
            dbuser = DBUser(self.db, call.from_user)
            self.db.update_shared_book(id=shared_book_id, deleted=True)
            if dbuser.user_options['active_book'] == shared_book.book_id:
                dbuser.update_active_book(0)
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_DISCONNECTED,
                    lang=call.from_user.language_code
                ).format(
                    title=shared_book.title,
                    currency=shared_book.currency
                ),
            )
            await self.books(call.message, state, call.from_user)
            return
        await self._invalid_request(call.message, state)

    async def actions(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Display actions for own book."""
        await state.set_state(BooksState.action)
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
                InlineKeyboardButton(
                    text=__(messages.BUTTON_TITLE, lang=from_user.language_code),
                    callback_data='/update_title'
                ),
                InlineKeyboardButton(
                    text=__(messages.BUTTON_CURRENCY, lang=from_user.language_code),
                    callback_data='/update_currency'
                ),
                InlineKeyboardButton(
                    text=__(messages.BUTTON_CATEGORIES, lang=from_user.language_code),
                    callback_data='/update_categories'
                ),
            ],
            [
                InlineKeyboardButton(
                    text=__(messages.BUTTON_JOIN, lang=from_user.language_code),
                    callback_data='/join'
                ),
                InlineKeyboardButton(
                    text=__(messages.BUTTON_REMOVE, lang=from_user.language_code),
                    callback_data='/delete'
                ),
            ],
            [
                self.back_button(from_user.language_code),
            ]
        ]
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_SELECTED,
                lang=from_user.language_code
            ).format(title=book.title, currency=book.currency, book_uid=book.book_uid),
            reply_markup=keyboard_inline,
        )

    async def actions_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for actions for own book."""
        await call.message.edit_reply_markup(reply_markup=None)
        dbuser = DBUser(self.db, call.from_user)
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
            await self.books(call.message, state, call.from_user)
            return
        if call.data == '/update_title':
            await self.title(call.message, state, call.from_user)
            return
        if call.data == '/update_currency':
            await self.currency(call.message, state, call.from_user)
            return
        if call.data == '/update_categories':
            await self.category_type(call.message, state, call.from_user)
            return
        if call.data == '/join':
            await state.clear()
            dbuser = DBUser(self.db, call.from_user)
            dbuser.update_active_book(book_id)
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_CONNECTED,
                    lang=call.from_user.language_code
                ).format(title=book.title, currency=book.currency),
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
                ).format(title=book.title, currency=book.currency),
            )
            await self.books(call.message, state, call.from_user)
            return
        await self._invalid_request(call.message, state)

    async def title(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays message and ask user to enter book title."""
        await state.set_state(BooksState.title)
        from_user = from_user or message.from_user
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_ADD_TITLE,
                lang=from_user.language_code
            ),
        )

    async def title_message(self, message: Message, state: FSMContext) -> None:
        """Handles the book title entered by user."""
        title = re.sub(r'\s{2,}', ' ', message.text.strip())
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
        await self.actions(message, state, message.from_user)

    async def currency(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays currency selector."""
        await state.set_state(BooksState.currency)
        from_user = from_user or message.from_user
        button_groups = []
        buttons = [
            InlineKeyboardButton(
                text=currency,
                callback_data=currency
            ) for currency in CURRENCIES
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 3:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_SET_CURRENCY,
                lang=from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def currency_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for currency selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        currency = call.data
        if currency not in CURRENCIES:
            self._invalid_request(call.message, state=state)
            return
        await state.update_data(currency=currency)
        data = await state.get_data()
        if data['book'] == '/new':
            await self.import_categories(call.message, state, call.from_user)
            return
        book_id = int(data['book'])
        book = self.db.get_book_by(
            user_id=call.from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            await self._invalid_request(call.message, state=state)
            return
        self.db.update_book(id=book_id, currency=currency)       
        await call.message.answer(
            text=__(
                text_dict=messages.BOOKS_CURRENCY_UPDATED,
                lang=call.from_user.language_code
            ),
        )
        await self.actions(call.message, state, call.from_user)

    async def import_categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Ask user either import default categories or not."""
        await state.set_state(BooksState.import_categories)
        from_user = from_user or message.from_user
        buttons = [
            InlineKeyboardButton(
                text=__(messages.BUTTON_YES, lang=from_user.language_code),
                callback_data='/yes'
            ),
            InlineKeyboardButton(
                text=__(messages.BUTTON_NO, lang=from_user.language_code),
                callback_data='/no'
            ),
        ]
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_CREATE_DEFAULT_CATEGORIES,
                lang=from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def import_categories_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for import_categories."""
        await call.message.edit_reply_markup(reply_markup=None)
        data = await state.get_data()
        await state.clear()
        default_expense_categories = {}
        default_income_categories = {}
        if call.data == '/yes':
            default_expense_categories=__(
                text_dict=DEFAULT_EXPENSE_CATEGORIES,
                lang=call.from_user.language_code
            )
            default_income_categories=__(
                text_dict=DEFAULT_INCOME_CATEGORIES,
                lang=call.from_user.language_code
            )
        book_ids = self.db.add_book(
            user_id=call.from_user.id,
            title=data['title'],
            currency=data['currency'],
            created=datetime.utcnow(),
            default_income_categories=default_income_categories,
            default_expense_categories=default_expense_categories
        )
        await call.message.answer(
            text=__(
                text_dict=messages.BOOKS_SUCCESSFULLY_CREATED,
                lang=call.from_user.language_code
            ).format(
                title=data['title'],
                currency=data['currency'],
                book_uid=book_ids['book_uid']
            ),
        )
        await self.books(call.message, state, call.from_user)
        return

    async def category_type(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays category type selector."""
        await state.set_state(BooksState.category_type)
        from_user = from_user or message.from_user
        buttons = [
            InlineKeyboardButton(
                text=__(messages.BUTTON_INCOME, lang=from_user.language_code),
                callback_data=CategoryType.INCOME.name
            ),
            InlineKeyboardButton(
                text=__(messages.BUTTON_EXPENSE, lang=from_user.language_code),
                callback_data=CategoryType.EXPENSE.name
            ),
        ]
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=[
            buttons,
            [self.back_button(from_user.language_code)]
        ])
        await message.answer(
            text=__(
                text_dict=messages.CATEGORIES_TYPE_WELCOME,
                lang=from_user.language_code
            ),
            reply_markup=keyboard_inline,
        )

    async def category_type_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for category type selector."""
        await call.message.edit_reply_markup(reply_markup=None)
        if call.data == '/back':
            await self.actions(call.message, state, call.from_user)
            return
        elif call.data == CategoryType.INCOME.name:
            await state.update_data(category_type=CategoryType.INCOME)
        else:
            await state.update_data(category_type=CategoryType.EXPENSE)
        await self.categories(call.message, state, call.from_user)
        return

    async def categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays root category selector."""
        await state.update_data(parent_category=0)
        await self._categories(message, state, from_user)

    async def _categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays category selector."""
        await state.set_state(BooksState.category)
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
        parent_category = None
        if 'parent_category' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
                category_type=data['category_type'],
                deleted=False,
            )
        categories = self.db.get_categories_by(
            book_id=book.id,
            category_type=data['category_type'],
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
                    text=__(messages.BUTTON_TITLE, lang=from_user.language_code),
                    callback_data='/update_title'
                ),
                InlineKeyboardButton(
                    text=__(messages.BUTTON_REMOVE, lang=from_user.language_code),
                    callback_data='/delete'
                ),
            ])
        button_groups.append([
            InlineKeyboardButton(
                text=__(messages.BUTTON_ADD_CATEGORY, lang=from_user.language_code),
                callback_data='/new'
            ),
            self.back_button(from_user.language_code)
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
                ).format(title=parent_category.title),
                reply_markup=keyboard_inline,
            )

    async def categories_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        """Callback for category selector."""
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
        parent_category = None
        if 'parent_category' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
                category_type=data['category_type'],
                deleted=False
            )

        if call.data == '/new':
            await state.update_data(category='/new')
            await self.category_title(call.message, state, call.from_user)
            return
        if call.data == '/update_title':
            await state.update_data(category=data['parent_category'])
            await self.category_title(call.message, state, call.from_user)
            return
        if call.data == '/delete':
            category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
                deleted=False
            )
            if category:
                self.db.delete_category(category.id)
                await state.update_data(parent_category=category.parent_id)
                await call.message.answer(
                    text=__(
                        text_dict=messages.CATEGORIES_DELETED,
                        lang=call.from_user.language_code
                    ).format(title=category.title),
                )
            else:
                await state.update_data(parent_category=0)
            await self._categories(call.message, state, call.from_user)
            return
        if call.data == '/back':
            if not parent_category:
                await self.category_type(call.message, state, call.from_user)
                return
            category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
                category_type=data['category_type'],
                deleted=False
            )
            if category:
                await state.update_data(parent_category=category.parent_id)
            else:
                await state.update_data(parent_category=0)
            await self._categories(call.message, state, call.from_user)
            return

        category_id = int(call.data)
        category = self.db.get_category_by(
            book_id=book.id,
            id=category_id,
            category_type=data['category_type'],
            deleted=False
        )
        if not category:
            await self._invalid_request(call.message, state)
            return
        await state.update_data(parent_category=category_id)
        await self._categories(call.message, state, call.from_user)

    async def category_title(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        """Displays message to request category title."""
        await state.set_state(BooksState.category_title)
        from_user = from_user or message.from_user
        await message.answer(
            text=__(
                text_dict=messages.CATEGORIES_ADD_TITLE,
                lang=from_user.language_code
            ),
        )

    async def category_title_message(self, message: Message, state: FSMContext) -> None:
        """Handles entered category title."""
        data = await state.get_data()
        book_id = int(data['book'])
        book = self.db.get_book_by(
            user_id=message.from_user.id,
            id=book_id,
            deleted=False
        )
        if not book:
            await self._invalid_request(message, state)
            return
        title = re.sub(r'\s{2,}', ' ', message.text.strip())
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
        if 'parent_category' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
                category_type=data['category_type'],
                deleted=False
            )
        category = self.db.get_category_by(
            book_id=book.id,
            parent_id=(0 if not parent_category else parent_category.id),
            category_type=data['category_type'],
            title=title,
            deleted=False
        )
        if category:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_ALREADY_EXISTS,
                    lang=message.from_user.language_code
                ).format(title=title),
            )
            return
        if data['category'] == '/new':
            self.db.add_category(
                book_id=book.id,
                category_type=data['category_type'],
                parent_id=(0 if not parent_category else parent_category.id),
                title=title,
                deleted=False
            )    
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_SUCCESSFULLY_CREATED,
                    lang=message.from_user.language_code
                ).format(title=title),
            )
            await self._categories(message, state, message.from_user)
            return
        category_id = int(data['category'])
        category = self.db.get_category_by(
            book_id=book.id,
            id=category_id,
            category_type=data['category_type'],
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

    async def join(self, message: Message, state: FSMContext) -> None:
        """Join current user to the book."""
        await state.clear()
        request = re.sub(r'\s{2,}', ' ', message.text.strip()).split()
        if len(request) != 2:
            await self._invalid_request(message, state)
            return
        book_uid = request[1]
        book = self.db.get_book_by(book_uid=book_uid, deleted=False)
        if not book:
            await self._invalid_request(message, state)
            return
        dbuser = DBUser(self.db, message.from_user)
        if book.user_id != dbuser.user.id:
            shared_book = self.db.get_shared_book_by(
                user_id=dbuser.user.id,
                book_id=book.id,
                deleted=False
            )
            if not shared_book:
                self.db.add_shared_book(
                    user_id=dbuser.user.id,
                    book_id=book.id,
                    disabled=False,
                    deleted=False
                )
            elif shared_book.disabled:
                await message.answer(
                    text=__(
                        text_dict=messages.BOOKS_DISABLED,
                        lang=message.from_user.language_code
                    ).format(title=book.title, currency=book.currency),
                )
                return
        dbuser.update_active_book(book.id)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_CONNECTED,
                lang=message.from_user.language_code
            ).format(title=book.title, currency=book.currency),
        )
        return
