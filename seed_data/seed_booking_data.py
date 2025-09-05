import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import enum

# Add paths for each service
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import models from each service
from services.booking_service.models import (
    Booking, BookingItem, SagaTransaction, SagaTransactionStep,
    BookingStatusHistory, BookingStatus, SagaTransactionStatus, SagaStepStatus
)

# Database configurations
DATABASE_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5434/booking-db'


def get_session(service_name):
    """Create database session for specific service."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def seed_booking_service(user_ids, event_data):
    """Add sample data to booking service."""
    if not user_ids or not event_data:
        print("✗ Cannot seed booking service: missing user or event data")
        return []
    
    session = get_session('booking')
    
    try:
        bookings = []
        
        for i, user_id in enumerate(user_ids[:2]):  # Create bookings for first 2 users
            booking = Booking(
                booking_reference=f"BK-2024-{1000+i}",
                user_id=str(user_id),
                event_id=str(event_data['event_id']),
                status=BookingStatus.CONFIRMED if i == 0 else BookingStatus.PENDING,
                total_amount=Decimal("225.00"),
                currency="USD",
                customer_email=f"user{i+1}@example.com",
                customer_name=f"User {i+1}",
                customer_phone=f"+123456789{i}",
                confirmed_at=datetime.utcnow() if i == 0 else None
            )
            bookings.append(booking)
            session.add(booking)
        
        session.flush()
        
        # Create booking items
        for i, booking in enumerate(bookings):
            # Create 2 booking items per booking
            for j in range(2):
                item = BookingItem(
                    booking_id=booking.id,
                    seat_id=str(1000 + i * 2 + j),  # Dummy seat IDs
                    venue_section_id=str(event_data['section_ids'][0]),
                    unit_price=Decimal("75.00") if j == 0 else Decimal("150.00"),
                    quantity=1,
                    total_price=Decimal("75.00") if j == 0 else Decimal("150.00"),
                    seat_row=f"Row {j+1}",
                    seat_number=str(j+1),
                    section_name="Floor" if j == 1 else "Lower Bowl",
                    pricing_tier="General"
                )
                session.add(item)
            
            # Create saga transaction
            saga = SagaTransaction(
                saga_id=f"saga-{booking.booking_reference}",
                booking_id=booking.id,
                transaction_type="booking_creation",
                status=SagaTransactionStatus.COMPLETED if i == 0 else SagaTransactionStatus.IN_PROGRESS
            )
            session.add(saga)
        
        session.commit()
        print("✓ Booking service data seeded successfully")
        return [booking.id for booking in bookings]
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding booking service: {e}")
        return []
    finally:
        session.close()
