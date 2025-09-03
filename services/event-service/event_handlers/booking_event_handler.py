import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from services.inventory_service import InventoryService
import logging

logger = logging.getLogger(__name__)

class EventServiceBookingHandler:
    def __init__(self):
        self.inventory_service = InventoryService()
        
    async def handle_booking_event(self, event_data):
        """Handle incoming booking service events"""
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        
        logger.info(f"Event service received booking event: {event_type}")
        
        try:
            if event_type == "booking_confirmed":
                await self._handle_booking_confirmed(data)
            elif event_type == "booking_cancelled":
                await self._handle_booking_cancelled(data)
                
        except Exception as e:
            logger.error(f"Error handling booking event {event_type}: {str(e)}")

    async def _handle_booking_confirmed(self, data):
        """When booking is confirmed, update seat inventory"""
        event_id = data.get("event_id")
        seat_ids = data.get("seat_ids", [])
        booking_id = data.get("booking_id")
        
        if not event_id or not seat_ids:
            logger.error("Missing event_id or seat_ids in booking_confirmed event")
            return
        
        try:
            await self.inventory_service.reserve_seats(
                event_id=event_id,
                seat_ids=seat_ids,
                booking_id=booking_id
            )
            logger.info(f"Seats reserved for booking {booking_id}: {seat_ids}")
        except Exception as e:
            logger.error(f"Failed to reserve seats for booking {booking_id}: {str(e)}")

    async def _handle_booking_cancelled(self, data):
        """When booking is cancelled, release seat inventory"""
        event_id = data.get("event_id")
        seat_ids = data.get("seat_ids", [])
        booking_id = data.get("booking_id")
        
        if not event_id or not seat_ids:
            logger.error("Missing event_id or seat_ids in booking_cancelled event")
            return
        
        try:
            await self.inventory_service.release_seats(
                event_id=event_id,
                seat_ids=seat_ids,
                booking_id=booking_id
            )
            logger.info(f"Seats released for cancelled booking {booking_id}: {seat_ids}")
        except Exception as e:
            logger.error(f"Failed to release seats for booking {booking_id}: {str(e)}")