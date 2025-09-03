import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.event_publisher import EventPublisher
from sqlalchemy.orm import Session
from database import get_db
from models import Seat, SeatReservation, SeatStatus, ReservationStatus
import logging

logger = logging.getLogger(__name__)

class EventWorkflowHandler:
    def __init__(self):
        self.event_publisher = EventPublisher("event-service")

    async def handle_seat_availability_check(self, event_data: dict):
        """Handle seat availability check request"""
        workflow_id = event_data.get("workflow_id")
        context = event_data.get("context", {})
        booking_items = context.get("booking_items", [])
        
        db: Session = next(get_db())
        try:
            all_available = True
            unavailable_seats = []
            
            for item in booking_items:
                seat_id = item["seat_id"]
                seat = db.query(Seat).filter(Seat.id == seat_id).first()
                
                if not seat or seat.status != SeatStatus.AVAILABLE:
                    all_available = False
                    unavailable_seats.append(seat_id)
            
            # Send response back to booking service
            response_data = {
                "workflow_id": workflow_id,
                "step_name": "check_seat_availability",
                "success": all_available,
                "result": {
                    "available": all_available,
                    "unavailable_seats": unavailable_seats
                },
                "error": None if all_available else "Some seats are not available"
            }
            
            await self.event_publisher.publish_booking_event("seats.check_availability_response", response_data)
            logger.info(f"Seat availability check for workflow {workflow_id}: {'Available' if all_available else 'Not available'}")
            
        except Exception as e:
            logger.error(f"Error checking seat availability: {e}")
            # Send error response
            response_data = {
                "workflow_id": workflow_id,
                "step_name": "check_seat_availability",
                "success": False,
                "result": None,
                "error": str(e)
            }
            await self.event_publisher.publish_booking_event("seats.check_availability_response", response_data)
        finally:
            db.close()

    async def handle_seat_reservation(self, event_data: dict):
        """Handle seat reservation request"""
        workflow_id = event_data.get("workflow_id")
        context = event_data.get("context", {})
        booking_items = context.get("booking_items", [])
        booking_id = context.get("booking_id")
        user_id = context.get("user_id")
        
        db: Session = next(get_db())
        try:
            reserved_seats = []
            
            for item in booking_items:
                seat_id = item["seat_id"]
                
                # Create reservation
                reservation = SeatReservation(
                    seat_id=seat_id,
                    user_id=user_id,
                    booking_reference=context.get("booking_reference"),
                    status=ReservationStatus.CONFIRMED
                )
                db.add(reservation)
                
                # Update seat status
                seat = db.query(Seat).filter(Seat.id == seat_id).first()
                if seat:
                    seat.status = SeatStatus.OCCUPIED
                    reserved_seats.append(seat_id)
            
            db.commit()
            
            # Send success response
            response_data = {
                "workflow_id": workflow_id,
                "step_name": "reserve_seats",
                "success": True,
                "result": {"reserved_seats": reserved_seats},
                "error": None
            }
            
            await self.event_publisher.publish_booking_event("seats.reserve_response", response_data)
            logger.info(f"Reserved {len(reserved_seats)} seats for workflow {workflow_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error reserving seats: {e}")
            
            # Send error response
            response_data = {
                "workflow_id": workflow_id,
                "step_name": "reserve_seats",
                "success": False,
                "result": None,
                "error": str(e)
            }
            await self.event_publisher.publish_booking_event("seats.reserve_response", response_data)
        finally:
            db.close()

    async def handle_seat_release(self, event_data: dict):
        """Handle seat release (compensation)"""
        workflow_id = event_data.get("workflow_id")
        original_result = event_data.get("original_result", {})
        reserved_seats = original_result.get("reserved_seats", [])
        
        db: Session = next(get_db())
        try:
            for seat_id in reserved_seats:
                # Remove reservation
                db.query(SeatReservation).filter(
                    SeatReservation.seat_id == seat_id
                ).delete()
                
                # Update seat status back to available
                seat = db.query(Seat).filter(Seat.id == seat_id).first()
                if seat:
                    seat.status = SeatStatus.AVAILABLE
            
            db.commit()
            logger.info(f"Released {len(reserved_seats)} seats for workflow {workflow_id} compensation")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error releasing seats: {e}")
        finally:
            db.close()