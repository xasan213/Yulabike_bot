from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .db import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    is_partner = Column(Boolean, default=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    passport_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Bike(Base):
    __tablename__ = 'bikes'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    available = Column(Boolean, default=True)
    price_per_hour = Column(Float, default=0.0)
    partner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    image_file_id = Column(String, nullable=True)
    code = Column(String, nullable=True, unique=True)
    is_main = Column(Boolean, default=False)

class Rental(Base):
    __tablename__ = 'rentals'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    bike_id = Column(Integer, ForeignKey('bikes.id'))
    start_at = Column(DateTime, default=datetime.datetime.utcnow)
    end_at = Column(DateTime, nullable=True)
    fee = Column(Float, default=0.0)


class Payout(Base):
    __tablename__ = 'payouts'
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User')
    bike = relationship('Bike')
