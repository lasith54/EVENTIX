# services/booking-service/event_handlers/user_event_handler.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Booking, BookingHistory, UserBookingProfile
from database import get_async_db
from shared.event_publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

class BookingServiceUserHandler:
    def __init__(self):
        self.event_publisher = EventPublisher("booking-service")
        
    async def handle_user_event(self, event_data):
        """Handle incoming user service events"""
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        
        logger.info(f"Booking service received user event: {event_type}")
        
        try:
            if event_type == "created":
                await self._handle_user_registration(data)
            elif event_type == "login_successful":
                await self._handle_user_login(data)
            elif event_type == "profile_updated":
                await self._handle_profile_update(data)
            elif event_type == "account_deactivated":
                await self._handle_account_deactivation(data)
            elif event_type == "preferences_updated":
                await self._handle_preference_update(data)
            elif event_type == "password_changed":
                await self._handle_security_event(data)
                
        except Exception as e:
            logger.error(f"Error handling user event {event_type}: {str(e)}")

    async def _handle_user_registration(self, data):
        """When new user registers, create booking profile"""
        user_id = data.get("user_id")
        email = data.get("email")
        
        async with get_async_db() as db:
            # Create user booking profile with default settings
            booking_profile = UserBookingProfile(
                user_id=user_id,
                booking_preferences={
                    "auto_seat_selection": False,
                    "preferred_payment_method": "card",
                    "booking_reminders": True,
                    "group_booking_notifications": True
                },
                booking_limits={
                    "max_concurrent_bookings": 10,
                    "max_tickets_per_booking": 8
                },
                created_at=datetime.utcnow()
            )
            
            db.add(booking_profile)
            await db.commit()
            
            # Publish booking profile creation
            await self.event_publisher.publish_booking_event("user_profile_created", {
                "user_id": user_id,
                "email": email,
                "booking_profile_created": True,
                "default_limits_applied": True,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Created booking profile for user {user_id}")

    async def _handle_user_login(self, data):
        """When user logs in, check for booking updates and reminders"""
        user_id = data.get("user_id")
        email = data.get("email")
        
        async with get_async_db() as db:
            # Check for pending bookings that need attention
            pending_bookings = await db.execute(
                select(Booking)
                .where(Booking.user_id == user_id)
                .where(Booking.status == "pending")
                .where(Booking.expires_at > datetime.utcnow())
            )
            
            bookings = pending_bookings.scalars().all()
            
            if bookings:
                # Notify about pending bookings
                await self.event_publisher.publish_booking_event("pending_bookings_reminder", {
                    "user_id": user_id,
                    "email": email,
                    "pending_bookings_count": len(bookings),
                    "booking_ids": [str(b.id) for b in bookings],
                    "expires_soon": [
                        str(b.id) for b in bookings 
                        if b.expires_at < datetime.utcnow() + timedelta(hours=1)
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Fix: Check for upcoming events using booking data only
            # Instead of joining Event table, use event_date from booking
            upcoming_bookings = await db.execute(
                select(Booking)
                .where(Booking.user_id == user_id)
                .where(Booking.status == "confirmed")
                .where(Booking.event_date > datetime.utcnow())
                .where(Booking.event_date < datetime.utcnow() + timedelta(days=7))
            )
            
            upcoming = upcoming_bookings.scalars().all()
            if upcoming:
                await self.event_publisher.publish_booking_event("upcoming_events_reminder", {
                    "user_id": user_id,
                    "email": email,
                    "upcoming_events_count": len(upcoming),
                    "booking_ids": [str(b.id) for b in upcoming],
                    "event_ids": [str(b.event_id) for b in upcoming],  # Include event IDs
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def _handle_profile_update(self, data):
        """When user updates profile, update booking-related information"""
        user_id = data.get("user_id")
        updated_fields = data.get("updated_fields", [])
        
        # Check if contact information was updated
        contact_fields = ["email", "phone_number", "first_name", "last_name"]
        if any(field in updated_fields for field in contact_fields):
            async with get_async_db() as db:
                # Update contact info for future bookings
                await self._update_booking_contact_info(user_id, data, db)
                
                # Publish contact update notification
                await self.event_publisher.publish_booking_event("contact_info_updated", {
                    "user_id": user_id,
                    "updated_fields": [f for f in updated_fields if f in contact_fields],
                    "future_bookings_updated": True,
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def _handle_account_deactivation(self, data):
        """When user deactivates account, handle active bookings"""
        user_id = data.get("user_id")
        email = data.get("email")
        
        async with get_async_db() as db:
            # Get all active bookings
            active_bookings = await db.execute(
                select(Booking)
                .where(Booking.user_id == user_id)
                .where(Booking.status.in_(["confirmed", "pending"]))
            )
            
            bookings = active_bookings.scalars().all()
            
            # Handle each booking based on event date stored in booking
            cancelled_bookings = []
            maintained_bookings = []
            
            for booking in bookings:
                # Use event_date from booking instead of joining Event table
                if booking.event_date and booking.event_date > datetime.utcnow() + timedelta(days=1):
                    booking.status = "cancelled_by_deactivation"
                    booking.cancelled_at = datetime.utcnow()
                    cancelled_bookings.append(str(booking.id))
                else:
                    # Keep booking active for events happening soon
                    maintained_bookings.append(str(booking.id))
            
            await db.commit()
            
            # Publish account deactivation handling
            await self.event_publisher.publish_booking_event("account_deactivation_handled", {
                "user_id": user_id,
                "email": email,
                "total_active_bookings": len(bookings),
                "cancelled_bookings": cancelled_bookings,
                "maintained_bookings": maintained_bookings,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def _handle_preference_update(self, data):
        """When user updates preferences, update booking preferences"""
        user_id = data.get("user_id")
        new_preferences = data.get("new_preferences", {})
        
        # Extract booking-related preferences
        booking_prefs = {}
        for key, value in new_preferences.items():
            if key.startswith("booking_") or key in ["payment_method", "notifications"]:
                booking_prefs[key] = value
        
        if booking_prefs:
            async with get_async_db() as db:
                # Update booking profile preferences
                profile_result = await db.execute(
                    select(UserBookingProfile).where(UserBookingProfile.user_id == user_id)
                )
                profile = profile_result.scalar_one_or_none()
                
                if profile:
                    # Update preferences
                    current_prefs = profile.booking_preferences or {}
                    current_prefs.update(booking_prefs)
                    profile.booking_preferences = current_prefs
                    profile.updated_at = datetime.utcnow()
                    
                    await db.commit()
                    
                    # Publish preference update
                    await self.event_publisher.publish_booking_event("booking_preferences_updated", {
                        "user_id": user_id,
                        "updated_preferences": booking_prefs,
                        "timestamp": datetime.utcnow().isoformat()
                    })

    async def _handle_security_event(self, data):
        """When user changes password, enhance booking security"""
        user_id = data.get("user_id")
        
        # For security events, we might want to require re-authentication 
        # for high-value bookings in the next 24 hours
        async with get_async_db() as db:
            # Flag recent bookings for additional verification
            recent_bookings = await db.execute(
                select(Booking)
                .where(Booking.user_id == user_id)
                .where(Booking.created_at > datetime.utcnow() - timedelta(hours=1))
                .where(Booking.status == "pending")
            )
            
            bookings = recent_bookings.scalars().all()
            flagged_bookings = []
            
            for booking in bookings:
                if booking.total_amount > 100:  # High value threshold
                    booking.requires_verification = True
                    flagged_bookings.append(str(booking.id))
            
            if flagged_bookings:
                await db.commit()
                
                # Publish security enhancement
                await self.event_publisher.publish_booking_event("security_verification_required", {
                    "user_id": user_id,
                    "reason": "password_change",
                    "flagged_bookings": flagged_bookings,
                    "verification_required": True,
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def _update_booking_contact_info(self, user_id: str, profile_data: dict, db: AsyncSession):
        """Update contact information for future bookings"""
        new_data = profile_data.get("new_data", {})
        
        # Update booking profile with new contact info
        profile_result = await db.execute(
            select(UserBookingProfile).where(UserBookingProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if profile:
            contact_info = profile.contact_preferences or {}
            
            if "email" in new_data:
                contact_info["email"] = new_data["email"]
            if "phone_number" in new_data:
                contact_info["phone"] = new_data["phone_number"]
            
            profile.contact_preferences = contact_info
            profile.updated_at = datetime.utcnow()
            await db.commit()