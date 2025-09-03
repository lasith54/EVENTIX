import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from services.booking_workflow_service import BookingWorkflowService
import logging

logger = logging.getLogger(__name__)

class BookingServicePaymentHandler:
    def __init__(self):
        self.workflow_service = BookingWorkflowService()
        
    async def handle_payment_event(self, event_data):
        """Handle incoming payment service events"""
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        
        logger.info(f"Booking service received payment event: {event_type}")
        
        try:
            if event_type == "payment_completed":
                await self._handle_payment_completed(data)
            elif event_type == "payment_failed":
                await self._handle_payment_failed(data)
            elif event_type == "payment_refunded":
                await self._handle_payment_refunded(data)
                
        except Exception as e:
            logger.error(f"Error handling payment event {event_type}: {str(e)}")

    async def _handle_payment_completed(self, data):
        """When payment is completed, confirm the booking"""
        booking_id = data.get("booking_id")
        payment_id = data.get("payment_id")
        
        if not booking_id or not payment_id:
            logger.error("Missing booking_id or payment_id in payment_completed event")
            return
        
        try:
            await self.workflow_service.confirm_booking(booking_id, payment_id)
            logger.info(f"Booking {booking_id} confirmed after payment {payment_id}")
        except Exception as e:
            logger.error(f"Failed to confirm booking {booking_id}: {str(e)}")

    async def _handle_payment_failed(self, data):
        """When payment fails, cancel the booking"""
        booking_id = data.get("booking_id")
        failure_reason = data.get("failure_reason", "payment_failed")
        
        if not booking_id:
            logger.error("Missing booking_id in payment_failed event")
            return
        
        try:
            await self.workflow_service.cancel_booking(booking_id, f"payment_failed: {failure_reason}")
            logger.info(f"Booking {booking_id} cancelled due to payment failure")
        except Exception as e:
            logger.error(f"Failed to cancel booking {booking_id}: {str(e)}")

    async def _handle_payment_refunded(self, data):
        """When payment is refunded, update booking status"""
        booking_id = data.get("booking_id")
        
        if not booking_id:
            logger.error("Missing booking_id in payment_refunded event")
            return
        
        try:
            await self.workflow_service.cancel_booking(booking_id, "refund_processed")
            logger.info(f"Booking {booking_id} cancelled after refund")
        except Exception as e:
            logger.error(f"Failed to handle refund for booking {booking_id}: {str(e)}")