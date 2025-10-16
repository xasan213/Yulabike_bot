from aiogram import Router
from aiogram.types import Message, ContentType
from database.queries import get_or_create_user, create_rental, pick_main_bike, update_user_profile

router = Router()

# tiny per-user in-memory state. For production use FSM storage.
_state = {}


@router.message(lambda msg: msg.text and 'Ijaraga' in msg.text)
async def start_rental(message: Message):
    uid = message.from_user.id
    _state[uid] = {'step': 'name'}
    await message.answer('Iltimos, ismingiz va familiyangizni yuboring:')


@router.message()
async def customer_steps(message: Message):
    uid = message.from_user.id
    state = _state.get(uid)
    if not state:
        return
    step = state.get('step')
    if step == 'name':
        parts = (message.text or '').split(None, 1)
        state['first_name'] = parts[0]
        state['last_name'] = parts[1] if len(parts) > 1 else ''
        state['step'] = 'phone'
        await message.answer('Telefon raqamingizni yuboring (faqat raqam):')
        return

    if step == 'phone':
        state['phone'] = (message.text or '').strip()
        state['step'] = 'location'
        await message.answer('Joylashuvingizni yuboring (lokatsiya tugmasi orqali):')
        return

    if step == 'location' and message.location:
        state['lat'] = message.location.latitude
        state['lon'] = message.location.longitude
        state['step'] = 'passport'
        await message.answer("Passport yoki shaxsiy ID raqamini yuboring:")
        return

    if step == 'passport':
        state['passport_id'] = (message.text or '').strip()
        # finalize profile
        user = await get_or_create_user(uid)
        await update_user_profile(uid, first_name=state.get('first_name'), last_name=state.get('last_name'), phone=state.get('phone'), lat=state.get('lat'), lon=state.get('lon'), passport_id=state.get('passport_id'))

        # assign main bike to this user automatically
        bike = await pick_main_bike()
        if not bike:
            await message.answer('Kechirasiz, hozircha bosh velosiped mavjud emas, admin bilan bog\'laning.')
            _state.pop(uid, None)
            return

        rental = await create_rental(user.id, bike.id)
        if not rental:
            await message.answer('Velosipedni band qilishda xatolik yuz berdi.')
            _state.pop(uid, None)
            return

        await message.answer(f"Siz muvaffaqiyatli ijaraga oldingiz. Velosiped ID: {bike.id}, kodi: {bike.code}")
        _state.pop(uid, None)
        return

    # fallback
    await message.answer('Iltimos, ko‘rsatmalarga rioya qiling.')
