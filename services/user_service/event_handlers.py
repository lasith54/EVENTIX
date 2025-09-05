from shared.event_handler import BaseEventHandler
from shared.event_schemas import EventType, BaseEvent
from shared.event_publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

class UserServiceEventHandler(BaseEventHandler):
    
    def __init__(self):
        super().__init__("user-service")
        self.publisher = EventPublisher("user-service")

    async def setup_handlers(self):
        """Setup event handlers for user service"""
        self.register_handler(EventType.BOOKING_CONFIRMED, self.handle_booking_confirmed)
        self.register_handler(EventType.PAYMENT_COMPLETED, self.handle_payment_completed)

    async def handle_booking_confirmed(self, event: BaseEvent):
        """Handle booking confirmation - send notification"""
        user_id = event.user_id
        booking_data = event.data
        
        # Send email notification
        notification_data = {
            'user_id': user_id,
            'recipient': booking_data.get('user_email'),
            'subject': 'Booking Confirmation',
            'content': f"Your booking #{booking_data.get('booking_id')} has been confirmed!",
            'template': 'booking_confirmation',
            'booking_details': booking_data
        }
        
        await self.publisher.publish_email_notification(
            notification_data, 
            event.correlation_id
        )
        
        logger.info(f"Sent booking confirmation notification for user {user_id}")

    async def handle_payment_completed(self, event: BaseEvent):
        """Handle payment completion - send receipt"""
        user_id = event.user_id
        payment_data = event.data
        
        # Send payment receipt
        notification_data = {
            'user_id': user_id,
            'recipient': payment_data.get('user_email'),
            'subject': 'Payment Receipt',
            'content': f"Payment receipt for booking #{payment_data.get('booking_id')}",
            'template': 'payment_receipt',
            'payment_details': payment_data
        }
        
        await self.publisher.publish_email_notification(
            notification_data, 
            event.correlation_id
        )
        
        logger.info(f"Sent payment receipt for user {user_id}")