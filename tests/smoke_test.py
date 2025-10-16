import asyncio

async def main():
    from database.db import init_db
    from database.queries import (
        get_or_create_user,
        create_bike_for_partner,
        set_main_bike,
        pick_main_bike,
        create_rental,
        set_rental_end,
        partner_earnings,
        record_payout,
        partner_balance,
    )

    print('Initializing DB...')
    await init_db()

    print('Creating partner user (telegram_id=1001)')
    partner = await get_or_create_user(1001)
    print('Partner DB id:', partner.id)

    print('Creating bike for partner')
    bike = await create_bike_for_partner(partner_id=partner.id, name='Test Bike', price_per_hour=10.0, image_file_id='img1', code='B100')
    print('Bike id:', bike.id)

    print('Setting main bike...')
    await set_main_bike(bike.id)
    main = await pick_main_bike()
    print('Main bike:', main.id if main else None)

    print('Creating customer user (telegram_id=2001)')
    user = await get_or_create_user(2001)
    print('User DB id:', user.id)

    print('Creating rental...')
    rental = await create_rental(user.id, bike.id)
    if not rental:
        print('Rental creation failed')
        return
    print('Rental id:', rental.id)

    print('Closing rental and calculating fee for 2 hours...')
    updated = await set_rental_end(rental.id, hours=2)
    print('Rental fee:', updated.fee)

    print('Partner earnings:')
    earnings = await partner_earnings(partner.id)
    print(earnings)

    print('Recording payout of 5.0')
    payout = await record_payout(partner.id, 5.0)
    print('Payout id:', payout.id)

    bal = await partner_balance(partner.id)
    print('Balance:', bal)

if __name__ == '__main__':
    asyncio.run(main())
