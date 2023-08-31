BOOKS_WELCOME = {
    'default': (
        'Hey. Let\'s configure books here. Select any existing book or tap '
        '<code>+ Add Book</code> to create a new one.'
    ),
}

BOOKS_ADD_TITLE = {
    'default': (
        'Please send the title of the book.'
    ),
}

BOOKS_TITLE_UPDATED = {
    'default': (
        'The title successfully updated.'
    ),
}

BOOKS_TITLE_TOO_SHORT = {
    'default': (
        'Hm. Seems the title is too short. Try to enter something longer.'
    ),
}

BOOKS_TITLE_TOO_LONG = {
    'default': (
        'Hm. Seems the title is too long. Try to enter something shorter.'
    ),
}

BOOKS_TITLE_AVOID_SLASH = {
    'default': (
        'Please do not start the title with <code>/</code> symbol. '
        'Try to enter something different.'
    ),
}

BOOKS_CURRENCY_NOT_FOUND = {
    'default': (
        'Hm. This currency doesn\'t exist.'
    ),
}

BOOKS_CURRENCY_UPDATED = {
    'default': (
        'The currency successfully updated.'
    ),
}

BOOKS_SUCCESSFULLY_CREATED = {
    'default': (
        'Book <strong>{title}</strong> (currency: <strong>{currency}</strong>) successfully created.\n'
        'Share the following command with people you want to join this book:\n\n'
        '<pre>/join {book_uid}</pre>\n\n'
        '<strong>Important!</strong> Everyone who knows this command can join the book.'
    ),
}

BOOKS_SELECTED = {
    'default': (
        'Book <strong>{title}</strong> (currency: <strong>{currency}</strong>) selected.\n'
        'Share the following command with people you want to join this book:\n\n'
        '<pre>/join {book_uid}</pre>\n\n'
        '<strong>Important!</strong> Everyone who knows this command can join the book.'
    ),
}

BOOKS_ALREADY_EXISTS = {
    'default': (
        'Book with this title already exists. '
        'Try to enter different title.'
    ),
}

BOOKS_SET_CURRENCY = {
    'default': (
        'Select the currency for the book.'
    ),
}

BOOKS_CONNECTED = {
    'default': (
        'You are joined to the book <strong>{title}</strong> '
        '(currency: <strong>{currency}</strong>). '
        'All further expenses will be saved into this book.'
    ),
}

BOOKS_DELETED = {
    'default': (
        'Book <strong>{title}</strong> (currency: <strong>{currency}</strong>) '
        'successfully removed.'
    ),
}

CATEGORIES_ACTIVE_BOOK_REQUIRED = {
    'default': 'Make sure that you are joined your own book. Currently you don\'t.',
}

CATEGORIES_ALREADY_EXISTS = {
    'default': 'Category <strong>{title}</strong> already exists.',
}

CATEGORIES_SUCCESSFULLY_CREATED = {
    'default': (
        'Category <strong>{title}</strong> successfully created.'
    ),
}

CATEGORIES_TITLE_UPDATED = {
    'default': (
        'The title successfully updated.'
    ),
}

CATEGORIES_TITLE_TOO_SHORT = {
    'default': (
        'Hm. Seems the title is too short. Try to enter something longer.'
    ),
}

CATEGORIES_TITLE_TOO_LONG = {
    'default': (
        'Hm. Seems the title is too long. Try to enter something shorter.'
    ),
}

CATEGORIES_TITLE_AVOID_SLASH = {
    'default': (
        'Please do not start the title with <code>/</code> symbol. '
        'Try to enter something different.'
    ),
}

CATEGORIES_DELETED = {
    'default': (
        'Category <strong>{title}</strong> (and its subcategories) '
        'successfully removed.'
    ),
}

CATEGORIES_WELCOME = {
    'default': (
        'Hey. Let\'s configure categories here. Select any existing category '
        'or tap <code>+ Add Category</code> to create a new one.'
    ),
}

CATEGORIES_WELCOME_TO_CATEGORY = {
    'default': (
        'You selected category <strong>{title}</strong>. Select any existing subcategory '
        'or tap <code>+ Add Category</code> to create a new one.'
    ),
}

CATEGORIES_ADD_TITLE = {
    'default': (
        'Please send the name of the category.'
    ),
}

EXPENSES_ACTIVE_BOOK_REQUIRED = {
    'default': 'Make sure that you are joined existing book. Currently you don\'t.',
}

EXPENSES_ADD_AMOUNT = {
    'default': (
        'Add <strong>{amount} {currency}</strong> to the book '
        '<strong>{book_title}</strong>.'
    ),
}

EXPENSES_ZERO_AMOUNT = {
    'default': (
        'Please enter non-zero amount.'
    ),
}

EXPENSES_CATEGORY_SELECT_CATEGORY = {
    'default': (
        'You selected <strong>{category_title}</strong> category. '
        'Select subcategory or click <strong>Submit</strong>.'
    ),
}

EXPENSES_ROOT_SELECT_CATEGORY = {
    'default': (
        'Select desired category or click <strong>Submit</strong> '
        'to add as uncategorized.'
    ),
}

EXPENSES_SUCCESSFULLY_CREATED_IN_CATEGORY = {
    'default': (
        '<strong>{amount} {currency}</strong> successfully added to '
        '<strong>{category_title}</strong> category of '
        '<strong>{book_title}</strong> book.'
    ),
}

EXPENSES_SUCCESSFULLY_CREATED = {
    'default': (
        '<strong>{amount} {currency}</strong> successfully added to '
        '<strong>{book_title}</strong> book.'
    ),
}

REPORTS_PER_CATEGORY_TITLE = {
    'default': 'Per category report, {book_title} ({currency}), period: {period}',
}

REPORTS_NO_DATA = {
    'default': 'No data for requested period.',
}

INVALID_REQUEST = {
    'default':  'Invalid request.',
}
