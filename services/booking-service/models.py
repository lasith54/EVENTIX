# services/booking-service/models.py
"""
Booking Service Models - Updated for single database with schemas
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.types import Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import sys
import os
import uuid

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.database import Base

class Booking(Base):
    __tablename__ = 'bookings'
    __table_args__ = {'schema': 'bookings'}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.users.id'), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey('events.events.id'), nullable=False, index=True)
    booking_reference = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), default='pending', index=True)
    total_amount = Column(Decimal(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    booking_date = Column(DateTime, server_default=func.now())
    expiry_date = Column(DateTime)
    payment_id = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    booking_seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        if not self.expiry_date:
            self.expiry_date = datetime.utcnow() + timedelta(minutes=15)  # 15 minute expiry
    
    @staticmethod
    def generate_booking_reference():
        """Generate unique booking reference"""
        return f"BK{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
    
    def __repr__(self):
        return f"<Booking(id={self.id}, reference='{self.booking_reference}', status='{self.status}')>"
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expiry_date if self.expiry_date else False
    
    @property
    def is_confirmed(self):
        return self.status == 'confirmed'
    
    @property
    def is_cancelled(self):
        return self.status == 'cancelled'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'booking_reference': self.booking_reference,
            'status': self.status,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'currency': self.currency,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'payment_id': self.payment_id,
            'notes': self.notes,
            'is_expired': self.is_expired,
            'is_confirmed': self.is_confirmed,
            'is_cancelled': self.is_cancelled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BookingSeat(Base):
    __tablename__ = 'booking_seats'
    __table_args__ = {'schema': 'bookings'}
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.bookings.id'), nullable=False)
    seat_id = Column(Integer, ForeignKey('events.seats.id'), nullable=False)
    price = Column(Decimal(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="booking_seats")
    
    def __repr__(self):
        return f"<BookingSeat(id={self.id}, booking_id={self.booking_id}, seat_id={self.seat_id})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'seat_id': self.seat_id,
            'price': float(self.price) if self.price else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SeatReservation(Base):
    __tablename__ = 'seat_reservations'
    __table_args__ = {'schema': 'bookings'}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.users.id'), nullable=False)
    seat_id = Column(Integer, ForeignKey('events.seats.id'), nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.bookings.id'))
    reserved_until = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default='reserved', index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.reserved_until:
            self.reserved_until = datetime.utcnow() + timedelta(minutes=15)  # 15 minute reservation
    
    def __repr__(self):
        return f"<SeatReservation(id={self.id}, seat_id={self.seat_id}, status='{self.status}')>"
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.reserved_until
    
    @property
    def is_active(self):
        return self.status == 'reserved' and not self.is_expired
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'seat_id': self.seat_id,
            'booking_id': self.booking_id,
            'reserved_until': self.reserved_until.isoformat() if self.reserved_until else None,
            'status': self.status,
            'is_expired': self.is_expired,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Booking Status Enum
class BookingStatus:
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'
    REFUNDED = 'refunded'

# Reservation Status Enum
class ReservationStatus:
    RESERVED = 'reserved'
    CONFIRMED = 'confirmed'
    EXPIRED = 'expired'
    RELEASED = 'released'