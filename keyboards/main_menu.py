from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Ijaraga olish')],
    [KeyboardButton(text='Hamkorlik')]
], resize_keyboard=True)
