from sqlalchemy import select, update
from .db import get_session
from .models import User, Bike, Rental, Payout


async def get_or_create_user(telegram_id: int):
    async with get_session() as session:
        q = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = q.scalars().first()
        if user:
            return user
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def list_available_bikes():
    async with get_session() as session:
        q = await session.execute(select(Bike).where(Bike.available == True))
        return q.scalars().all()


async def create_rental(user_id: int, bike_id: int):
    async with get_session() as session:
        async with session.begin():
            # lock the bike row for update to avoid race conditions
            q = select(Bike).where(Bike.id == bike_id).with_for_update()
            res = await session.execute(q)
            bike = res.scalars().first()
            if not bike or not bike.available:
                return None
            rental = Rental(user_id=user_id, bike_id=bike_id)
            session.add(rental)
            bike.available = False
        # commit happens at context exit
        await session.refresh(rental)
        return rental


async def update_user_profile(telegram_id: int, **fields):
    async with get_session() as session:
        q = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = q.scalars().first()
        if not user:
            return None
        for k, v in fields.items():
            if hasattr(user, k):
                setattr(user, k, v)
        await session.commit()
        await session.refresh(user)
        return user


async def register_partner(telegram_id: int):
    async with get_session() as session:
        q = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = q.scalars().first()
        if not user:
            user = User(telegram_id=telegram_id, is_partner=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        user.is_partner = True
        await session.commit()
        await session.refresh(user)
        return user


async def create_bike_for_partner(partner_id: int, name: str, price_per_hour: float, image_file_id: str = None, code: str = None):
    async with get_session() as session:
        bike = Bike(name=name, price_per_hour=price_per_hour, partner_id=partner_id, image_file_id=image_file_id, code=code)
        session.add(bike)
        await session.commit()
        await session.refresh(bike)
        return bike


async def pick_available_bike():
    """Pick one available bike (simple policy: lowest id)."""
    async with get_session() as session:
        q = await session.execute(select(Bike).where(Bike.available == True).order_by(Bike.id))
        return q.scalars().first()


async def set_main_bike(bike_id: int):
    async with get_session() as session:
        # unset previous mains
        await session.execute(update(Bike).where(Bike.is_main == True).values(is_main=False))
        b = await session.get(Bike, bike_id)
        if not b:
            return None
        b.is_main = True
        await session.commit()
        await session.refresh(b)
        return b


async def pick_main_bike():
    async with get_session() as session:
        q = await session.execute(select(Bike).where(Bike.is_main == True))
        return q.scalars().first()


async def get_rental_by_id(rental_id: int):
    async with get_session() as session:
        return await session.get(Rental, rental_id)


async def get_user_by_db_id(db_user_id: int):
    async with get_session() as session:
        return await session.get(User, db_user_id)


async def assign_bike_to_rental(rental_id: int, bike_id: int):
    async with get_session() as session:
        async with session.begin():
            # lock bike
            q = select(Bike).where(Bike.id == bike_id).with_for_update()
            res = await session.execute(q)
            bike = res.scalars().first()
            if not bike or not bike.available:
                return None
            rental = await session.get(Rental, rental_id)
            if not rental:
                return None
            rental.bike_id = bike_id
            bike.available = False
        await session.refresh(rental)
        return rental


async def set_rental_end(rental_id: int, hours: float):
    async with get_session() as session:
        async with session.begin():
            rental = await session.get(Rental, rental_id)
            if not rental:
                return None
            bike = await session.get(Bike, rental.bike_id)
            if not bike:
                return None
            from datetime import datetime, timedelta
            rental.end_at = datetime.utcnow()
            rental.fee = (bike.price_per_hour or 0.0) * hours
        await session.refresh(rental)
        return rental


async def list_rentals():
    async with get_session() as session:
        q = await session.execute(select(Rental))
        return q.scalars().all()


async def partner_earnings(partner_id: int):
    async with get_session() as session:
        q = await session.execute(select(Rental).join(Bike).where(Bike.partner_id == partner_id))
        rentals = q.scalars().all()
        total = sum(r.fee or 0.0 for r in rentals)
        return {'total': total, 'rentals': rentals}


async def record_payout(partner_id: int, amount: float):
    async with get_session() as session:
        payout = Payout(partner_id=partner_id, amount=amount)
        session.add(payout)
        await session.commit()
        await session.refresh(payout)
        return payout


async def list_partner_payouts(partner_id: int):
    async with get_session() as session:
        q = await session.execute(select(Payout).where(Payout.partner_id == partner_id))
        return q.scalars().all()


async def partner_balance(partner_id: int):
    earnings = await partner_earnings(partner_id)
    payouts = await list_partner_payouts(partner_id)
    paid = sum(p.amount for p in payouts)
    return {'earned': earnings['total'], 'paid': paid, 'balance': earnings['total'] - paid}
