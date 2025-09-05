import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from .rabbitmq_client import rabbitmq_client
from .event_schemas import BaseEvent, EventType
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    """
    Central event publisher for publishing domain events
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.exchange_name = "eventix.events"

    async def publish_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish a domain event"""
        
        event_id = str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        
        event = BaseEvent(
            event_id=event_id,
            event_type=event_type,
            service_name=self.service_name,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id,
            user_id=user_id,
            data=data,
            metadata=metadata or {}
        )
        
        await rabbitmq_client.publish_message(
            exchange_name=self.exchange_name,
            routing_key=event_type.value,
            message=event.dict(),
            message_id=event_id,
            correlation_id=correlation_id
        )
        
        logger.info(f"Published event: {event_type.value} with ID: {event_id}")
        return event_id

    # User Events
    async def publish_user_created(self, user_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.USER_CREATED,
            user_data,
            user_id=user_data.get('user_id'),
            correlation_id=correlation_id
        )

    async def publish_user_updated(self, user_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.USER_UPDATED,
            user_data,
            user_id=user_data.get('user_id'),
            correlation_id=correlation_id
        )

    # Event Events
    async def publish_event_created(self, event_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.EVENT_CREATED,
            event_data,
            correlation_id=correlation_id
        )

    async def publish_event_updated(self, event_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.EVENT_UPDATED,
            event_data,
            correlation_id=correlation_id
        )

    # Booking Events
    async def publish_booking_initiated(self, booking_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.BOOKING_INITIATED,
            booking_data,
            user_id=booking_data.get('user_id'),
            correlation_id=correlation_id
        )

    async def publish_booking_confirmed(self, booking_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.BOOKING_CONFIRMED,
            booking_data,
            user_id=booking_data.get('user_id'),
            correlation_id=correlation_id
        )
    
    async def publish_booking_cancelled(self, booking_data: dict, correlation_id: str = None):
        return await self.publish_event(
            event_type=EventType.BOOKING_CANCELLED,
            data=booking_data,
            correlation_id=correlation_id
        )

    async def publish_seat_reserved(self, seat_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.SEAT_RESERVED,
            seat_data,
            user_id=seat_data.get('user_id'),
            correlation_id=correlation_id
        )

    # Payment Events
    async def publish_payment_completed(self, payment_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.PAYMENT_COMPLETED,
            payment_data,
            user_id=payment_data.get('user_id'),
            correlation_id=correlation_id
        )

    async def publish_payment_failed(self, payment_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.PAYMENT_FAILED,
            payment_data,
            user_id=payment_data.get('user_id'),
            correlation_id=correlation_id
        )

    # Notification Events
    async def publish_email_notification(self, notification_data: Dict[str, Any], correlation_id: str = None):
        return await self.publish_event(
            EventType.EMAIL_NOTIFICATION,
            notification_data,
            user_id=notification_data.get('user_id'),
            correlation_id=correlation_id
        )