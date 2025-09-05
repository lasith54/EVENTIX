# services/user-service/models.py
"""
User Service Models - Updated for single database with schemas
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.database import Base

class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        {'schema': 'users'},
        Index('idx_user_email', 'email'),
        Index('idx_user_active', 'is_active'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def display_name(self):
        """Get display name for UI"""
        return self.full_name
    
    @property
    def is_verified(self):
        """Check if user is verified (active)"""
        return self.is_active
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_public_dict(self):
        """Public representation (safe for API responses)"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        {'schema': 'users'},
        Index('idx_profile_user', 'user_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.users.id'), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    bio = Column(Text)
    avatar_url = Column(String(500))
    preferences = Column(JSON, default=lambda: {})
    notification_settings = Column(JSON, default=lambda: {
        'email_notifications': True,
        'sms_notifications': False,
        'push_notifications': True,
        'marketing_emails': False
    })
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id}, city='{self.city}')>"
    
    @property
    def age(self):
        """Calculate user's age from date of birth"""
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.city:
            address_parts.append(self.city)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        return ', '.join(address_parts) if address_parts else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'gender': self.gender,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'postal_code': self.postal_code,
            'full_address': self.full_address,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'preferences': self.preferences or {},
            'notification_settings': self.notification_settings or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserSession(Base):
    __tablename__ = 'user_sessions'
    __table_args__ = (
        {'schema': 'users'},
        Index('idx_session_token', 'token_hash'),
        Index('idx_session_user', 'user_id'),
        Index('idx_session_active', 'is_active', 'expires_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.users.id'), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    user_agent = Column(Text)
    ip_address = Column(String(45))  # Supports IPv6
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address
        }

# Constants and Enums
class UserRole:
    """User role constants"""
    USER = 'user'
    ADMIN = 'admin'
    MODERATOR = 'moderator'

class NotificationSettings:
    """Default notification settings"""
    DEFAULT = {
        'email_notifications': True,
        'sms_notifications': False,
        'push_notifications': True,
        'marketing_emails': False,
        'booking_confirmations': True,
        'event_reminders': True,
        'payment_notifications': True
    }