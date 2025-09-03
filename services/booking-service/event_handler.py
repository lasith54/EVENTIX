import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.event_handler import BaseEventHandler
from workflow_handler import BookingWorkflowHandler
import logging

logger = logging.getLogger(__name__)

class BookingServiceEventHandler(BaseEventHandler):
    def __init__(self):
        super().__init__("booking-service")
        self.workflow_handler = BookingWorkflowHandler()

    async def handle_user_event(self, event_type: str, event_data: dict):
        """Handle user service events"""
        if event_type.endswith("_response"):
            await self.workflow_handler.handle_workflow_response(event_type, event_data)
        else:
            logger.info(f"Booking service received user event: {event_type}")

    async def handle_event_event(self, event_type: str, event_data: dict):
        """Handle event service events"""
        if event_type.endswith("_response"):
            await self.workflow_handler.handle_workflow_response(event_type, event_data)
        else:
            logger.info(f"Booking service received event event: {event_type}")

    async def handle_booking_event(self, event_type: str, event_data: dict):
        """Handle booking service events"""
        logger.info(f"Booking service received booking event: {event_type}")

    async def handle_payment_event(self, event_type: str, event_data: dict):
        """Handle payment service events"""
        if event_type.endswith("_response"):
            await self.workflow_handler.handle_workflow_response(event_type, event_data)
        else:
            logger.info(f"Booking service received payment event: {event_type}")