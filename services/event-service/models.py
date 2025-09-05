# services/event-service/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.types import Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.database import Base

class Venue(Base):
    __tablename__ = 'venues'
    __table_args__ = {'schema': 'events'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    facilities = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    events = relationship("Event", back_populates="venue")
    seat_sections = relationship("SeatSection", back_populates="venue", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Venue(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'capacity': self.capacity,
            'facilities': self.facilities,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Event(Base):
    __tablename__ = 'events'
    __table_args__ = {'schema': 'events'}
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    venue_id = Column(Integer, ForeignKey('events.venues.id'))
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False, index=True)
    category = Column(String(100), index=True)
    status = Column(String(50), default='active', index=True)
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    base_price = Column(Decimal(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    image_url = Column(Text)
    tags = Column(JSON, default=[])
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    venue = relationship("Venue", back_populates="events")
    seats = relationship("Seat", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}')>"
    
    @property
    def is_active(self):
        return self.status == 'active' and self.start_datetime > datetime.utcnow()
    
    @property
    def is_sold_out(self):
        return self.available_seats <= 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'venue_id': self.venue_id,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'category': self.category,
            'status': self.status,
            'total_seats': self.total_seats,
            'available_seats': self.available_seats,
            'base_price': float(self.base_price) if self.base_price else None,
            'currency': self.currency,
            'image_url': self.image_url,
            'tags': self.tags,
            'is_active': self.is_active,
            'is_sold_out': self.is_sold_out,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SeatSection(Base):
    __tablename__ = 'seat_sections'
    __table_args__ = {'schema': 'events'}
    
    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey('events.venues.id'), nullable=False)
    section_name = Column(String(100), nullable=False)
    seat_count = Column(Integer, nullable=False)
    price_multiplier = Column(Decimal(3, 2), default=1.00)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    venue = relationship("Venue", back_populates="seat_sections")
    seats = relationship("Seat", back_populates="section")
    
    def __repr__(self):
        return f"<SeatSection(id={self.id}, name='{self.section_name}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'venue_id': self.venue_id,
            'section_name': self.section_name,
            'seat_count': self.seat_count,
            'price_multiplier': float(self.price_multiplier) if self.price_multiplier else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Seat(Base):
    __tablename__ = 'seats'
    __table_args__ = {'schema': 'events'}
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.events.id'), nullable=False)
    section_id = Column(Integer, ForeignKey('events.seat_sections.id'))
    seat_number = Column(String(20), nullable=False)
    row_number = Column(String(10))
    is_available = Column(Boolean, default=True, index=True)
    price = Column(Decimal(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="seats")
    section = relationship("SeatSection", back_populates="seats")
    
    def __repr__(self):
        return f"<Seat(id={self.id}, seat_number='{self.seat_number}', available={self.is_available})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'section_id': self.section_id,
            'seat_number': self.seat_number,
            'row_number': self.row_number,
            'is_available': self.is_available,
            'price': float(self.price) if self.price else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }