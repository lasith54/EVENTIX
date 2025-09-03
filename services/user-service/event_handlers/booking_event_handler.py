import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

class NotificationServiceBookingHandler:
    def __init__(self):
        self.notification_service = NotificationService()
        
    async def handle_booking_event(self, event_data):
        """Handle incoming booking service events for notifications"""
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        
        logger.info(f"Notification handler received booking event: {event_type}")
        
        try:
            if event_type == "booking_confirmed":
                await self._handle_booking_confirmed(data)
            elif event_type == "booking_cancelled":
                await self._handle_booking_cancelled(data)
            elif event_type == "pending_bookings_reminder":
                await self._handle_pending_bookings_reminder(data)
            elif event_type == "upcoming_events_reminder":
                await self._handle_upcoming_events_reminder(data)
                
        except Exception as e:
            logger.error(f"Error handling booking event {event_type}: {str(e)}")

    async def _handle_booking_confirmed(self, data):
        """Send confirmation notification when booking is confirmed"""
        user_id = data.get("user_id")
        booking_id = data.get("booking_id")
        customer_details = data.get("customer_details", {})
        
        try:
            await self.notification_service.send_booking_confirmation(
                user_id=user_id,
                booking_id=booking_id,
                customer_details=customer_details,
                booking_data=data
            )
            logger.info(f"Booking confirmation sent for {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation for {booking_id}: {str(e)}")

    async def _handle_booking_cancelled(self, data):
        """Send cancellation notification when booking is cancelled"""
        user_id = data.get("user_id")
        booking_id = data.get("booking_id")
        reason = data.get("reason", "unknown")
        
        try:
            await self.notification_service.send_booking_cancellation(
                user_id=user_id,
                booking_id=booking_id,
                reason=reason,
                booking_data=data
            )
            logger.info(f"Booking cancellation sent for {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send booking cancellation for {booking_id}: {str(e)}")

    async def _handle_pending_bookings_reminder(self, data):
        """Send reminder about pending bookings"""
        user_id = data.get("user_id")
        email = data.get("email")
        pending_count = data.get("pending_bookings_count", 0)
        
        try:
            await self.notification_service.send_pending_bookings_reminder(
                user_id=user_id,
                email=email,
                pending_count=pending_count,
                booking_data=data
            )
            logger.info(f"Pending bookings reminder sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send pending bookings reminder to {user_id}: {str(e)}")

    async def _handle_upcoming_events_reminder(self, data):
        """Send reminder about upcoming events"""
        user_id = data.get("user_id")
        email = data.get("email")
        events_count = data.get("upcoming_events_count", 0)
        
        try:
            await self.notification_service.send_upcoming_events_reminder(
                user_id=user_id,
                email=email,
                events_count=events_count,
                booking_data=data
            )
            logger.info(f"Upcoming events reminder sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send upcoming events reminder to {user_id}: {str(e)}")