from aiogram import Router
from aiogram.types import Message, ContentType, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from database.queries import register_partner, update_user_profile, create_bike_for_partner, get_or_create_user, partner_balance, list_partner_payouts
from config import ADMIN_IDS

router = Router()

# Very small in-memory FSM per-user (for scaffold). For production use FSM storage.
_partner_state = {}


@router.message(lambda msg: msg.text and 'hamkor' in msg.text.lower())
async def become_partner(message: Message):
    _partner_state[message.from_user.id] = {'step': 'name'}
    await message.answer("Hamkor bo'lish uchun ismingizni va familiyangizni yuboring:")


@router.message()
async def partner_steps(message: Message):
    uid = message.from_user.id
    state = _partner_state.get(uid)
    if not state:
        return

    step = state.get('step')
    if step == 'name':
        # parse name
        # Expect full name: Familya Ism Otasining_ismi (example: Abrorov Abror Abrorovich)
        parts = (message.text or '').split(None, 1)
        state['first_name'] = parts[0]
        state['last_name'] = parts[1] if len(parts) > 1 else ''
        state['step'] = 'phone'
        await message.answer('Telefon raqamingizni yuboring (faqat raqam):')
        return

    if step == 'phone':
        phone = (message.text or '').strip()
        state['phone'] = phone
        state['step'] = 'city'
        await message.answer("Qaysi shahardan ekanligingiz? Iltimos shahar nomini yuboring (masalan: Tashkent yoki Namangan)")
        return

    if step == 'city':
        state['city'] = (message.text or '').strip()
        # ask for location via Telegram location button
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Share location", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
        state['step'] = 'location'
        await message.answer('Iltimos, joylashuvingizni ulashing ("Share location" tugmasini bosing):', reply_markup=kb)
        return

    if step == 'location' and message.location:
        state['lat'] = message.location.latitude
        state['lon'] = message.location.longitude
        state['step'] = 'passport'
        await message.answer("Passport yoki shaxsiy ID raqamini yuboring:", reply_markup=ReplyKeyboardRemove())
        return

    if step == 'passport':
        state['passport_id'] = (message.text or '').strip()
        state['step'] = 'photo'
        await message.answer('Velosiped rasmini yuboring:')
        return

    if step == 'photo' and message.content_type == ContentType.PHOTO:
        # take highest resolution
        photo = message.photo[-1]
        file_id = photo.file_id

        # create or update partner user (ensure DB user exists)
        user = await get_or_create_user(uid)
        await register_partner(uid)
        await update_user_profile(uid, first_name=state.get('first_name'), last_name=state.get('last_name'), phone=state.get('phone'), lat=state.get('lat'), lon=state.get('lon'), passport_id=state.get('passport_id'))

        # create bike record under partner
        bike = await create_bike_for_partner(partner_id=uid, name=f"Partner bike {uid}", price_per_hour=0.0, image_file_id=file_id)

        # notify admin(s)
        for aid in ADMIN_IDS:
            try:
                await message.bot.send_photo(aid, photo=file_id, caption=f"Yangi hamkor: {state.get('first_name')} {state.get('last_name')}\nTel: {state.get('phone')}\nBike ID: {bike.id}")
            except Exception:
                pass

        await message.answer('Rahmat, arizangiz qabul qilindi. Adminlar bilan bog\'lanamiz.')
        _partner_state.pop(uid, None)
        # show current balance/earnings to partner
        try:
            bal = await partner_balance(uid)
            await message.answer(f"Sizning jami daromadingiz: {bal['earned']}, to'langan: {bal['paid']}, balans: {bal['balance']}")
        except Exception:
            pass
        return

    # fallback
    await message.answer('Iltimos, ko‘rsatmalarga rioya qiling yoki /start ni bosing.')


@router.message(lambda msg: msg.text and msg.text.startswith('/my_earnings'))
async def cmd_my_earnings(message: Message):
    uid = message.from_user.id
    # ensure partner
    res = await partner_balance(uid)
    payouts = await list_partner_payouts(uid)
    lines = [f"Earned: {res['earned']}, Paid: {res['paid']}, Balance: {res['balance']}"]
    for p in payouts:
        lines.append(f"{p.id}: {p.amount} at {p.created_at}")
    await message.answer('\n'.join(lines))
