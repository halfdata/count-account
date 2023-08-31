"""Defines class to work with database."""
from secrets import token_urlsafe
from typing import Any, Optional

from sqlalchemy import Table, Index, Column
from sqlalchemy import Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy import MetaData
from sqlalchemy import create_engine, Engine
from sqlalchemy import select, insert, update, func, asc
from sqlalchemy.engine.base import Connection

class DB:
    """Definition of database tables."""
    metadata_obj: MetaData = MetaData()
    engine: Engine

    def __init__(self, database_url: str = 'sqlite:///db.sqlite3'):
        self.engine = create_engine(database_url)
        self._define_db_tables()
        self.metadata_obj.create_all(self.engine)

    def _define_db_tables(self) -> None:
        """Define required database tables."""
        self.log_table = Table(
            "log",
            self.metadata_obj,
            Column("id", Integer, primary_key=True),
            Column("user_id", Integer),
            Column("username", String(255)),
            Column("request", Text),
            Column("response", Text, default=''),
            Column("created", DateTime),
            Index("idx_log_user_id", "user_id"),
            Index("idx_log_username", "username"),
            Index("idx_log_created", "created"),
        )

        self.user_table = Table(
            "users",
            self.metadata_obj,
            Column("id", Integer, primary_key=True),
            Column("username", String(255)),
            Column("full_name", String(255)),
            Column("language", String(15)),
            Column("options", String(4095)),
            Index("idx_users_id", "id"),
        )
        self.book_table = Table(
            "books",
            self.metadata_obj,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("user_id", Integer),
            Column("book_uid", String(255)),
            Column("title", String(1023)),
            Column("currency", String(15)),
            Column("created", DateTime),
            Column("deleted", Boolean, default=False),
            Index("idx_books_user_id", "user_id"),
            Index("idx_books_book_uid", "book_uid"),
        )
        self.category_table = Table(
            "categories",
            self.metadata_obj,
            Column("id", Integer, primary_key=True),
            Column("parent_id", Integer, default=0),
            Column("book_id", Integer),
            Column("title", String(255)),
            Column("deleted", Boolean, default=False),
            Index("idx_categories_parent_id", "parent_id"),
            Index("idx_categories_book_title", "book_id", "title"),
        )
        self.expense_table = Table(
            "expenses",
            self.metadata_obj,
            Column("id", Integer, primary_key=True),
            Column("user_id", Integer),
            Column("book_id", Integer),
            Column("category_id", Integer),
            Column("amount", Float),
            Column("year", Integer),
            Column("month", Integer),
            Column("day", Integer),
            Column("created", DateTime),
            Column("deleted", Boolean, default=False),
            Index("idx_expenses_user_id", "user_id"),
            Index("idx_expenses_book_id", "book_id"),
            Index("idx_expenses_category_id", "category_id"),
            Index("idx_expenses_created", "created"),
            Index("idx_expenses_date", "year", "month", "day"),
        )

    def add_log_record(self, **kwargs) -> int:
        """Insert new log record."""
        with self.engine.connect() as connection:
            id = connection.execute(
                insert(self.log_table).values(**kwargs)
            ).inserted_primary_key.id
            connection.commit()
        return id

    def update_log_record(self, id: int, **kwargs):
        """Update log record."""
        with self.engine.connect() as connection:
            connection.execute(update(self.log_table)
                .where(self.log_table.c.id == id)
                .values(**kwargs))
            connection.commit()

    def get_user_by(self, *,
                    id: Optional[int] = None,
                    username: Optional[str] = None) -> Any:
        """Get user from DB."""
        with self.engine.connect() as connection:
            statement = select(self.user_table)
            if id is not None:
                statement = statement.where(self.user_table.c.id == id)
            if username is not None:
                statement = statement.where(self.user_table.c.username == username)
            statement = statement.limit(1)
            user_record = connection.execute(statement).first()
        return user_record

    def add_user(self, **kwargs):
        """Insert new user."""
        with self.engine.connect() as connection:
            connection.execute(insert(self.user_table).values(**kwargs))
            connection.commit()

    def update_user(self, id: int, **kwargs):
        """Update user."""
        with self.engine.connect() as connection:
            connection.execute(update(self.user_table)
                .where(self.user_table.c.id == id)
                .values(**kwargs))
            connection.commit()

    def get_books_by(self, *,
                     user_id: Optional[int] = None,
                     deleted: Optional[bool] = None,
                     offset: Optional[int] = 0,
                     number: Optional[int] = 100) -> list[Any]:
        """Get books from DB."""
        with self.engine.connect() as connection:
            statement = (select(self.book_table)
                .order_by(self.book_table.c.created.desc(),
                          self.book_table.c.id.desc())
                .offset(offset)
                .limit(number))
            if user_id is not None:
                statement = statement.where(self.book_table.c.user_id == user_id)
            if deleted is not None:
                statement = statement.where(self.book_table.c.deleted == deleted)
            books = connection.execute(statement).all()
        return books

    def get_book_by(self, *,
                    id: Optional[int] = None,
                    user_id: Optional[int] = None,
                    book_uid: Optional[str] = None,
                    title: Optional[str] = None,
                    deleted: Optional[bool] = None) -> Any:
        """Get book from DB."""
        with self.engine.connect() as connection:
            statement = select(self.book_table)
            if id is not None:
                statement = statement.where(self.book_table.c.id == id)
            if user_id is not None:
                statement = statement.where(self.book_table.c.user_id == user_id)
            if book_uid is not None:
                statement = statement.where(self.book_table.c.book_uid == book_uid)
            if title is not None:
                statement = statement.where(self.book_table.c.title == title)
            if deleted is not None:
                statement = statement.where(self.book_table.c.deleted == deleted)
            statement = statement.limit(1)
            book_record = connection.execute(statement).first()
        return book_record

    def add_book(self, **kwargs) -> dict[str, Any]:
        """Insert new book and return its book_uid."""
        with self.engine.connect() as connection:
            id = connection.execute(
                insert(self.book_table).values(**kwargs)).inserted_primary_key.id
            book_uid = f'{id}:' + token_urlsafe(12)
            connection.execute(
                update(self.book_table)
                    .where(self.book_table.c.id == id)
                    .values(book_uid=book_uid))
            connection.commit()
        return {'id': id, 'book_uid': book_uid}

    def update_book(self, id: int, **kwargs):
        """Update book."""
        with self.engine.connect() as connection:
            connection.execute(update(self.book_table)
                .where(self.book_table.c.id == id)
                .values(**kwargs))
            connection.commit()

    def get_categories_by(self, *,
                        book_id: int,
                        parent_id: Optional[int] = None,
                        deleted: Optional[bool] = None,
                        offset: Optional[int] = 0,
                        number: Optional[int] = 100) -> list[Any]:
        """Get categories from DB."""
        with self.engine.connect() as connection:
            statement = (select(self.category_table)
                .where(self.category_table.c.book_id == book_id)
                .order_by(self.category_table.c.title.asc())
                .offset(offset)
                .limit(number))
            if parent_id is not None:
                statement = statement.where(self.category_table.c.parent_id == parent_id)
            if deleted is not None:
                statement = statement.where(self.category_table.c.deleted == deleted)
            categories = connection.execute(statement).all()
        return categories

    def get_category_by(self, *,
                        book_id: int,
                        id: Optional[int] = None,
                        parent_id: Optional[int] = None,
                        title: Optional[str] = None,
                        deleted: Optional[bool] = None) -> Any:
        """Get category from DB."""
        with self.engine.connect() as connection:
            statement = select(self.category_table).where(self.category_table.c.book_id == book_id)
            if id is not None:
                statement = statement.where(self.category_table.c.id == id)
            if parent_id is not None:
                statement = statement.where(self.category_table.c.parent_id == parent_id)
            if title is not None:
                statement = statement.where(self.category_table.c.title == title)
            if deleted is not None:
                statement = statement.where(self.category_table.c.deleted == deleted)
            statement = statement.limit(1)
            category_record = connection.execute(statement).first()
        return category_record

    def add_category(self, **kwargs):
        """Insert new category."""
        with self.engine.connect() as connection:
            category_id = connection.execute(
                insert(self.category_table).values(**kwargs)).inserted_primary_key.id
            connection.commit()
        return category_id

    def update_category(self, id: int, **kwargs):
        """Update category."""
        with self.engine.connect() as connection:
            connection.execute(update(self.category_table)
                .where(self.category_table.c.id == id)
                .values(**kwargs))
            connection.commit()

    def _delete_category(self, connection: Connection, id: int):
        """Delete category."""
        connection.execute(update(self.category_table)
            .where(self.category_table.c.id == id)
            .values(deleted=True))
        statement = select(self.category_table).where(self.category_table.c.parent_id == id)
        categories = connection.execute(statement).all()
        for category in categories:
            self._delete_category(connection, category.id)

    def delete_category(self, id: int):
        """Delete category."""
        with self.engine.connect() as connection:
            self._delete_category(connection, id)
            connection.commit()

    def add_expense(self, **kwargs):
        """Insert new expense."""
        with self.engine.connect() as connection:
            expense_id = connection.execute(
                insert(self.expense_table).values(**kwargs)).inserted_primary_key.id
            connection.commit()
        return expense_id

    def get_expenses_per_category(self, book_id: int, from_date: DateTime, to_date: DateTime):
        """Returns expenses groupped by categories within specified dates."""
        with self.engine.connect() as connection:
            statement = (select(
                    self.expense_table.c.category_id.label('category_id'),
                    self.category_table.c.title.label('category_title'),
                    func.sum(self.expense_table.c.amount).label('amount')
                )
                .select_from(self.expense_table)
                .join(self.category_table, self.expense_table.c.category_id == self.category_table.c.id)
                .where(self.expense_table.c.book_id == book_id)
                .where(self.expense_table.c.deleted == False)
                .where(self.expense_table.c.created >= from_date)
                .where(self.expense_table.c.created <= to_date)
                .group_by(self.expense_table.c.category_id)
                .order_by(asc('amount'))
            )
            expenses = connection.execute(statement).all()
        return expenses
