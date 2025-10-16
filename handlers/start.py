from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboards.main_menu import main_menu
from keyboards.admin_menu import admin_menu
from keyboards.partner_menu import partner_menu
from config import ADMIN_IDS
from database.queries import get_or_create_user, set_referrer

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    uid = message.from_user.id
    # Handle referral code in start params
    if message.text and '?start=ref' in message.text:
        try:
            ref_code = message.text.split('ref%3D')[1].strip()
            await set_referrer(uid, ref_code)
        except Exception:
            pass  # ignore ref errors
    
    # Create or get user
    user = await get_or_create_user(uid)

    if message.from_user and message.from_user.id in ADMIN_IDS:
        await message.answer("Admin panelga xush kelibsiz.", reply_markup=admin_menu)
        return
    
    # Show partner menu if user is partner
    if user.is_partner:
        await message.answer("Hamkor panelga xush kelibsiz.", reply_markup=partner_menu)
        return
    
    # Regular user menu
    await message.answer("Assalomu alaykum! Velobike botga xush kelibsiz.", reply_markup=main_menu)
