from aiogram import Router
from aiogram.types import Message
from config import ADMIN_IDS
from database.queries import list_rentals, pick_available_bike, update_user_profile, partner_earnings
from database.queries import pick_main_bike, get_rental_by_id, assign_bike_to_rental, set_main_bike, get_user_by_db_id, record_payout, partner_balance

router = Router()


def is_admin(msg: Message) -> bool:
    return bool(msg.from_user and msg.from_user.id in ADMIN_IDS)


@router.message(lambda msg: msg.text and msg.text.startswith('/admin'))
async def admin_panel(message: Message):
    if not is_admin(message):
        return
    await message.answer('Admin panel: /list_rentals, /assign_bike <rental_id>, /partner_earnings <partner_id>')


@router.message(lambda msg: msg.text and msg.text.startswith('/list_rentals'))
async def cmd_list_rentals(message: Message):
    if not is_admin(message):
        return
    rentals = await list_rentals()
    if not rentals:
        await message.answer('Aktiv ijaralar topilmadi.')
        return
    lines = [f"{r.id}: user={r.user_id} bike={r.bike_id} start={r.start_at} fee={r.fee}" for r in rentals]
    await message.answer('\n'.join(lines))


@router.message(lambda msg: msg.text and msg.text.startswith('/assign_bike'))
async def cmd_assign_bike(message: Message):
    if not is_admin(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer('Foydalanish: /assign_bike <rental_id>')
        return
    try:
        rid = int(parts[1])
    except Exception:
        await message.answer('Noto`g`ri rental id')
        return

    # prefer main bike
    bike = await pick_main_bike()
    if not bike:
        await message.answer('Bosh velosiped topilmadi')
        return

    rental = await assign_bike_to_rental(rid, bike.id)
    if not rental:
        await message.answer('Tayinlashda xato: velosiped band yoki rental topilmadi')
        return

    # notify renter
    renter = await get_user_by_db_id(rental.user_id)
    try:
        await message.bot.send_message(renter.telegram_id, f"Sizga velosiped ajratildi. ID: {bike.id}, kodi: {bike.code}")
    except Exception:
        pass

    await message.answer(f"Assigned bike {bike.id} (code: {bike.code}) to rental {rid}")


@router.message(lambda msg: msg.text and msg.text.startswith('/set_main'))
async def cmd_set_main(message: Message):
    if not is_admin(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer('Foydalanish: /set_main <bike_id>')
        return
    try:
        bid = int(parts[1])
    except Exception:
        await message.answer('Noto`g`ri bike id')
        return
    b = await set_main_bike(bid)
    if not b:
        await message.answer('Velosiped topilmadi')
        return
    await message.answer(f'Bike {b.id} belgilandi bosh velosipedga')


@router.message(lambda msg: msg.text and msg.text.startswith('/pay_partner'))
async def cmd_pay_partner(message: Message):
    if not is_admin(message):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer('Foydalanish: /pay_partner <partner_telegram_id> <amount>')
        return
    try:
        pid = int(parts[1])
        amount = float(parts[2])
    except Exception:
        await message.answer('Noto`g`ri argumentlar. partner_id butun son, amount raqam bo`lishi kerak.')
        return

    payout = await record_payout(pid, amount)
    if not payout:
        await message.answer('Payout yozilmadi, xatolik yuz berdi.')
        return

    # notify partner
    try:
        await message.bot.send_message(pid, f"Sizga to'lov chiqarildi: {amount}. Admin tomonidan.")
    except Exception:
        pass

    # show updated balance
    bal = await partner_balance(pid)
    await message.answer(f"Payout yozildi. Partner balance: earned={bal['earned']} paid={bal['paid']} balance={bal['balance']}")


@router.message(lambda msg: msg.text and msg.text.startswith('/partner_earnings'))
async def cmd_partner_earnings(message: Message):
    if not is_admin(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer('Foydalanish: /partner_earnings <partner_telegram_id>')
        return
    try:
        pid = int(parts[1])
    except Exception:
        await message.answer('Noto`g`ri partner id')
        return
    res = await partner_earnings(pid)
    await message.answer(f"Partner jami daromadi: {res['total']}")
