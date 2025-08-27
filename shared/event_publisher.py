from datetime import datetime
from typing import Dict, Any
from .rabbitmq_client import rabbitmq_client
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, service_name: str):
        self.service_name = service_name

    async def publish_user_event(self, event_type: str, user_data: Dict[str, Any]):
        """Publish user-related events"""
        event_data = {
            "service": self.service_name,
            "event_type": event_type,
            "data": user_data
        }
        
        await rabbitmq_client.publish_event(
            exchange_name="user.events",
            routing_key=f"user.{event_type}",
            event_data=event_data
        )

    async def publish_event_event(self, event_type: str, event_data_payload: Dict[str, Any]):
        """Publish event-related events"""
        event_data = {
            "service": self.service_name,
            "event_type": event_type,
            "data": event_data_payload
        }
        
        await rabbitmq_client.publish_event(
            exchange_name="event.events",
            routing_key=f"event.{event_type}",
            event_data=event_data
        )

    async def publish_booking_event(self, event_type: str, booking_data: Dict[str, Any]):
        """Publish booking-related events"""
        event_data = {
            "service": self.service_name,
            "event_type": event_type,
            "data": booking_data
        }
        
        await rabbitmq_client.publish_event(
            exchange_name="booking.events",
            routing_key=f"booking.{event_type}",
            event_data=event_data
        )

    async def publish_payment_event(self, event_type: str, payment_data: Dict[str, Any]):
        """Publish payment-related events"""
        event_data = {
            "service": self.service_name,
            "event_type": event_type,
            "data": payment_data
        }
        
        await rabbitmq_client.publish_event(
            exchange_name="payment.events",
            routing_key=f"payment.{event_type}",
            event_data=event_data
        )