from shared.event_handler import BaseEventHandler
from shared.event_schemas import EventType, BaseEvent
from shared.event_publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

class EventServiceEventHandler(BaseEventHandler):
    
    def __init__(self):
        super().__init__("event-service")
        self.publisher = EventPublisher("event-service")

    async def setup_handlers(self):
        """Setup event handlers for event service"""
        self.register_handler(EventType.BOOKING_INITIATED, self.handle_booking_initiated)
        self.register_handler(EventType.BOOKING_CANCELLED, self.handle_booking_cancelled)

    async def handle_booking_initiated(self, event: BaseEvent):
        """Handle booking initiation - update seat availability"""
        booking_data = event.data
        event_id = booking_data.get('event_id')
        seats = booking_data.get('seats', [])
        
        # Update seat availability in database
        # This would interact with your event service database
        logger.info(f"Processing seat reservation for event {event_id}")
        
        # Publish seat reserved event
        for seat in seats:
            seat_data = {
                'event_id': event_id,
                'seat_id': seat.get('seat_id'),
                'section_id': seat.get('section_id'),
                'booking_id': booking_data.get('booking_id'),
                'user_id': event.user_id,
                'reserved_until': booking_data.get('expires_at')
            }
            
            await self.publisher.publish_seat_reserved(
                seat_data, 
                event.correlation_id
            )

    async def handle_booking_cancelled(self, event: BaseEvent):
        """Handle booking cancellation - release seats"""
        booking_data = event.data
        seats = booking_data.get('seats', [])
        
        # Release seats back to inventory
        for seat in seats:
            logger.info(f"Releasing seat {seat.get('seat_id')} from booking {booking_data.get('booking_id')}")
            
        logger.info(f"Released seats for cancelled booking {booking_data.get('booking_id')}")