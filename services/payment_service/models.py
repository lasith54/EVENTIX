from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    CANCELLED = "CANCELLED"

class PaymentMethodType(str, enum.Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    DIGITAL_WALLET = "DIGITAL_WALLET"
    CASH = "CASH"

class TransactionType(str, enum.Enum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    CHARGEBACK = "CHARGEBACK"
    AUTHORIZATION = "AUTHORIZATION"
    CAPTURE = "CAPTURE"
    VOID = "VOID"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("payment_methods.id"))
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    reference_number = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    payment_metadata = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    # Relationships
    payment_method = relationship("PaymentMethod", back_populates="payments")
    transactions = relationship("Transaction", back_populates="payment")
    refunds = relationship("Refund", back_populates="payment")
    audit_logs = relationship("PaymentAuditLog", back_populates="payment")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    method_type = Column(Enum(PaymentMethodType), nullable=False)
    provider = Column(String(50), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    card_last_four = Column(String(4))
    card_expiry = Column(String(7))
    billing_details = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = relationship("Payment", back_populates="payment_method")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(50), nullable=False)
    provider_transaction_id = Column(String(100))
    provider_response = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="transactions")

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    refund_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    refund_metadata = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    transaction = relationship("Transaction")

class PaymentAuditLog(Base):
    __tablename__ = "payment_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    action = Column(String(50), nullable=False)
    performed_by = Column(UUID(as_uuid=True), nullable=False)  # User ID
    previous_status = Column(Enum(PaymentStatus))
    new_status = Column(Enum(PaymentStatus))
    changes = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="audit_logs")