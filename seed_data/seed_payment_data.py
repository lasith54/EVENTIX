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
from services.payment_service.models import (
    Payment, PaymentMethod, Transaction, Refund, PaymentAuditLog,
    PaymentStatus, PaymentMethodType, TransactionType
)

# Database configurations
DATABASE_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5435/payment-db'

def get_session(service_name):
    """Create database session for specific service."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def seed_payment_service(user_ids, booking_ids):
    """Add sample data to payment service."""
    if not user_ids or not booking_ids:
        print("✗ Cannot seed payment service: missing user or booking data")
        return
    
    session = get_session('payment')
    
    try:
        payment_methods = []
        
        # Create payment methods for users
        for i, user_id in enumerate(user_ids[:2]):
            payment_method = PaymentMethod(
                user_id=user_id,
                method_type=PaymentMethodType.CREDIT_CARD if i == 0 else PaymentMethodType.DIGITAL_WALLET,
                provider="Stripe" if i == 0 else "PayPal",
                is_default=True,
                card_last_four="1234" if i == 0 else None,
                card_expiry="12/2025" if i == 0 else None,
                billing_details={
                    "name": f"User {i+1}",
                    "address": f"{i+1}23 Main St",
                    "city": "New York",
                    "country": "US"
                }
            )
            payment_methods.append(payment_method)
            session.add(payment_method)
        
        session.flush()
        
        # Create payments
        for i, booking_id in enumerate(booking_ids):
            payment = Payment(
                booking_id=booking_id,
                user_id=user_ids[i],
                payment_method_id=payment_methods[i].id,
                amount=Decimal("225.00"),
                currency="USD",
                status=PaymentStatus.COMPLETED if i == 0 else PaymentStatus.PENDING,
                reference_number=f"PAY-2024-{2000+i}",
                description=f"Payment for booking {booking_id}",
                payment_metadata={"booking_reference": f"BK-2024-{1000+i}"},
                completed_at=datetime.utcnow() if i == 0 else None
            )
            session.add(payment)
            session.flush()
            
            # Create transaction
            transaction = Transaction(
                payment_id=payment.id,
                type=TransactionType.PAYMENT,
                amount=payment.amount,
                currency=payment.currency,
                status="success" if i == 0 else "pending",
                provider_transaction_id=f"txn_{uuid.uuid4().hex[:10]}",
                provider_response={"status": "succeeded" if i == 0 else "pending"}
            )
            session.add(transaction)
            
            # Create audit log
            audit_log = PaymentAuditLog(
                payment_id=payment.id,
                action="payment_created",
                performed_by=user_ids[i],
                new_status=payment.status,
                changes={"amount": str(payment.amount), "status": payment.status.value},
                ip_address="192.168.1.100"
            )
            session.add(audit_log)
        
        session.commit()
        print("✓ Payment service data seeded successfully")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding payment service: {e}")
    finally:
        session.close()
