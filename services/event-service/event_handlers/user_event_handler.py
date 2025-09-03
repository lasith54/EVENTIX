import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Event, UserEventPreference, EventRecommendation
from database import get_async_db
from shared.event_publisher import EventPublisher
import logging
import json

logger = logging.getLogger(__name__)

class EventServiceUserHandler:
    def __init__(self):
        self.event_publisher = EventPublisher("event-service")
        
    async def handle_user_event(self, event_data):
        """Handle incoming user service events"""
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        
        logger.info(f"Event service received user event: {event_type}")
        
        try:
            if event_type == "created":
                await self._handle_user_registration(data)
            elif event_type == "preferences_updated":
                await self._handle_preference_update(data)
            elif event_type == "login_successful":
                await self._handle_user_login(data)
            elif event_type == "profile_updated":
                await self._handle_profile_update(data)
            elif event_type == "account_deactivated":
                await self._handle_account_deactivation(data)
                
        except Exception as e:
            logger.error(f"Error handling user event {event_type}: {str(e)}")

    async def _handle_user_registration(self, data):
        """When a new user registers, create default event preferences"""
        user_id = data.get("user_id")
        email = data.get("email")
        
        async with get_async_db() as db:
            # Create default event preferences for new user
            default_preferences = UserEventPreference(
                user_id=user_id,
                preferred_categories=["music", "technology", "sports"],  # Default categories
                price_range_min=0,
                price_range_max=500,
                preferred_locations=["any"],
                notification_settings={
                    "email_new_events": True,
                    "email_recommendations": True,
                    "sms_reminders": False
                },
                created_at=datetime.utcnow()
            )
            
            db.add(default_preferences)
            await db.commit()
            
            # Generate initial event recommendations
            await self._generate_initial_recommendations(user_id, db)
            
            # Publish event service response
            await self.event_publisher.publish_event_event("user_onboarded", {
                "user_id": user_id,
                "email": email,
                "default_preferences_created": True,
                "initial_recommendations_generated": True,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Created default event preferences for user {user_id}")

    async def _handle_preference_update(self, data):
        """When user updates preferences, update event recommendations"""
        user_id = data.get("user_id")
        new_preferences = data.get("new_preferences", {})
        
        # Check if event-related preferences changed
        event_related_changes = {}
        for key, value in new_preferences.items():
            if key.startswith("event_") or key in ["location", "budget", "categories"]:
                event_related_changes[key] = value
        
        if event_related_changes:
            async with get_async_db() as db:
                # Update user event preferences
                await self._update_event_preferences(user_id, event_related_changes, db)
                
                # Regenerate recommendations based on new preferences
                recommendations = await self._generate_updated_recommendations(user_id, db)
                
                # Publish updated recommendations
                await self.event_publisher.publish_event_event("recommendations_updated", {
                    "user_id": user_id,
                    "updated_preferences": event_related_changes,
                    "new_recommendations_count": len(recommendations),
                    "recommendation_ids": [str(r.id) for r in recommendations],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Updated event recommendations for user {user_id}")

    async def _handle_user_login(self, data):
        """When user logs in, check for new events they might be interested in"""
        user_id = data.get("user_id")
        last_login = data.get("last_login")
        
        async with get_async_db() as db:
            # Find events created since last login
            if last_login:
                last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                
                # Get user preferences
                user_prefs = await db.execute(
                    select(UserEventPreference).where(UserEventPreference.user_id == user_id)
                )
                preferences = user_prefs.scalar_one_or_none()
                
                if preferences:
                    # Find new events matching user preferences
                    new_events = await self._find_matching_events_since(last_login_dt, preferences, db)
                    
                    if new_events:
                        # Create notifications for new matching events
                        await self._create_event_notifications(user_id, new_events, db)
                        
                        # Publish new events notification
                        await self.event_publisher.publish_event_event("new_events_notification", {
                            "user_id": user_id,
                            "new_events_count": len(new_events),
                            "event_ids": [str(e.id) for e in new_events],
                            "since_last_login": last_login,
                            "timestamp": datetime.utcnow().isoformat()
                        })

    async def _handle_profile_update(self, data):
        """When user updates profile, check if location changed for event recommendations"""
        user_id = data.get("user_id")
        updated_fields = data.get("updated_fields", [])
        
        # Check if location-related fields were updated
        location_fields = ["address", "city", "state", "country", "postal_code"]
        if any(field in updated_fields for field in location_fields):
            async with get_async_db() as db:
                # Update location-based event recommendations
                await self._update_location_based_recommendations(user_id, db)
                
                # Publish location update notification
                await self.event_publisher.publish_event_event("location_based_update", {
                    "user_id": user_id,
                    "updated_location_fields": [f for f in updated_fields if f in location_fields],
                    "recommendations_refreshed": True,
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def _handle_account_deactivation(self, data):
        """When user deactivates account, clean up event-related data"""
        user_id = data.get("user_id")
        
        async with get_async_db() as db:
            # Archive user's event preferences
            await db.execute(
                update(UserEventPreference)
                .where(UserEventPreference.user_id == user_id)
                .values(is_active=False, deactivated_at=datetime.utcnow())
            )
            
            # Archive recommendations
            await db.execute(
                update(EventRecommendation)
                .where(EventRecommendation.user_id == user_id)
                .values(is_active=False)
            )
            
            await db.commit()
            
            # Publish cleanup completion
            await self.event_publisher.publish_event_event("user_data_archived", {
                "user_id": user_id,
                "preferences_archived": True,
                "recommendations_archived": True,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def _generate_initial_recommendations(self, user_id: str, db: AsyncSession):
        """Generate initial event recommendations for new user"""
        # Get popular events in default categories
        popular_events = await db.execute(
            select(Event)
            .where(Event.category.in_(["music", "technology", "sports"]))
            .where(Event.event_date > datetime.utcnow())
            .order_by(Event.popularity_score.desc())
            .limit(10)
        )
        
        events = popular_events.scalars().all()
        recommendations = []
        
        for event in events:
            recommendation = EventRecommendation(
                user_id=user_id,
                event_id=event.id,
                recommendation_score=0.8,  # High score for popular events
                reason="Popular in your categories",
                created_at=datetime.utcnow()
            )
            recommendations.append(recommendation)
            db.add(recommendation)
        
        await db.commit()
        return recommendations

    async def _update_event_preferences(self, user_id: str, changes: dict, db: AsyncSession):
        """Update user's event preferences based on preference changes"""
        prefs_result = await db.execute(
            select(UserEventPreference).where(UserEventPreference.user_id == user_id)
        )
        preferences = prefs_result.scalar_one_or_none()
        
        if preferences:
            # Map preference changes to event preference fields
            if "event_categories" in changes:
                preferences.preferred_categories = changes["event_categories"]
            if "budget" in changes:
                budget = changes["budget"]
                preferences.price_range_max = budget.get("max", preferences.price_range_max)
                preferences.price_range_min = budget.get("min", preferences.price_range_min)
            if "location" in changes:
                preferences.preferred_locations = [changes["location"]]
            
            preferences.updated_at = datetime.utcnow()
            await db.commit()

    async def _generate_updated_recommendations(self, user_id: str, db: AsyncSession):
        """Generate new recommendations based on updated preferences"""
        # Clear old recommendations
        await db.execute(
            update(EventRecommendation)
            .where(EventRecommendation.user_id == user_id)
            .values(is_active=False)
        )
        
        # Get updated preferences
        prefs_result = await db.execute(
            select(UserEventPreference).where(UserEventPreference.user_id == user_id)
        )
        preferences = prefs_result.scalar_one_or_none()
        
        if preferences:
            # Find matching events
            matching_events = await self._find_matching_events(preferences, db)
            recommendations = []
            
            for event, score in matching_events:
                recommendation = EventRecommendation(
                    user_id=user_id,
                    event_id=event.id,
                    recommendation_score=score,
                    reason="Matches your updated preferences",
                    created_at=datetime.utcnow()
                )
                recommendations.append(recommendation)
                db.add(recommendation)
            
            await db.commit()
            return recommendations
        
        return []