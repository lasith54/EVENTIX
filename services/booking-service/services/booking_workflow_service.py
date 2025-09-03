import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Booking, BookingHistory
from database import get_async_db
from shared.event_publisher import EventPublisher
import logging
import uuid

logger = logging.getLogger(__name__)

class BookingWorkflowService:
    def __init__(self):
        self.event_publisher = EventPublisher("booking-service")

    async def create_booking(self, booking_data: dict):
        """Create a new booking and initiate payment workflow"""
        async with get_async_db() as db:
            try:
                # Create booking record
                booking = Booking(
                    id=str(uuid.uuid4()),
                    user_id=booking_data["user_id"],
                    event_id=booking_data["event_id"],
                    seat_ids=booking_data["seat_ids"],
                    ticket_quantity=len(booking_data["seat_ids"]),
                    total_amount=booking_data["total_amount"],
                    customer_details=booking_data["customer_details"],
                    event_date=booking_data["event_date"],
                    status="pending_payment",
                    expires_at=datetime.utcnow() + timedelta(minutes=15),
                    created_at=datetime.utcnow()
                )
                
                db.add(booking)
                
                # Create booking history entry
                history = BookingHistory(
                    id=str(uuid.uuid4()),
                    booking_id=booking.id,
                    status="pending_payment",
                    changed_by=booking_data["user_id"],
                    change_reason="Booking created",
                    created_at=datetime.utcnow()
                )
                
                db.add(history)
                await db.commit()
                
                # Publish booking.created event to trigger payment
                await self.event_publisher.publish_booking_event("booking_created", {
                    "booking_id": booking.id,
                    "user_id": booking.user_id,
                    "event_id": booking.event_id,
                    "seat_ids": booking.seat_ids,
                    "total_amount": float(booking.total_amount),
                    "customer_details": booking.customer_details,
                    "expires_at": booking.expires_at.isoformat(),
                    "payment_required": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Booking created: {booking.id}, payment initiation triggered")
                return booking
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating booking: {str(e)}")
                raise

    async def confirm_booking(self, booking_id: str, payment_id: str):
        """Confirm booking after successful payment"""
        async with get_async_db() as db:
            try:
                # Get booking
                booking_result = await db.execute(
                    select(Booking).where(Booking.id == booking_id)
                )
                booking = booking_result.scalar_one_or_none()
                
                if not booking:
                    raise ValueError(f"Booking {booking_id} not found")
                
                if booking.status != "pending_payment":
                    raise ValueError(f"Booking {booking_id} cannot be confirmed, current status: {booking.status}")
                
                # Update booking status
                booking.status = "confirmed"
                booking.payment_id = payment_id
                booking.confirmed_at = datetime.utcnow()
                
                # Create history entry
                history = BookingHistory(
                    id=str(uuid.uuid4()),
                    booking_id=booking.id,
                    status="confirmed",
                    changed_by="system",
                    change_reason=f"Payment completed: {payment_id}",
                    created_at=datetime.utcnow()
                )
                
                db.add(history)
                await db.commit()
                
                # Publish booking.confirmed event to trigger inventory update and notifications
                await self.event_publisher.publish_booking_event("booking_confirmed", {
                    "booking_id": booking.id,
                    "user_id": booking.user_id,
                    "event_id": booking.event_id,
                    "seat_ids": booking.seat_ids,
                    "ticket_quantity": booking.ticket_quantity,
                    "total_amount": float(booking.total_amount),
                    "payment_id": payment_id,
                    "customer_details": booking.customer_details,
                    "event_date": booking.event_date.isoformat() if booking.event_date else None,
                    "confirmed_at": booking.confirmed_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Booking confirmed: {booking.id}")
                return booking
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error confirming booking {booking_id}: {str(e)}")
                raise

    async def cancel_booking(self, booking_id: str, reason: str = "user_cancelled"):
        """Cancel a booking and trigger refund if needed"""
        async with get_async_db() as db:
            try:
                booking_result = await db.execute(
                    select(Booking).where(Booking.id == booking_id)
                )
                booking = booking_result.scalar_one_or_none()
                
                if not booking:
                    raise ValueError(f"Booking {booking_id} not found")
                
                old_status = booking.status
                booking.status = "cancelled"
                booking.cancelled_at = datetime.utcnow()
                
                # Create history entry
                history = BookingHistory(
                    id=str(uuid.uuid4()),
                    booking_id=booking.id,
                    status="cancelled",
                    changed_by="system",
                    change_reason=reason,
                    created_at=datetime.utcnow()
                )
                
                db.add(history)
                await db.commit()
                
                # Publish booking.cancelled event
                await self.event_publisher.publish_booking_event("booking_cancelled", {
                    "booking_id": booking.id,
                    "user_id": booking.user_id,
                    "event_id": booking.event_id,
                    "seat_ids": booking.seat_ids,
                    "previous_status": old_status,
                    "reason": reason,
                    "refund_required": old_status == "confirmed",
                    "payment_id": booking.payment_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Booking cancelled: {booking.id}, reason: {reason}")
                return booking
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error cancelling booking {booking_id}: {str(e)}")
                raise