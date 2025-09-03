import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from services.payment_workflow_service import PaymentWorkflowService
import logging

logger = logging.getLogger(__name__)

class PaymentServiceBookingHandler:
    def __init__(self):
        self.workflow_service = PaymentWorkflowService()
        
    async def handle_booking_event(self, event_data):
        """Handle incoming booking service events"""
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        
        logger.info(f"Payment service received booking event: {event_type}")
        
        try:
            if event_type == "booking_created":
                await self._handle_booking_created(data)
            elif event_type == "booking_cancelled":
                await self._handle_booking_cancelled(data)
                
        except Exception as e:
            logger.error(f"Error handling booking event {event_type}: {str(e)}")

    async def _handle_booking_created(self, data):
        """When booking is created, initiate payment process"""
        booking_id = data.get("booking_id")
        user_id = data.get("user_id")
        total_amount = data.get("total_amount")
        
        if not all([booking_id, user_id, total_amount]):
            logger.error("Missing required fields in booking_created event")
            return
        
        try:
            await self.workflow_service.initiate_payment(
                booking_id=booking_id,
                user_id=user_id,
                amount=total_amount,
                description=f"Event ticket booking {booking_id}",
                metadata={
                    "event_id": data.get("event_id"),
                    "seat_ids": data.get("seat_ids"),
                    "customer_details": data.get("customer_details")
                }
            )
            logger.info(f"Payment initiated for booking {booking_id}")
        except Exception as e:
            logger.error(f"Failed to initiate payment for booking {booking_id}: {str(e)}")

    async def _handle_booking_cancelled(self, data):
        """When booking is cancelled, handle refund if needed"""
        booking_id = data.get("booking_id")
        refund_required = data.get("refund_required", False)
        payment_id = data.get("payment_id")
        
        if refund_required and payment_id:
            try:
                await self.workflow_service.process_refund(
                    payment_id=payment_id,
                    booking_id=booking_id,
                    reason=data.get("reason", "booking_cancelled")
                )
                logger.info(f"Refund processed for booking {booking_id}")
            except Exception as e:
                logger.error(f"Failed to process refund for booking {booking_id}: {str(e)}")