from aiogram import Router
from aiogram.types import Message, ContentType, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from database.queries import get_or_create_user, create_rental, pick_main_bike, update_user_profile
from database.queries import set_referrer, count_referrals

router = Router()

# tiny per-user in-memory state. For production use FSM storage.
_state = {}


@router.message(lambda msg: msg.text and 'ijaraga' in msg.text.lower())
async def start_rental(message: Message):
    uid = message.from_user.id
    # detect referral code in message text (formats: 'ref:CODE' or '/start?ref=CODE')
    ref_code = None
    txt = (message.text or '')
    if 'ref:' in txt.lower():
        try:
            ref_code = txt.split('ref:')[1].strip().split()[0]
        except Exception:
            ref_code = None
    if '?ref=' in txt.lower():
        try:
            ref_code = txt.split('?ref=')[1].strip().split()[0]
        except Exception:
            ref_code = ref_code

    _state[uid] = {'step': 'name', 'ref_code': ref_code}
    await message.answer('Iltimos, ismingiz va familiyangizni yuboring:')


@router.message()
async def customer_steps(message: Message):
    uid = message.from_user.id
    state = _state.get(uid)
    if not state:
        return
    step = state.get('step')
    if step == 'name':
        # Expect full name: Familya Ism Otasining_ismi (example: Abrorov Abror Abrorovich)
        parts = (message.text or '').split(None, 1)
        state['first_name'] = parts[0]
        state['last_name'] = parts[1] if len(parts) > 1 else ''
        state['step'] = 'phone'
        await message.answer('Telefon raqamingizni yuboring (faqat raqam):')
        return

    if step == 'phone':
        state['phone'] = (message.text or '').strip()
        # ask for city (with example)
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
        # remove keyboard after getting location
        await message.answer("Passport yoki shaxsiy ID raqamini yuboring:", reply_markup=ReplyKeyboardRemove())
        return

    if step == 'passport':
        state['passport_id'] = (message.text or '').strip()
        # finalize profile
        user = await get_or_create_user(uid)
        await update_user_profile(uid, first_name=state.get('first_name'), last_name=state.get('last_name'), phone=state.get('phone'), lat=state.get('lat'), lon=state.get('lon'), passport_id=state.get('passport_id'))

        # if there was a referral code provided earlier, set referrer
        if state.get('ref_code'):
            try:
                await set_referrer(uid, state.get('ref_code'))
            except Exception:
                pass

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
        # show referral link for this user
        try:
            # ensure user has a referral code
            if not user.referral_code:
                # user was created earlier with a code, but ensure
                pass
            ref_link = f"https://t.me/{message.bot.username}?start=ref%3D{user.referral_code}"
            cnt = await count_referrals(user.telegram_id)
            await message.answer(f"Sizning referal ligangiz: {ref_link}\nSiz tomonidan qo'shilganlar soni: {cnt}")
        except Exception:
            pass
        _state.pop(uid, None)
        return

    # fallback
    await message.answer('Iltimos, ko‘rsatmalarga rioya qiling.')
