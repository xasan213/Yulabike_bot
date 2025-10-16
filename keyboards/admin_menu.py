from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='/list_rentals')],
    [KeyboardButton(text='/assign_bike')],
    [KeyboardButton(text='/partner_earnings')]
], resize_keyboard=True)
