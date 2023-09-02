BOOKS_WELCOME = {
    'default': (
        'Hey. Let\'s configure books here. Select any existing book or tap '
        '<code>+ Add Book</code> to create a new one.'
    ),
    'ru': (
        'Давай настроим книги учета затрат. Выбери существующую книгу '
        'или тапни <code>+ Создать</code>, чтобы создать новую.'
    ),
}

BOOKS_ADD_TITLE = {
    'default': 'Please send the title of the book.',
    'ru': 'Отправьте название учетной книги.',
}

BOOKS_TITLE_UPDATED = {
    'default': 'The title successfully updated.',
    'ru': 'Название обновлено.',
}

BOOKS_TITLE_TOO_SHORT = {
    'default': 'Seems the title is too short. Try to enter something longer.',
    'ru': 'Кажется, название слишком короткое. Сделайте его чуток длиннее.',
}

BOOKS_TITLE_TOO_LONG = {
    'default': 'Seems the title is too long. Try to enter something shorter.',
    'ru': 'Кажется, название слишком длинное. Сделайте его чуток короче.',
}

BOOKS_TITLE_AVOID_SLASH = {
    'default': (
        'Please do not start the title with <code>/</code> symbol. '
        'Try to enter something different.'
    ),
    'ru': 'Не начинайте название с символа <code>/</code>.',
}

BOOKS_CURRENCY_NOT_FOUND = {
    'default': 'This currency doesn\'t exist.',
    'ru': 'Такая валюта не существует.',
}

BOOKS_CURRENCY_UPDATED = {
    'default': 'The currency successfully updated.',
    'ru': 'Валюта обновлена.',
}

BOOKS_SUCCESSFULLY_CREATED = {
    'default': (
        'Book <strong>{title}</strong> (currency: <strong>{currency}</strong>) successfully created.\n'
        'Share the following command with people you want to join this book:\n\n'
        '<pre>/join {book_uid}</pre>\n\n'
        '<strong>Important!</strong> Everyone who knows this command can join the book.'
    ),
    'ru': (
        'Учетная книга <strong>{title}</strong> (валюта: <strong>{currency}</strong>) создана.\n'
        'Если хотите дать кому-то возможность вносить в нее расходы, поделитесь командой:\n\n'
        '<pre>/join {book_uid}</pre>\n\n'
        '<strong>ВАЖНО!</strong> Любой, кто знает эту команду, может вносить расходы в эту книгу.'
    ),
}

BOOKS_SELECTED = {
    'default': (
        'Book <strong>{title}</strong> (currency: <strong>{currency}</strong>) selected.\n'
        'Share the following command with people you want to join this book:\n\n'
        '<pre>/join {book_uid}</pre>\n\n'
        '<strong>Important!</strong> Everyone who knows this command can join the book.'
    ),
    'ru': (
        'Вы выбрали учетную книгу <strong>{title}</strong> (валюта: <strong>{currency}</strong>).\n'
        'Если хотите дать кому-то возможность вносить в нее расходы, поделитесь командой:\n\n'
        '<pre>/join {book_uid}</pre>\n\n'
        '<strong>ВАЖНО!</strong> Любой, кто знает эту команду, может вносить расходы в эту книгу.'
    ),
}

BOOKS_ALREADY_EXISTS = {
    'default': 'Book with this title already exists. Try to enter different title.',
    'ru': 'Учетная книга с таким названием уже существует. Попробуйте другое название.',
}

BOOKS_SET_CURRENCY = {
    'default': 'Select the currency for the book.',
    'ru': 'Выберите валюту учетной книги.',
}

BOOKS_CONNECTED = {
    'default': (
        'You are joined to the book <strong>{title}</strong> '
        '(currency: <strong>{currency}</strong>). '
        'All further expenses will be saved into this book.'
    ),
    'ru': (
        'Вы активировали учетную книгу <strong>{title}</strong> '
        '(валюта: <strong>{currency}</strong>). '
        'Все расходы будут записываться в нее.'
    ),
}

BOOKS_DELETED = {
    'default': (
        'Book <strong>{title}</strong> (currency: <strong>{currency}</strong>) '
        'successfully removed.'
    ),
    'ru': (
        'Учетная книга <strong>{title}</strong> (валюта: <strong>{currency}</strong>) '
        'удалена.'
    ),
}

CATEGORIES_ACTIVE_BOOK_REQUIRED = {
    'default': 'Make sure that you are joined your own book. Currently you don\'t.',
    'ru': (
        'Кажется, вы не выбрали активную книгу. Сделайте это через меню '
        '<code>/books</code>.'
    ),
}

CATEGORIES_ALREADY_EXISTS = {
    'default': 'Category <strong>{title}</strong> already exists.',
    'ru': 'Категория <strong>{title}</strong> уже существует.',
}

CATEGORIES_SUCCESSFULLY_CREATED = {
    'default': 'Category <strong>{title}</strong> successfully created.',
    'ru': 'Категория <strong>{title}</strong> создана.',
}

CATEGORIES_TITLE_UPDATED = {
    'default': 'The title successfully updated.',
    'ru': 'Название обновлено.',
}

CATEGORIES_TITLE_TOO_SHORT = {
    'default': (
        'Hm. Seems the title is too short. Try to enter something longer.'
    ),
    'ru': 'Кажется, название слишком короткое. Сделайте его чуток длиннее.',
}

