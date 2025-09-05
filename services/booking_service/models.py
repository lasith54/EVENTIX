from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class SagaTransactionStatus(enum.Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

class SagaStepStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_reference = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)  # References user_service
    event_id = Column(String, nullable=False, index=True)  # References event_service
    
    # Booking details
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='LKR')
    
    # Timestamps
    booking_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional details
    special_requests = Column(Text, nullable=True)
    booking_notes = Column(Text, nullable=True)
    
    # Contact information (cached from user service)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    customer_name = Column(String(100), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    booking_items = relationship("BookingItem", back_populates="booking", cascade="all, delete-orphan")
    saga_transactions = relationship("SagaTransaction", back_populates="booking")
    status_history = relationship("BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, reference={self.booking_reference}, status={self.status.value})>"

class BookingItem(Base):
    __tablename__ = 'booking_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    
    # Item details (references to event service)
    seat_id = Column(String, nullable=False, index=True)  # References event_service.seats
    venue_section_id = Column(String, nullable=False, index=True)  # References event_service.venue_sections
    
    # Pricing information
    unit_price = Column(DECIMAL(8, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Cached information from event service
    seat_row = Column(String(10), nullable=True)
    seat_number = Column(String(10), nullable=True)
    section_name = Column(String(100), nullable=False)
    pricing_tier = Column(String(50), nullable=True)
    
    # Item status
    is_cancelled = Column(Boolean, nullable=False, default=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="booking_items")
    
    def __repr__(self):
        return f"<BookingItem(id={self.id}, seat_id={self.seat_id}, price={self.total_price})>"

class SagaTransaction(Base):
    __tablename__ = 'saga_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    saga_id = Column(String(100), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # e.g., 'booking_creation', 'booking_cancellation'
    status = Column(Enum(SagaTransactionStatus), nullable=False, default=SagaTransactionStatus.STARTED)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Compensation data
    compensation_data = Column(Text, nullable=True)  # JSON stored as text
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="saga_transactions")
    steps = relationship("SagaTransactionStep", back_populates="saga_transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SagaTransaction(id={self.id}, saga_id={self.saga_id}, status={self.status.value})>"

class SagaTransactionStep(Base):
    __tablename__ = 'saga_transaction_steps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    saga_transaction_id = Column(Integer, ForeignKey('saga_transactions.id'), nullable=False)
    
    # Step details
    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    service_name = Column(String(50), nullable=False)  # e.g., 'event_service', 'payment_service'
    
    # Step status and timing
    status = Column(Enum(SagaStepStatus), nullable=False, default=SagaStepStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    compensated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Request and response data
    request_data = Column(Text, nullable=True)  # JSON stored as text
    response_data = Column(Text, nullable=True)  # JSON stored as text
    compensation_data = Column(Text, nullable=True)  # JSON stored as text
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    saga_transaction = relationship("SagaTransaction", back_populates="steps")
    
    def __repr__(self):
        return f"<SagaTransactionStep(id={self.id}, step_name={self.step_name}, status={self.status.value})>"

class BookingStatusHistory(Base):
    __tablename__ = 'booking_status_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    
    # Status change details
    previous_status = Column(Enum(BookingStatus), nullable=True)
    new_status = Column(Enum(BookingStatus), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Change context
    changed_by = Column(String(100), nullable=True)  # User ID or system identifier
    change_reason = Column(String(255), nullable=True)
    change_notes = Column(Text, nullable=True)
    
    # Related transaction
    saga_transaction_id = Column(Integer, ForeignKey('saga_transactions.id'), nullable=True)
    
    # Additional metadata
    saga_metadata = Column(Text, nullable=True)  # JSON stored as text for additional context
    
    # Relationships
    booking = relationship("Booking", back_populates="status_history")
    
    def __repr__(self):
        return f"<BookingStatusHistory(id={self.id}, booking_id={self.booking_id}, status={self.new_status.value})>"

# Additional utility methods can be added to models as needed
def generate_booking_reference():
    """Generate a unique booking reference"""
    import uuid
    import time
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    uuid_part = str(uuid.uuid4()).replace('-', '').upper()[:6]
    return f"BK{timestamp}{uuid_part}"

# Add this method to the Booking class
Booking.generate_reference = staticmethod(generate_booking_reference)