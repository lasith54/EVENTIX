# services/payment-service/models.py
"""
Payment Service Models - Updated for single database with schemas
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.types import Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os
import uuid

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.database import Base

class Payment(Base):
    __tablename__ = 'payments'
    __table_args__ = {'schema': 'payments'}
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.bookings.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.users.id'), nullable=False, index=True)
    amount = Column(Decimal(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    payment_method = Column(String(50))  # card, paypal, stripe, etc.
    payment_gateway = Column(String(50), index=True)  # stripe, paypal, square, etc.
    gateway_transaction_id = Column(String(255), index=True)
    status = Column(String(50), default='pending', index=True)
    payment_date = Column(DateTime)
    failure_reason = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, booking_id={self.booking_id}, status='{self.status}')>"
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'declined', 'cancelled']
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_refundable(self):
        return self.status == 'completed' and self.amount > 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'user_id': self.user_id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_gateway': self.payment_gateway,
            'gateway_transaction_id': self.gateway_transaction_id,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'failure_reason': self.failure_reason,
            'metadata': self.metadata,
            'is_successful': self.is_successful,
            'is_failed': self.is_failed,
            'is_pending': self.is_pending,
            'is_refundable': self.is_refundable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Refund(Base):
    __tablename__ = 'refunds'
    __table_args__ = {'schema': 'payments'}
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey('payments.payments.id'), nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.bookings.id'), nullable=False)
    amount = Column(Decimal(10, 2), nullable=False)
    reason = Column(Text)
    status = Column(String(50), default='pending', index=True)
    gateway_refund_id = Column(String(255))
    processed_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    
    def __repr__(self):
        return f"<Refund(id={self.id}, payment_id={self.payment_id}, status='{self.status}')>"
    
    @property
    def is_processed(self):
        return self.status == 'processed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'booking_id': self.booking_id,
            'amount': float(self.amount) if self.amount else None,
            'reason': self.reason,
            'status': self.status,
            'gateway_refund_id': self.gateway_refund_id,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'is_processed': self.is_processed,
            'is_failed': self.is_failed,
            'is_pending': self.is_pending,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Payment Status Enum
class PaymentStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    DECLINED = 'declined'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'

# Refund Status Enum
class RefundStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    PROCESSED = 'processed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

# Payment Method Enum
class PaymentMethod:
    CREDIT_CARD = 'credit_card'
    DEBIT_CARD = 'debit_card'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'
    DIGITAL_WALLET = 'digital_wallet'
    CASH = 'cash'

# Payment Gateway Enum
class PaymentGateway:
    STRIPE = 'stripe'
    PAYPAL = 'paypal'
    SQUARE = 'square'
    BRAINTREE = 'braintree'
    AUTHORIZE_NET = 'authorize_net'
    MOCK = 'mock'  # For testing