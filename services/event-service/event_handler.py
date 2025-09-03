import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.event_handler import BaseEventHandler
from workflow_handler import EventWorkflowHandler
import logging

logger = logging.getLogger(__name__)

class EventServiceEventHandler(BaseEventHandler):
    def __init__(self):
        super().__init__("event-service")
        self.workflow_handler = EventWorkflowHandler()

    async def handle_user_event(self, event_type: str, event_data: dict):
        """Handle user service events"""
        logger.info(f"Event service received user event: {event_type}")

    async def handle_event_event(self, event_type: str, event_data: dict):
        """Handle event service events"""
        if event_type == "seats.check_availability":
            await self.workflow_handler.handle_seat_availability_check(event_data)
        elif event_type == "seats.reserve":
            await self.workflow_handler.handle_seat_reservation(event_data)
        elif event_type == "seats.reserve.compensate":
            await self.workflow_handler.handle_seat_release(event_data)
        else:
            logger.info(f"Event service received event event: {event_type}")

    async def handle_booking_event(self, event_type: str, event_data: dict):
        """Handle booking service events"""
        logger.info(f"Event service received booking event: {event_type}")

    async def handle_payment_event(self, event_type: str, event_data: dict):
        """Handle payment service events"""
        logger.info(f"Event service received payment event: {event_type}")