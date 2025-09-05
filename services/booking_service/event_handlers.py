from shared.event_handler import BaseEventHandler, SagaOrchestrator
from shared.event_schemas import EventType, BaseEvent
from shared.event_publisher import EventPublisher
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BookingServiceEventHandler(BaseEventHandler):
    
    def __init__(self):
        super().__init__("booking-service")
        self.publisher = EventPublisher("booking-service")
        self.saga = SagaOrchestrator("booking-service")
        self.setup_sagas()

    def setup_sagas(self):
        """Setup booking saga patterns"""
        # Booking confirmation saga
        self.saga.define_saga(
            "booking_confirmation",
            steps=[
                self.reserve_seats_step,
                self.create_payment_step,
                self.confirm_booking_step
            ],
            compensations=[
                self.cancel_booking_compensation,
                self.cancel_payment_compensation,
                self.release_seats_compensation
            ]
        )

    async def setup_handlers(self):
        """Setup event handlers for booking service"""
        self.register_handler(EventType.SEAT_RESERVED, self.handle_seat_reserved)
        self.register_handler(EventType.PAYMENT_COMPLETED, self.handle_payment_completed)
        self.register_handler(EventType.PAYMENT_FAILED, self.handle_payment_failed)

    async def handle_seat_reserved(self, event: BaseEvent):
        """Handle seat reservation confirmation"""
        seat_data = event.data
        booking_id = seat_data.get('booking_id')
        
        logger.info(f"Seat reserved for booking {booking_id}")
        # Update booking status in database

    async def handle_payment_completed(self, event: BaseEvent):
        """Handle payment completion - confirm booking"""
        payment_data = event.data
        booking_id = payment_data.get('booking_id')
        
        # Confirm the booking
        booking_data = {
            'booking_id': booking_id,
            'user_id': event.user_id,
            'status': 'confirmed',
            'payment_id': payment_data.get('payment_id'),
            'confirmed_at': event.timestamp.isoformat()
        }
        
        await self.publisher.publish_booking_confirmed(
            booking_data, 
            event.correlation_id
        )
        
        logger.info(f"Booking {booking_id} confirmed after successful payment")

    async def handle_payment_failed(self, event: BaseEvent):
        """Handle payment failure - cancel booking"""
        payment_data = event.data
        booking_id = payment_data.get('booking_id')
        
        # Cancel the booking
        booking_data = {
            'booking_id': booking_id,
            'user_id': event.user_id,
            'status': 'cancelled',
            'reason': 'payment_failed',
            'cancelled_at': event.timestamp.isoformat()
        }
        
        await self.publisher.publish_booking_cancelled(
            booking_data, 
            event.correlation_id
        )
        
        logger.info(f"Booking {booking_id} cancelled due to payment failure")

    # Saga Steps
    async def reserve_seats_step(self, context: Dict[str, Any]):
        """Reserve seats for booking"""
        try:
            booking_id = context.get('booking_id')
            seats = context.get('seats', [])
            
            logger.info(f"Reserving {len(seats)} seats for booking {booking_id}")
            
            # Publish seat reservation request for each seat
            for seat in seats:
                seat_reservation_data = {
                    'booking_id': booking_id,
                    'seat_id': seat.get('seat_id'),
                    'venue_section_id': seat.get('venue_section_id'),
                    'event_id': context.get('event_id'),
                    'user_id': context.get('user_id'),
                    'expires_at': context.get('expires_at'),
                    'price': seat.get('price')
                }
                
                await self.publisher.publish_event(
                    event_type=EventType.SEAT_RESERVATION_REQUESTED,
                    data=seat_reservation_data,
                    correlation_id=context.get('correlation_id')
                )
            
            context['seats_reservation_requested'] = True
            logger.info(f"Seat reservation requests sent for booking {booking_id}")
            
        except Exception as e:
            logger.error(f"Failed to reserve seats for booking {context.get('booking_id')}: {str(e)}")
            context['error'] = f"Seat reservation failed: {str(e)}"
            raise

    async def create_payment_step(self, context: Dict[str, Any]):
        """Create payment for booking"""
        try:
            booking_id = context.get('booking_id')
            total_amount = context.get('total_amount')
            user_email = context.get('user_email')
            payment_method = context.get('payment_method', 'stripe')
            
            logger.info(f"Creating payment for booking {booking_id}, amount: {total_amount}")
            
            payment_data = {
                'booking_id': booking_id,
                'user_id': context.get('user_id'),
                'amount': total_amount,
                'currency': context.get('currency', 'LKR'),
                'customer_email': user_email,
                'payment_method': payment_method,
                'description': f"Payment for booking {booking_id}",
                'metadata': {
                    'booking_id': booking_id,
                    'event_id': context.get('event_id')
                }
            }
            
            await self.publisher.publish_event(
                event_type=EventType.PAYMENT_INITIATED,
                data=payment_data,
                correlation_id=context.get('correlation_id')
            )
            
            context['payment_initiated'] = True
            logger.info(f"Payment creation request sent for booking {booking_id}")

        except Exception as e:
            logger.error(f"Failed to create payment for booking {context.get('booking_id')}: {str(e)}")
            context['error'] = f"Payment creation failed: {str(e)}"
            raise

    async def confirm_booking_step(self, context: Dict[str, Any]):
        """Confirm the booking"""
        try:
            booking_id = context.get('booking_id')
            
            logger.info(f"Confirming booking {booking_id}")
            
            # Update booking status in database
            # This would typically involve a database update
            booking_confirmation_data = {
                'booking_id': booking_id,
                'user_id': context.get('user_id'),
                'status': 'confirmed',
                'confirmed_at': context.get('confirmed_at'),
                'payment_id': context.get('payment_id'),
                'total_amount': context.get('total_amount')
            }
            
            await self.publisher.publish_booking_confirmed(
                booking_confirmation_data,
                context.get('correlation_id')
            )
            
            # Send confirmation email notification
            email_data = {
                'booking_id': booking_id,
                'user_email': context.get('user_email'),
                'customer_name': context.get('customer_name'),
                'event_id': context.get('event_id'),
                'seats': context.get('seats'),
                'total_amount': context.get('total_amount'),
                'booking_reference': context.get('booking_reference'),
                'template': 'booking_confirmation'
            }
            
            await self.publisher.publish_event(
                event_type=EventType.EMAIL_NOTIFICATION,
                data=email_data,
                correlation_id=context.get('correlation_id')
            )
            
            context['booking_confirmed'] = True
            logger.info(f"Booking {booking_id} confirmed successfully")
            
        except Exception as e:
            logger.error(f"Failed to confirm booking {context.get('booking_id')}: {str(e)}")
            context['error'] = f"Booking confirmation failed: {str(e)}"
            raise

    # Compensation Steps
    async def release_seats_compensation(self, context: Dict[str, Any]):
        """Release reserved seats"""
        try:
            booking_id = context.get('booking_id')
            seats = context.get('seats', [])
            
            logger.info(f"Releasing {len(seats)} seats for booking {booking_id}")
            
            # Only release seats if they were actually reserved
            if not context.get('seats_reservation_requested'):
                logger.info(f"No seats to release for booking {booking_id}")
                return
            
            for seat in seats:
                seat_release_data = {
                    'booking_id': booking_id,
                    'seat_id': seat.get('seat_id'),
                    'venue_section_id': seat.get('venue_section_id'),
                    'event_id': context.get('event_id'),
                    'reason': 'booking_cancelled'
                }
                
                await self.publisher.publish_event(
                    event_type=EventType.SEAT_RELEASED,
                    data=seat_release_data,
                    correlation_id=context.get('correlation_id')
                )
            
            logger.info(f"Seat release requests sent for booking {booking_id}")
            
        except Exception as e:
            logger.error(f"Failed to release seats for booking {context.get('booking_id')}: {str(e)}")

    async def cancel_payment_compensation(self, context: Dict[str, Any]):
        """Cancel payment"""
        try:
            booking_id = context.get('booking_id')
            payment_id = context.get('payment_id')
            
            logger.info(f"Cancelling payment for booking {booking_id}")
            
            # Only cancel payment if it was actually initiated
            if not context.get('payment_initiated'):
                logger.info(f"No payment to cancel for booking {booking_id}")
                return
            
            payment_cancellation_data = {
                'booking_id': booking_id,
                'payment_id': payment_id,
                'reason': 'booking_cancelled',
                'cancelled_at': context.get('cancelled_at')
            }
            
            await self.publisher.publish_event(
                event_type=EventType.PAYMENT_CANCELLED,
                data=payment_cancellation_data,
                correlation_id=context.get('correlation_id')
            )
            
            logger.info(f"Payment cancellation request sent for booking {booking_id}")
            
        except Exception as e:
            logger.error(f"Failed to cancel payment for booking {context.get('booking_id')}: {str(e)}")

    async def cancel_booking_compensation(self, context: Dict[str, Any]):
        """Cancel booking"""
        try:
            booking_id = context.get('booking_id')
            
            logger.info(f"Cancelling booking {booking_id}")
            
            booking_cancellation_data = {
                'booking_id': booking_id,
                'user_id': context.get('user_id'),
                'status': 'cancelled',
                'reason': context.get('cancellation_reason', 'saga_compensation'),
                'cancelled_at': context.get('cancelled_at'),
                'original_amount': context.get('total_amount')
            }
            
            await self.publisher.publish_event(
                event_type=EventType.BOOKING_CANCELLED,
                data=booking_cancellation_data,
                correlation_id=context.get('correlation_id')
            )
            
            # Send cancellation email notification
            email_data = {
                'booking_id': booking_id,
                'user_email': context.get('user_email'),
                'customer_name': context.get('customer_name'),
                'booking_reference': context.get('booking_reference'),
                'cancellation_reason': context.get('cancellation_reason', 'System error'),
                'template': 'booking_cancellation'
            }

            await self.publisher.publish_event(
                event_type=EventType.EMAIL_NOTIFICATION,
                data=email_data,
                correlation_id=context.get('correlation_id')
            )
            
            logger.info(f"Booking {booking_id} cancelled successfully")
            
        except Exception as e:
            logger.error(f"Failed to cancel booking {context.get('booking_id')}: {str(e)}")