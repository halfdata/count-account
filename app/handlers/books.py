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

import messages
import models
import utils
from utils import __, DBUser


class BooksState(StatesGroup):
    book = State()
    action = State()
    title = State()
    currency = State()
    parent_category = State()
    category = State()
    category_title = State()


class Books:
    """Handlers for /books workflow."""
    db: models.DB

    def __init__(self, db: models.DB, dp: Dispatcher, router: Router) -> None:
        self.db = db
        dp.message.register(self.books, Command('books'))
        router.callback_query.register(self.books_callback, BooksState.book)
        router.callback_query.register(self.actions_callback, BooksState.action)
        router.message.register(self.title_message, BooksState.title)
        router.callback_query.register(self.currency_callback, BooksState.currency)
        router.callback_query.register(self.categories_callback, BooksState.category)
        router.message.register(self.category_title_message, BooksState.category_title)
        dp.message.register(self.join, Command('join'))

    async def _invalid_request(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(text='Invalid request.')

    def _back_button(self):
        return InlineKeyboardButton(text='Back', callback_data='/back')

    async def books(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.clear()
        await state.set_state(BooksState.book)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
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
                lang=dbuser.user_options['hl']
            ),
            reply_markup=keyboard_inline,
        )

    async def books_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        if call.data == '/new':
            await state.update_data(book='/new')
            await self.title(call.message, state, call.from_user)
        else:
            book_id = int(call.data)
            await state.update_data(book=book_id)
            await self.actions(call.message, state, call.from_user)

    async def actions(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(BooksState.action)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
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
                InlineKeyboardButton(text='Edit Title', callback_data='/update_title'),
                InlineKeyboardButton(text='Edit Currency', callback_data='/update_currency'),
                InlineKeyboardButton(text='Edit Categories', callback_data='/update_categories'),
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
                lang=dbuser.user_options['hl']
            ).format(title=book.title.capitalize(), currency=book.currency, book_uid=book.book_uid),
            reply_markup=keyboard_inline,
        )

    async def actions_callback(self, call: CallbackQuery, state: FSMContext) -> None:
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
            await self.categories(call.message, state, call.from_user)
            return
        if call.data == '/join':
            await state.clear()
            dbuser = DBUser(self.db, call.from_user)
            dbuser.update_active_book(book_id)
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_CONNECTED,
                    lang=dbuser.user_options['hl']
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
                    lang=dbuser.user_options['hl']
                ).format(title=book.title.capitalize(), currency=book.currency),
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
        await state.set_state(BooksState.title)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_ADD_TITLE,
                lang=dbuser.user_options['hl']
            ),
        )

    async def title_message(self, message: Message, state: FSMContext) -> None:
        dbuser = DBUser(self.db, message.from_user)
        title = re.sub('\s{2,}', ' ', message.text.strip().lower())
        if len(title) > 31:
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_TITLE_TOO_LONG,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        if len(title) < 2:
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_TITLE_TOO_SHORT,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        if title.startswith('/'):
            await message.answer(
                text=__(
                    text_dict=messages.BOOKS_TITLE_AVOID_SLASH,
                    lang=dbuser.user_options['hl']
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
                    lang=dbuser.user_options['hl']
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
                lang=dbuser.user_options['hl']
            ),
        )
        await self.actions(message, state, message.from_user)

    async def currency(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(BooksState.currency)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        button_groups = []
        buttons = [
            InlineKeyboardButton(
                text=currency,
                callback_data=currency
            ) for currency in utils.CURRENCIES
        ]
        for button in buttons:
            if len(button_groups) < 1 or len(button_groups[-1]) > 3:
                button_groups.append([])
            button_groups[-1].append(button)
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        await message.answer(
            text=__(
                text_dict=messages.BOOKS_SET_CURRENCY,
                lang=dbuser.user_options['hl']
            ),
            reply_markup=keyboard_inline,
        )

    async def currency_callback(self, call: CallbackQuery, state: FSMContext) -> None:
        await call.message.edit_reply_markup(reply_markup=None)
        dbuser = DBUser(self.db, call.from_user)
        currency = call.data
        if currency not in utils.CURRENCIES:
            await call.message.answer(
                text=__(
                    text_dict=messages.BOOKS_CURRENCY_invalid_request,
                    lang=dbuser.user_options['hl']
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
                    lang=dbuser.user_options['hl']
                ).format(title=data['title'].capitalize(), currency=data['currency'], book_uid=book_ids['book_uid']),
            )
            await self.books(call.message, state, call.from_user)
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
                lang=dbuser.user_options['hl']
            ),
        )
        await self.actions(call.message, state, call.from_user)

    async def categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.update_data(parent_category=0)
        await self._categories(message, state, from_user)

    async def _categories(
        self,
        message: Message,
        state: FSMContext,
        from_user: Optional[User] = None
    ) -> None:
        await state.set_state(BooksState.category)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
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
        if parent_category:
            button_groups.append([
                InlineKeyboardButton(text="Edit Title", callback_data='/update_title'),
                InlineKeyboardButton(text="Remove", callback_data='/delete'),
            ])
        button_groups.append([
            InlineKeyboardButton(text="+ Add Category", callback_data='/new'),
            self._back_button()
        ])
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=button_groups)
        if not parent_category:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_WELCOME,
                    lang=dbuser.user_options['hl']
                ),
                reply_markup=keyboard_inline,
            )
        else:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_WELCOME_TO_CATEGORY,
                    lang=dbuser.user_options['hl']
                ).format(title=parent_category.title.capitalize()),
                reply_markup=keyboard_inline,
            )

    async def categories_callback(self, call: CallbackQuery, state: FSMContext) -> None:
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
        parent_category = None
        if 'parent_category' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
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
                        lang=dbuser.user_options['hl']
                    ).format(title=category.title.capitalize()),
                )
            else:
                await state.update_data(parent_category=0)
            await self._categories(call.message, state, call.from_user)
            return
        if call.data == '/back':
            if not parent_category:
                await self.actions(call.message, state, call.from_user)
                return
            category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
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
        await state.set_state(BooksState.category_title)
        from_user = from_user or message.from_user
        dbuser = DBUser(self.db, from_user)
        await message.answer(
            text=__(
                text_dict=messages.CATEGORIES_ADD_TITLE,
                lang=dbuser.user_options['hl']
            ),
        )

    async def category_title_message(self, message: Message, state: FSMContext) -> None:
        dbuser = DBUser(self.db, message.from_user)
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
        title = re.sub('\s{2,}', ' ', message.text.strip().lower())
        if len(title) > 31:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_TITLE_TOO_LONG,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        if len(title) < 2:
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_TITLE_TOO_SHORT,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        if title.startswith('/'):
            await message.answer(
                text=__(
                    text_dict=messages.CATEGORIES_TITLE_AVOID_SLASH,
                    lang=dbuser.user_options['hl']
                ),
            )
            return
        parent_category = None
        if 'parent_category' in data:
            parent_category = self.db.get_category_by(
                book_id=book.id,
                id=int(data['parent_category']),
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
                    lang=dbuser.user_options['hl']
                ).format(title=title.capitalize()),
            )
            return
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
                    lang=dbuser.user_options['hl']
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
                lang=dbuser.user_options['hl']
            ),
        )
        await self._categories(message, state, message.from_user)

    async def join(self, message: Message, state: FSMContext) -> None:
        """Join current user to the book."""
        await state.clear()
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
                lang=dbuser.user_options['hl']
            ).format(title=book.title.capitalize(), currency=book.currency),
        )
