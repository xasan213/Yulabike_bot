from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboards.main_menu import main_menu
from keyboards.admin_menu import admin_menu
from config import ADMIN_IDS

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    if message.from_user and message.from_user.id in ADMIN_IDS:
        await message.answer("Admin panelga xush kelibsiz.", reply_markup=admin_menu)
        return
    await message.answer("Assalomu alaykum! Velobike botga xush kelibsiz.", reply_markup=main_menu)
