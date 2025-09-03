import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from models import Notification  # Add this model to user service models
from database import get_async_db
from shared.event_publisher import EventPublisher
import logging
import uuid

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.event_publisher = EventPublisher("user-service")

    async def send_booking_confirmation(self, user_id: str, booking_id: str, 
                                       customer_details: dict, booking_data: dict):
        """Send booking confirmation notification"""
        async with get_async_db() as db:
            try:
                # Create notification record
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    type="booking_confirmation",
                    title="Booking Confirmed! 🎉",
                    message=f"Your booking {booking_id} has been confirmed. Get ready for an amazing event!",
                    data={
                        "booking_id": booking_id,
                        "customer_details": customer_details,
                        "booking_data": booking_data
                    },
                    channels=["email", "push"],
                    status="pending",
                    created_at=datetime.utcnow()
                )
                
                db.add(notification)
                await db.commit()
                
                # Publish notification event
                await self.event_publisher.publish_user_event("customer_notification_sent", {
                    "notification_id": notification.id,
                    "user_id": user_id,
                    "booking_id": booking_id,
                    "type": "booking_confirmation",
                    "channels": notification.channels,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Booking confirmation notification created: {notification.id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating booking confirmation notification: {str(e)}")
                raise

    async def send_booking_cancellation(self, user_id: str, booking_id: str, 
                                       reason: str, booking_data: dict):
        """Send booking cancellation notification"""
        async with get_async_db() as db:
            try:
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    type="booking_cancellation",
                    title="Booking Cancelled",
                    message=f"Your booking {booking_id} has been cancelled. Reason: {reason}",
                    data={
                        "booking_id": booking_id,
                        "reason": reason,
                        "booking_data": booking_data
                    },
                    channels=["email", "push"],
                    status="pending",
                    created_at=datetime.utcnow()
                )
                
                db.add(notification)
                await db.commit()
                
                # Publish notification event
                await self.event_publisher.publish_user_event("customer_notification_sent", {
                    "notification_id": notification.id,
                    "user_id": user_id,
                    "booking_id": booking_id,
                    "type": "booking_cancellation",
                    "reason": reason,
                    "channels": notification.channels,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Booking cancellation notification created: {notification.id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating booking cancellation notification: {str(e)}")
                raise

    async def send_pending_bookings_reminder(self, user_id: str, email: str, 
                                           pending_count: int, booking_data: dict):
        """Send reminder about pending bookings"""
        async with get_async_db() as db:
            try:
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    type="pending_bookings_reminder",
                    title="Pending Bookings Reminder",
                    message=f"You have {pending_count} pending booking(s) that need your attention.",
                    data={
                        "pending_count": pending_count,
                        "booking_data": booking_data
                    },
                    channels=["email", "push"],
                    status="pending",
                    created_at=datetime.utcnow()
                )
                
                db.add(notification)
                await db.commit()
                
                logger.info(f"Pending bookings reminder notification created: {notification.id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating pending bookings reminder: {str(e)}")
                raise

    async def send_upcoming_events_reminder(self, user_id: str, email: str, 
                                          events_count: int, booking_data: dict):
        """Send reminder about upcoming events"""
        async with get_async_db() as db:
            try:
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    type="upcoming_events_reminder",
                    title="Upcoming Events Reminder",
                    message=f"You have {events_count} upcoming event(s) this week. Don't forget!",
                    data={
                        "events_count": events_count,
                        "booking_data": booking_data
                    },
                    channels=["email", "push"],
                    status="pending",
                    created_at=datetime.utcnow()
                )
                
                db.add(notification)
                await db.commit()
                
                logger.info(f"Upcoming events reminder notification created: {notification.id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating upcoming events reminder: {str(e)}")
                raise