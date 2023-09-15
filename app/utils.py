"""Some fixed stuff here."""

import messages

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

def __(text_dict: dict[str, str], lang: str = 'en'):
    """Get message text."""
    if lang in text_dict:
        return text_dict[lang]
    return text_dict['default']
