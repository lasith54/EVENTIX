from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Annotated
from auth import get_current_user, TokenData
import uuid
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

from database import get_async_db
from models import (
    Venue, VenueSection, Event, Seat, SeatReservation, EventPricingTier,
    SeatStatus, SeatType, ReservationStatus
)
from schemas import (
    SeatAvailabilityRequest, SeatAvailabilityResponse,
    MessageResponse, ErrorResponse
)

router = APIRouter(prefix="/utility", tags=["seat-utility"])

@router.post("/availability", response_model=SeatAvailabilityResponse)
async def check_seat_availability(
    availability_request: SeatAvailabilityRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Check seat availability for an event"""
    
    # Get all seats in the requested sections
    query = select(Seat).options(
        joinedload(Seat.venue_section)
    ).where(Seat.venue_section_id.in_(availability_request.venue_section_ids))
    
    if availability_request.seat_types:
        query = query.where(Seat.seat_type.in_(availability_request.seat_types))
    
    result = await db.execute(query)
    all_seats = result.scalars().unique().all()
    
    # Get existing reservations for this event
    reservation_query = select(SeatReservation).where(
        and_(
            SeatReservation.event_id == availability_request.event_id,
            SeatReservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
        )
    )
    reservation_result = await db.execute(reservation_query)
    reserved_seat_ids = {res.seat_id for res in reservation_result.scalars().all()}
    
    # Calculate availability
    available_seats = []
    unavailable_seats = []
    
    for seat in all_seats:
        if seat.id in reserved_seat_ids or seat.status != SeatStatus.AVAILABLE:
            unavailable_seats.append({
                "seat_id": seat.id,
                "row_number": seat.row_number,
                "seat_number": seat.seat_number,
                "reason": "reserved" if seat.id in reserved_seat_ids else seat.status
            })
        else:
            available_seats.append({
                "seat_id": seat.id,
                "row_number": seat.row_number,
                "seat_number": seat.seat_number,
                "seat_type": seat.seat_type,
                "venue_section_id": seat.venue_section_id,
                "venue_section_name": seat.venue_section.name
            })
    
    return SeatAvailabilityResponse(
        event_id=availability_request.event_id,
        total_seats=len(all_seats),
        available_seats=available_seats,
        unavailable_seats=unavailable_seats,
        availability_checked_at=datetime.utcnow()
    )


@router.post("/cleanup-expired", response_model=MessageResponse)
async def cleanup_expired_reservations(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_async_db)
):
    """Cleanup expired reservations (Admin only)"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can cleanup expired reservations"
        )
    
    # Find expired reservations that are still pending
    expired_query = select(SeatReservation).options(
        joinedload(SeatReservation.seat)
    ).where(
        and_(
            SeatReservation.status == ReservationStatus.PENDING,
            SeatReservation.expires_at < datetime.utcnow()
        )
    )
    
    result = await db.execute(expired_query)
    expired_reservations = result.scalars().unique().all()
    
    # Update expired reservations and free seats
    for reservation in expired_reservations:
        reservation.status = ReservationStatus.EXPIRED
        reservation.status_changed_at = datetime.utcnow()
        reservation.status_changed_by = "system"
        reservation.seat.status = SeatStatus.AVAILABLE
    
    await db.commit()
    
    logger.info(f"Cleaned up {len(expired_reservations)} expired reservations")
    return MessageResponse(message=f"Cleaned up {len(expired_reservations)} expired reservations")