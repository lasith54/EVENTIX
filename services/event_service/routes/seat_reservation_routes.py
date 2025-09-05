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
    SeatReservationCreate, SeatReservationUpdate, SeatReservationResponse,
    # Utility schemas
    MessageResponse, ErrorResponse
)

router = APIRouter(prefix="/reservations", tags=["seat-reservations"])

@router.post("/", response_model=SeatReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_seat_reservation(
    user: Annotated[TokenData, Depends(get_current_user)],
    reservation_data: SeatReservationCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new seat reservation"""
    
    # Verify seat exists and is available
    seat_query = select(Seat).where(Seat.id == reservation_data.seat_id)
    seat_result = await db.execute(seat_query)
    seat = seat_result.scalar_one_or_none()
    
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found"
        )
    
    if seat.status != SeatStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seat is not available (current status: {seat.status})"
        )
    
    # Verify event exists
    event_query = select(Event).where(Event.id == reservation_data.event_id)
    event_result = await db.execute(event_query)
    if not event_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check for existing active reservations for this seat/event
    existing_reservation_query = select(SeatReservation).where(
        and_(
            SeatReservation.seat_id == reservation_data.seat_id,
            SeatReservation.event_id == reservation_data.event_id,
            SeatReservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
        )
    )
    existing_result = await db.execute(existing_reservation_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat already has an active reservation for this event"
        )
    
    # Generate reservation ID
    reservation_id = f"RES-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Set expiration time (default 15 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    reservation_dict = reservation_data.model_dump()
    reservation_dict.update({
        'reservation_id': reservation_id,
        'user_id': user.user_id,
        'expires_at': expires_at
    })
    
    reservation = SeatReservation(**reservation_dict)
    db.add(reservation)
    
    # Update seat status
    seat.status = SeatStatus.RESERVED
    
    await db.commit()
    await db.refresh(reservation)
    
    logger.info(f"Created reservation {reservation_id} for seat {seat.row_number}{seat.seat_number}")
    return reservation


@router.get("/", response_model=List[SeatReservationResponse])
async def get_reservations(
    user: Annotated[TokenData, Depends(get_current_user)],
    event_id: Optional[uuid.UUID] = None,
    status: Optional[ReservationStatus] = None,
    user_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """Get reservations with filters"""
    
    query = select(SeatReservation).options(
        joinedload(SeatReservation.seat).joinedload(Seat.venue_section),
        joinedload(SeatReservation.event),
        joinedload(SeatReservation.pricing_tier)
    )
    
    # Apply filters
    filters = []
    if event_id:
        filters.append(SeatReservation.event_id == event_id)
    if status:
        filters.append(SeatReservation.status == status)
    
    # Users can only see their own reservations unless they're admin
    if user.role != "admin":
        filters.append(SeatReservation.user_id == user.user_id)
    elif user_id:  # Admin can filter by specific user
        filters.append(SeatReservation.user_id == user_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(SeatReservation.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().unique().all()


@router.get("/{reservation_id}", response_model=SeatReservationResponse)
async def get_reservation(
    user: Annotated[TokenData, Depends(get_current_user)],
    reservation_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific reservation"""
    
    query = select(SeatReservation).options(
        joinedload(SeatReservation.seat).joinedload(Seat.venue_section),
        joinedload(SeatReservation.event),
        joinedload(SeatReservation.pricing_tier)
    ).where(SeatReservation.reservation_id == reservation_id)
    
    result = await db.execute(query)
    reservation = result.scalar_one_or_none()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Users can only view their own reservations unless they're admin
    if user.role != "admin" and reservation.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return reservation


@router.put("/{reservation_id}", response_model=SeatReservationResponse)
async def update_reservation(
    user: Annotated[TokenData, Depends(get_current_user)],
    reservation_id: str,
    reservation_data: SeatReservationUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a reservation"""
    
    query = select(SeatReservation).options(
        joinedload(SeatReservation.seat)
    ).where(SeatReservation.reservation_id == reservation_id)
    
    result = await db.execute(query)
    reservation = result.scalar_one_or_none()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Users can only update their own reservations unless they're admin
    if user.role != "admin" and reservation.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update fields
    update_data = reservation_data.model_dump(exclude_unset=True)
    
    # Handle status changes
    old_status = reservation.status
    new_status = update_data.get('status', old_status)
    
    for field, value in update_data.items():
        setattr(reservation, field, value)
    
    # Update seat status based on reservation status change
    if old_status != new_status:
        if new_status == ReservationStatus.CONFIRMED:
            reservation.seat.status = SeatStatus.OCCUPIED
            reservation.confirmed_at = datetime.utcnow()
        elif new_status in [ReservationStatus.CANCELLED, ReservationStatus.EXPIRED]:
            reservation.seat.status = SeatStatus.AVAILABLE
            reservation.cancelled_at = datetime.utcnow()
        
        reservation.status_changed_at = datetime.utcnow()
        reservation.status_changed_by = str(user.user_id)
    
    await db.commit()
    await db.refresh(reservation)
    
    logger.info(f"Updated reservation {reservation_id}, status: {old_status} -> {new_status}")
    return reservation


@router.delete("/{reservation_id}", response_model=MessageResponse)
async def cancel_reservation(
    user: Annotated[TokenData, Depends(get_current_user)],
    reservation_id: str,
    cancellation_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel a reservation"""
    
    query = select(SeatReservation).options(
        joinedload(SeatReservation.seat)
    ).where(SeatReservation.reservation_id == reservation_id)
    
    result = await db.execute(query)
    reservation = result.scalar_one_or_none()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Users can only cancel their own reservations unless they're admin
    if user.role != "admin" and reservation.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if reservation.status in [ReservationStatus.CANCELLED, ReservationStatus.EXPIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation is already cancelled or expired"
        )
    
    # Update reservation
    reservation.status = ReservationStatus.CANCELLED
    reservation.cancelled_at = datetime.utcnow()
    reservation.status_changed_at = datetime.utcnow()
    reservation.status_changed_by = str(user.user_id)
    if cancellation_reason:
        reservation.cancellation_reason = cancellation_reason
    
    # Free up the seat
    reservation.seat.status = SeatStatus.AVAILABLE
    
    await db.commit()
    
    logger.info(f"Cancelled reservation {reservation_id}")
    return MessageResponse(message="Reservation cancelled successfully")