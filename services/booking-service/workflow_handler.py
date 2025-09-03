import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.workflow_manager import WorkflowManager, WorkflowStep
from shared.event_publisher import EventPublisher
from sqlalchemy.orm import Session
from database import get_db
from models import Booking, BookingItem, BookingStatus, SagaTransaction, SagaTransactionStatus
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class BookingWorkflowHandler:
    def __init__(self):
        self.event_publisher = EventPublisher("booking-service")
        self.workflow_manager = WorkflowManager("booking-service", self.event_publisher)
        self._register_workflows()

    def _register_workflows(self):
        """Register workflow definitions"""
        
        # Booking Creation Workflow
        booking_steps = [
            WorkflowStep("validate_user", "user-service", "user.validate", 30),
            WorkflowStep("check_seat_availability", "event-service", "seats.check_availability", 30),
            WorkflowStep("create_payment_intent", "payment-service", "payment.create_intent", 30),
        ]
        self.workflow_manager.register_workflow_definition("booking_creation", booking_steps)

        # Booking Confirmation Workflow
        confirmation_steps = [
            WorkflowStep("reserve_seats", "event-service", "seats.reserve", 30),
            WorkflowStep("process_payment", "payment-service", "payment.process", 60),
            WorkflowStep("send_confirmation", "user-service", "notification.send", 30),
        ]
        self.workflow_manager.register_workflow_definition("booking_confirmation", confirmation_steps)

    async def start_booking_workflow(self, booking_data: dict) -> str:
        """Start the booking creation workflow"""
        db: Session = next(get_db())
        
        try:
            # Create booking record in PENDING status
            booking = Booking(
                booking_reference=self._generate_booking_reference(),
                user_id=booking_data["user_id"],
                event_id=booking_data["event_id"],
                status=BookingStatus.PENDING,
                total_amount=booking_data["total_amount"],
                currency=booking_data.get("currency", "LKR"),
                expiry_date=datetime.utcnow() + timedelta(minutes=15),
                customer_email=booking_data["customer_email"],
                customer_name=booking_data["customer_name"],
                customer_phone=booking_data.get("customer_phone")
            )
            
            db.add(booking)
            db.flush()  # Get the ID without committing
            
            # Create booking items
            for item_data in booking_data["booking_items"]:
                booking_item = BookingItem(
                    booking_id=booking.id,
                    seat_id=item_data["seat_id"],
                    venue_section_id=item_data["venue_section_id"],
                    seat_row=item_data.get("seat_row"),
                    seat_number=item_data.get("seat_number"),
                    section_name=item_data.get("section_name"),
                    unit_price=item_data["unit_price"],
                    quantity=item_data.get("quantity", 1)
                )
                db.add(booking_item)
            
            # Create saga transaction
            saga = SagaTransaction(
                booking_id=booking.id,
                status=SagaTransactionStatus.STARTED,
                workflow_type="booking_creation"
            )
            db.add(saga)
            
            db.commit()
            
            # Start workflow
            workflow_context = {
                "booking_id": str(booking.id),
                "booking_reference": booking.booking_reference,
                "user_id": str(booking.user_id),
                "event_id": str(booking.event_id),
                "total_amount": float(booking.total_amount),
                "currency": booking.currency,
                "booking_items": [
                    {
                        "seat_id": str(item.seat_id),
                        "venue_section_id": str(item.venue_section_id),
                        "unit_price": float(item.unit_price),
                        "quantity": item.quantity
                    } for item in booking.booking_items
                ],
                "customer_email": booking.customer_email,
                "customer_name": booking.customer_name
            }
            
            workflow_id = await self.workflow_manager.start_workflow("booking_creation", workflow_context)
            
            # Update saga with workflow ID
            saga.workflow_id = workflow_id
            saga.status = SagaTransactionStatus.IN_PROGRESS
            db.commit()
            
            logger.info(f"Started booking workflow for booking {booking.booking_reference}")
            return workflow_id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error starting booking workflow: {e}")
            raise
        finally:
            db.close()

    async def handle_workflow_response(self, event_type: str, event_data: dict):
        """Handle responses from other services in the workflow"""
        workflow_id = event_data.get("workflow_id")
        step_name = event_data.get("step_name")
        
        if not workflow_id or not step_name:
            logger.warning("Invalid workflow response: missing workflow_id or step_name")
            return

        success = event_data.get("success", False)
        result = event_data.get("result")
        error = event_data.get("error")

        await self.workflow_manager.handle_workflow_response(
            workflow_id, step_name, success, result, error
        )

        # Handle specific step completions
        if success:
            if step_name == "validate_user":
                await self._handle_user_validation_success(workflow_id, result)
            elif step_name == "check_seat_availability":
                await self._handle_seat_availability_success(workflow_id, result)
            elif step_name == "create_payment_intent":
                await self._handle_payment_intent_success(workflow_id, result)
        else:
            await self._handle_step_failure(workflow_id, step_name, error)

    async def _handle_user_validation_success(self, workflow_id: str, result: dict):
        """Handle successful user validation"""
        logger.info(f"User validation successful for workflow {workflow_id}")

    async def _handle_seat_availability_success(self, workflow_id: str, result: dict):
        """Handle successful seat availability check"""
        if result.get("available", False):
            logger.info(f"Seats available for workflow {workflow_id}")
        else:
            # Seats not available - fail the workflow
            await self.workflow_manager.handle_workflow_response(
                workflow_id, "check_seat_availability", False, None, "Seats not available"
            )

    async def _handle_payment_intent_success(self, workflow_id: str, result: dict):
        """Handle successful payment intent creation"""
        logger.info(f"Payment intent created for workflow {workflow_id}: {result.get('payment_intent_id')}")

    async def _handle_step_failure(self, workflow_id: str, step_name: str, error: str):
        """Handle workflow step failure"""
        logger.error(f"Workflow {workflow_id} step {step_name} failed: {error}")
        
        # Update booking status to cancelled
        db: Session = next(get_db())
        try:
            # Get workflow context to find booking
            workflow = self.workflow_manager.active_workflows.get(workflow_id)
            if workflow:
                booking_id = workflow.context.get("booking_id")
                if booking_id:
                    booking = db.query(Booking).filter(Booking.id == booking_id).first()
                    if booking:
                        booking.status = BookingStatus.CANCELLED
                        booking.cancelled_at = datetime.utcnow()
                        db.commit()
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            db.rollback()
        finally:
            db.close()

    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference"""
        return f"BK{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"