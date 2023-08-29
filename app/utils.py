def __(text_dict: dict[str, str], lang: str = 'en'):
    """Get message text."""
    if lang in text_dict:
        return text_dict[lang]
    return text_dict['default']