CATEGORIES_TITLE_TOO_LONG = {
    'default': (
        'Hm. Seems the title is too long. Try to enter something shorter.'
    ),
    'ru': 'Кажется, название слишком длинное. Сделайте его чуток короче.',
}

CATEGORIES_TITLE_AVOID_SLASH = {
    'default': (
        'Please do not start the title with <code>/</code> symbol. '
        'Try to enter something different.'
    ),
    'ru': 'Не начинайте название с символа <code>/</code>.',
}

CATEGORIES_DELETED = {
    'default': (
        'Category <strong>{title}</strong> (and its subcategories) '
        'successfully removed.'
    ),
    'ru': (
        'Категория <strong>{title}</strong> (и все подкатегории) удалены.'
    ),
}

CATEGORIES_WELCOME = {
    'default': (
        'Hey. Let\'s configure categories here. Select any existing category '
        'or tap <code>+ Add Category</code> to create a new one.'
    ),
    'ru': (
        'Давай настроим категории. Выбери существующую категорию '
        'или тапни <code>+ Создать</code>, чтобы создать новую.'
    ),
}

CATEGORIES_WELCOME_TO_CATEGORY = {
    'default': (
        'You selected category <strong>{title}</strong>. Select any existing subcategory '
        'or tap <code>+ Add Category</code> to create a new one.'
    ),
    'ru': (
        'Вы выбрали категорию <strong>{title}</strong>. Выберите подкатегорию '
        'или тапните <code>+ Создать</code>, чтобы создать новую.'
    ),
}

CATEGORIES_ADD_TITLE = {
    'default': 'Please send the name of the category.',
    'ru': 'Введите название категории.',
}

EXPENSES_ADD_AMOUNT = {
    'default': (
        'Add <strong>{amount} {currency}</strong> to the book '
        '<strong>{book_title}</strong>.'
    ),
    'ru': (
        'Добавляем <strong>{amount} {currency}</strong> в книгу учета '
        '<strong>{book_title}</strong>.'
    ),
}

EXPENSES_ZERO_AMOUNT = {
    'default': 'Please enter non-zero amount.',
    'ru': 'Введите ненулевое значение.',
}

EXPENSES_CATEGORY_SELECT_CATEGORY = {
    'default': (
        'You selected <strong>{category_title}</strong> category. '
        'Select subcategory or tap <strong>Submit</strong>.'
    ),
    'ru': (
        'Вы выбрали категорию <strong>{category_title}</strong>. '
        'Выберите подкатегорию или тапните <strong>Сохранить</strong>.'
    ),
}

EXPENSES_ROOT_SELECT_CATEGORY = {
    'default': (
        'Select desired category or click <strong>Submit</strong> '
        'to add as uncategorized.'
    ),
    'ru': (
        'Выберите категорию или тапните <strong>Сохранить</strong>, '
        'чтобы сохранить без категории.'
    ),
}

EXPENSES_SUCCESSFULLY_CREATED_IN_CATEGORY = {
    'default': (
        '<strong>{amount} {currency}</strong> successfully added to '
        '<strong>{category_title}</strong> category of '
        '<strong>{book_title}</strong> book.'
    ),
    'ru': (
        '<strong>{amount} {currency}</strong> добавлено в категорию '
        '<strong>{category_title}</strong> учетной книги '
        '<strong>{book_title}</strong>.'
    ),
}

EXPENSES_SUCCESSFULLY_CREATED = {
    'default': (
        '<strong>{amount} {currency}</strong> successfully added to '
        '<strong>{book_title}</strong> book.'
    ),
    'ru': (
        '<strong>{amount} {currency}</strong> добавлено в учетную книгу '
        '<strong>{book_title}</strong>.'
    ),
}

REPORTS_BOOK_AND_PERIOD = {
    'default': '{book_title} ({currency}), {period}',
    'ru': '{book_title} ({currency}), {period}',
}

REPORTS_NO_DATA = {
    'default': 'No data for requested period.',
    'ru': 'Данные за выбраный период отсутствуют.',
}

SETTINGS_WELCOME = {
    'default': (
        'Settings:\n\n'
        'Language: <strong>{language}</strong>\n\n'
        'Tap the button below to edit relevant parameter.'
    ),
    'ru': (
        'Настройки:\n\n'
        'Язык: <strong>{language}</strong>\n\n'
        'Тапните кнопку ниже, чтобы изменить соответствующие настройки.'
    ),
}

SETTINGS_SELECT_LANGUAGE = {
    'default': (
        'Current language is <strong>{language}</strong>. '
        'Tap the button below to set new language.'
    ),
    'ru': (
        'Текущий язык - <strong>{language}</strong>. '
        'Тапните кнопку ниже, чтобы изменить язык.'
    ),
}

SETTINGS_LANGUAGE_UPDATED = {
    'default': (
        'Current language successfully updated to <strong>{language}</strong>.'
    ),
    'ru': (
        'Язык сообщений изменен на <strong>{language}</strong>.'
    ),
}

ACTIVE_BOOK_REQUIRED = {
    'default': (
        'Make sure that you are joined existing book. You can do it through the menu '
        '<code>/books</code> or by sending relevant command.'
    ),
    'ru': (
        'Кажется, вы не выбрали активную книгу. Сделайте это через меню '
        '<code>/books</code>, или отправив соответствующую команду.'
    ),
}
