import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Payment, PaymentMethod, UserPaymentProfile
from database import get_async_db
from shared.event_publisher import EventPublisher
import logging
import uuid

logger = logging.getLogger(__name__)

class PaymentWorkflowService:
    def __init__(self):
        self.event_publisher = EventPublisher("payment-service")

    async def initiate_payment(self, booking_id: str, user_id: str, amount: float, 
                             description: str, metadata: dict = None):
        """Initiate payment process for a booking"""
        async with get_async_db() as db:
            try:
                # Create payment record
                payment = Payment(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    booking_id=booking_id,
                    amount=amount,
                    currency="USD",
                    description=description,
                    metadata=metadata or {},
                    status="pending",
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(minutes=15)
                )
                
                db.add(payment)
                await db.commit()
                
                # Publish payment.initiated event
                await self.event_publisher.publish_payment_event("payment_initiated", {
                    "payment_id": payment.id,
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "amount": amount,
                    "currency": payment.currency,
                    "description": description,
                    "expires_at": payment.expires_at.isoformat(),
                    "payment_url": f"/payments/{payment.id}/process",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Payment initiated: {payment.id} for booking {booking_id}")
                return payment
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error initiating payment for booking {booking_id}: {str(e)}")
                raise

    async def complete_payment(self, payment_id: str, payment_method_id: str = None, 
                             external_payment_id: str = None):
        """Complete a payment and trigger booking confirmation"""
        async with get_async_db() as db:
            try:
                # Get payment
                payment_result = await db.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                payment = payment_result.scalar_one_or_none()
                
                if not payment:
                    raise ValueError(f"Payment {payment_id} not found")
                
                if payment.status != "pending":
                    raise ValueError(f"Payment {payment_id} cannot be completed, current status: {payment.status}")
                
                # Update payment status
                payment.status = "completed"
                payment.payment_method_id = payment_method_id
                payment.external_payment_id = external_payment_id
                payment.completed_at = datetime.utcnow()
                
                await db.commit()
                
                # Publish payment.completed event to trigger booking confirmation
                await self.event_publisher.publish_payment_event("payment_completed", {
                    "payment_id": payment.id,
                    "booking_id": payment.booking_id,
                    "user_id": payment.user_id,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "payment_method_id": payment_method_id,
                    "external_payment_id": external_payment_id,
                    "completed_at": payment.completed_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Payment completed: {payment.id}")
                return payment
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error completing payment {payment_id}: {str(e)}")
                raise

    async def fail_payment(self, payment_id: str, failure_reason: str):
        """Mark payment as failed"""
        async with get_async_db() as db:
            try:
                payment_result = await db.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                payment = payment_result.scalar_one_or_none()
                
                if not payment:
                    raise ValueError(f"Payment {payment_id} not found")
                
                payment.status = "failed"
                payment.failure_reason = failure_reason
                payment.failed_at = datetime.utcnow()
                
                await db.commit()
                
                # Publish payment.failed event
                await self.event_publisher.publish_payment_event("payment_failed", {
                    "payment_id": payment.id,
                    "booking_id": payment.booking_id,
                    "user_id": payment.user_id,
                    "amount": float(payment.amount),
                    "failure_reason": failure_reason,
                    "failed_at": payment.failed_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Payment failed: {payment.id}, reason: {failure_reason}")
                return payment
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error failing payment {payment_id}: {str(e)}")
                raise

    async def process_refund(self, payment_id: str, booking_id: str, reason: str):
        """Process a refund for a completed payment"""
        async with get_async_db() as db:
            try:
                payment_result = await db.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                payment = payment_result.scalar_one_or_none()
                
                if not payment:
                    raise ValueError(f"Payment {payment_id} not found")
                
                if payment.status != "completed":
                    raise ValueError(f"Cannot refund payment {payment_id}, status: {payment.status}")
                
                # Create refund record (you might want a separate Refund model)
                payment.status = "refunded"
                payment.refunded_at = datetime.utcnow()
                payment.refund_reason = reason
                
                await db.commit()
                
                # Publish payment.refunded event
                await self.event_publisher.publish_payment_event("payment_refunded", {
                    "payment_id": payment.id,
                    "booking_id": booking_id,
                    "user_id": payment.user_id,
                    "refund_amount": float(payment.amount),
                    "reason": reason,
                    "refunded_at": payment.refunded_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Payment refunded: {payment.id}")
                return payment
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error processing refund for payment {payment_id}: {str(e)}")
                raise