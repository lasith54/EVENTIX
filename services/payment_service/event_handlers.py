from shared.event_handler import BaseEventHandler
from shared.event_schemas import EventType, BaseEvent
from shared.event_publisher import EventPublisher
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PaymentServiceEventHandler(BaseEventHandler):
    
    def __init__(self):
        super().__init__("payment-service")
        self.publisher = EventPublisher("payment-service")

    async def setup_handlers(self):
        """Setup event handlers for payment service"""
        self.register_handler(EventType.BOOKING_INITIATED, self.handle_booking_initiated)

    async def handle_booking_initiated(self, event: BaseEvent):
        """Handle booking initiation - create payment intent"""
        booking_data = event.data
        booking_id = booking_data.get('booking_id')
        amount = booking_data.get('total_amount')
        
        # Create payment intent (mock implementation)
        payment_data = {
            'payment_id': f"pay_{booking_id}",
            'booking_id': booking_id,
            'user_id': event.user_id,
            'amount': amount,
            'currency': 'USD',
            'payment_method': booking_data.get('payment_method', 'stripe'),
            'status': 'initiated'
        }
        
        # Simulate payment processing
        try:
            # Mock payment processing logic
            success = await self.process_payment(payment_data)
            
            if success:
                payment_data['status'] = 'completed'
                await self.publisher.publish_payment_completed(
                    payment_data, 
                    event.correlation_id
                )
                logger.info(f"Payment completed for booking {booking_id}")
            else:
                payment_data['status'] = 'failed'
                await self.publisher.publish_payment_failed(
                    payment_data, 
                    event.correlation_id
                )
                logger.error(f"Payment failed for booking {booking_id}")
                
        except Exception as e:
            logger.error(f"Payment processing error for booking {booking_id}: {e}")
            payment_data['status'] = 'failed'
            await self.publisher.publish_payment_failed(
                payment_data, 
                event.correlation_id
            )

    async def process_payment(self, payment_data: Dict[str, Any]) -> bool:
        """Mock payment processing"""
        # Simulate payment processing
        import random
        import asyncio
        
        await asyncio.sleep(1)  # Simulate processing time
        return random.choice([True, True, True, False])  # 75% success rate