import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Event, Seat, SeatReservation
from database import get_async_db
from shared.event_publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

class InventoryService:
    def __init__(self):
        self.event_publisher = EventPublisher("event-service")

    async def reserve_seats(self, event_id: str, seat_ids: list, booking_id: str):
        """Reserve seats for a confirmed booking"""
        async with get_async_db() as db:
            try:
                # Update seat status to reserved
                await db.execute(
                    update(Seat)
                    .where(Seat.id.in_(seat_ids))
                    .where(Seat.event_id == event_id)
                    .where(Seat.status == "available")
                    .values(
                        status="reserved",
                        reserved_at=datetime.utcnow(),
                        booking_id=booking_id
                    )
                )
                
                # Create seat reservations
                for seat_id in seat_ids:
                    reservation = SeatReservation(
                        seat_id=seat_id,
                        booking_id=booking_id,
                        event_id=event_id,
                        reserved_at=datetime.utcnow(),
                        status="confirmed"
                    )
                    db.add(reservation)
                
                await db.commit()
                
                # Update event available seat count
                await self._update_event_availability(event_id, db)
                
                # Publish inventory update event
                await self.event_publisher.publish_event_event("seat_inventory_updated", {
                    "event_id": event_id,
                    "seat_ids": seat_ids,
                    "booking_id": booking_id,
                    "action": "reserved",
                    "reserved_count": len(seat_ids),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Reserved {len(seat_ids)} seats for booking {booking_id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error reserving seats for booking {booking_id}: {str(e)}")
                raise

    async def release_seats(self, event_id: str, seat_ids: list, booking_id: str):
        """Release seats when booking is cancelled"""
        async with get_async_db() as db:
            try:
                # Update seat status back to available
                await db.execute(
                    update(Seat)
                    .where(Seat.id.in_(seat_ids))
                    .where(Seat.event_id == event_id)
                    .where(Seat.booking_id == booking_id)
                    .values(
                        status="available",
                        reserved_at=None,
                        booking_id=None
                    )
                )
                
                # Update seat reservations
                await db.execute(
                    update(SeatReservation)
                    .where(SeatReservation.seat_id.in_(seat_ids))
                    .where(SeatReservation.booking_id == booking_id)
                    .values(
                        status="cancelled",
                        cancelled_at=datetime.utcnow()
                    )
                )
                
                await db.commit()
                
                # Update event available seat count
                await self._update_event_availability(event_id, db)
                
                # Publish inventory update event
                await self.event_publisher.publish_event_event("seat_inventory_updated", {
                    "event_id": event_id,
                    "seat_ids": seat_ids,
                    "booking_id": booking_id,
                    "action": "released",
                    "released_count": len(seat_ids),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Released {len(seat_ids)} seats from booking {booking_id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error releasing seats for booking {booking_id}: {str(e)}")
                raise

    async def _update_event_availability(self, event_id: str, db: AsyncSession):
        """Update event's available seat count"""
        # Count available seats
        available_result = await db.execute(
            select(Seat)
            .where(Seat.event_id == event_id)
            .where(Seat.status == "available")
        )
        available_count = len(available_result.scalars().all())
        
        # Update event
        await db.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(available_seats=available_count)
        )