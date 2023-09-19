"""Some fixed stuff here."""

import enum
from typing import Any
from utils import messages

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

MONTH_LABELS = {
    1: messages.JANUARY,
    2: messages.FEBRUARY,
    3: messages.MARCH,
    4: messages.APRIL,
    5: messages.MAY,
    6: messages.JUNE,
    7: messages.JULY,
    8: messages.AUGUST,
    9: messages.SEPTEMBER,
    10: messages.OCTOBER,
    11: messages.NOVEMBER,
    12: messages.DECEMBER,
}

DEFAULT_EXPENSE_CATEGORIES = {
    'default': {
        'Automobile': {
            'Auto Parts': {},
            'Auto Service': {},
            'Car Rental': {},
            'Car Wash': {},
            'Gasoline': {},
        },
        'Beauty & Wellness': {},
        'Clothes & Shoes': {},
        'Cosmetics': {},
        'Electronics': {
            'Appliances': {},
            'Audio & Video': {},
            'Gadgets': {},
        },
        'Entertainment': {
            'Attractions': {},
            'Cinema': {},
            'Circus': {},
            'Concert': {},
            'Museum': {},
            'Show': {},
            'Sport Games': {},
            'Theater': {},
            'Waterpark': {},
        },
        'Furniture': {},
        'Gift & Presents': {},
        'Grocery': {},
        'Household Goods': {},
        'Kid\'s Activities': {},
        'Medicine': {
            'Drug Store': {},
            'Doctor': {},
            'Massage': {},
            'Medical Tests': {},
        },
        'Other': {},
        'Restaurants': {
            'Bar': {},
            'Cafe': {},
            'Street Food': {},
            'Take Away': {},
        },
        'Services': {
            'Administrative': {},
            'Delivery': {},
            'Tips': {},
        },
        'Sport Activities': {},
        'Stationery': {},
        'Transport': {
            'Airplane': {},
            'Autobus': {},
            'Public Transport': {},
            'Taxi': {},
            'Train': {},
            'Tram': {},
        },
        'Utilities': {
            'Electricity': {},
            'Heating': {},
            'Internet': {},
            'Media': {},
            'Telephone': {},
            'TV': {},
            'Water': {},
        },
    },
    'ru': {
        'Автомобиль': {
            'Автозапчасти': {},
            'Автомойка': {},
            'Автосервис': {},
            'Бензин': {},
            'Прокат Авто': {},
        },
        'Красота и Уход': {},
        'Одежда и Обувь': {},
        'Косметика': {},
        'Техника': {
            'Аудио & Видео': {},
            'Гаджеты': {},
            'Домашняя техника': {},
        },
        'Развлечения': {
            'Аквапарк': {},
            'Аттракционы': {},
            'Кино': {},
            'Концерт': {},
            'Музей': {},
            'Спортивные Игры': {},
            'Театр': {},
            'Цирк': {},
            'Шоу': {},
        },
        'Мебель': {},
        'Подарки': {},
        'Продукты': {},
        'Хозтовары': {},
        'Кружки и Секции': {},
        'Медицина': {
            'Анализы': {},
            'Доктор': {},
            'Лекарство': {},
            'Массаж': {},
        },
        'Другое': {},
        'Рестораны': {
            'Бар': {},
            'Еда На Вынос': {},
            'Кафе': {},
            'Уличная Еда': {},
        },
        'Услуги': {
            'Госуслуги': {},
            'Доставка': {},
            'Чаевые': {},
        },
        'Спорт': {},
        'Канцтовары': {},
        'Транспорт': {
            'Автобус': {},
            'Поезд': {},
            'Проездной': {},
            'Самолет': {},
            'Такси': {},
            'Трамвай': {},
        },
        'Коммунальные Услуги': {
            'Водоснабжение': {},
            'Интернет': {},
            'Квартплата': {},
            'Отопление': {},
            'ТВ': {},
            'Телефон': {},
            'Электричество': {},
        },
    },
}

def __(text_dict: dict[str, Any], lang: str = 'en') -> Any:
    """Get message text."""
    if lang in text_dict:
        return text_dict[lang]
    return text_dict['default']


class CategoryType(enum.Enum):
    """Types of categories."""
    EXPENSE = 'expense'
    INCOME = 'income'
