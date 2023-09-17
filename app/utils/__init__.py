"""Some fixed stuff here."""

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
        'Коммунальные услуги': {
            'Интернет': {},
            'Телефон': {},
            'ТВ': {},
            'Вода': {},
            'Отопление': {},
            'Электричество': {},
            'Квартплата': {},
        },
        'Мебель': {},
        'Продукты питания': {},
        'Транспорт': {
            'Автобус': {},
            'Поезд': {},
            'Самолет': {},
            'Такси': {},
        }
    },
}

def __(text_dict: dict[str, str], lang: str = 'en'):
    """Get message text."""
    if lang in text_dict:
        return text_dict[lang]
    return text_dict['default']
