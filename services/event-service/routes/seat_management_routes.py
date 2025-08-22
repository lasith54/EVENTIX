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
    SeatCreate, SeatUpdate, SeatResponse, SeatBulkCreate,
    MessageResponse, ErrorResponse
)

router = APIRouter(prefix="/seats", tags=["seat-management"])

@router.post("/venue-sections/{section_id}/seats", response_model=SeatResponse, status_code=status.HTTP_201_CREATED)
async def create_seat(
    user: Annotated[TokenData, Depends(get_current_user)],
    section_id: uuid.UUID,
    seat_data: SeatCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new seat in a venue section"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create seats"
        )
    
    # Verify venue section exists
    section_query = select(VenueSection).where(VenueSection.id == section_id)
    section_result = await db.execute(section_query)
    section = section_result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue section not found"
        )
    
    # Check for duplicate seats
    existing_seat_query = select(Seat).where(
        and_(
            Seat.venue_section_id == section_id,
            Seat.row_number == seat_data.row_number,
            Seat.seat_number == seat_data.seat_number
        )
    )
    existing_result = await db.execute(existing_seat_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seat {seat_data.row_number}{seat_data.seat_number} already exists in this section"
        )
    
    seat = Seat(venue_section_id=section_id, **seat_data.model_dump())
    db.add(seat)
    await db.commit()
    await db.refresh(seat)
    
    logger.info(f"Created seat {seat.row_number}{seat.seat_number} in section {section_id}")
    return seat


@router.post("/venue-sections/{section_id}/seats/bulk", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_seats_bulk(
    user: Annotated[TokenData, Depends(get_current_user)],
    section_id: uuid.UUID,
    seats_data: SeatBulkCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create multiple seats at once"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create seats"
        )
    
    # Verify venue section exists
    section_query = select(VenueSection).where(VenueSection.id == section_id)
    section_result = await db.execute(section_query)
    if not section_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue section not found"
        )
    
    seats_to_create = []
    for seat_data in seats_data.seats:
        # Check for duplicates
        existing_seat_query = select(Seat).where(
            and_(
                Seat.venue_section_id == section_id,
                Seat.row_number == seat_data.row_number,
                Seat.seat_number == seat_data.seat_number
            )
        )
        existing_result = await db.execute(existing_seat_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seat {seat_data.row_number}{seat_data.seat_number} already exists"
            )
        
        seat = Seat(venue_section_id=section_id, **seat_data.model_dump())
        seats_to_create.append(seat)
    
    db.add_all(seats_to_create)
    await db.commit()
    
    logger.info(f"Created {len(seats_to_create)} seats in section {section_id}")
    return MessageResponse(message=f"Successfully created {len(seats_to_create)} seats")


@router.get("/venue-sections/{section_id}/seats", response_model=List[SeatResponse])
async def get_seats_by_section(
    section_id: uuid.UUID,
    status: Optional[SeatStatus] = None,
    seat_type: Optional[SeatType] = None,
    row_number: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get all seats in a venue section"""
    query = select(Seat).where(Seat.venue_section_id == section_id)
    
    # Apply filters
    filters = []
    if status:
        filters.append(Seat.status == status)
    if seat_type:
        filters.append(Seat.seat_type == seat_type)
    if row_number:
        filters.append(Seat.row_number == row_number)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Seat.row_number, Seat.seat_number)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/seats/{seat_id}", response_model=SeatResponse)
async def get_seat(
    seat_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific seat by ID"""
    query = select(Seat).options(
        joinedload(Seat.venue_section)
    ).where(Seat.id == seat_id)
    
    result = await db.execute(query)
    seat = result.scalar_one_or_none()
    
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found"
        )
    
    return seat


@router.put("/seats/{seat_id}", response_model=SeatResponse)
async def update_seat(
    user: Annotated[TokenData, Depends(get_current_user)],
    seat_id: uuid.UUID,
    seat_data: SeatUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a seat"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update seats"
        )
    
    query = select(Seat).where(Seat.id == seat_id)
    result = await db.execute(query)
    seat = result.scalar_one_or_none()
    
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found"
        )
    
    # Update fields
    update_data = seat_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(seat, field, value)
    
    await db.commit()
    await db.refresh(seat)
    
    logger.info(f"Updated seat {seat.row_number}{seat.seat_number}")
    return seat


@router.delete("/seats/{seat_id}", response_model=MessageResponse)
async def delete_seat(
    user: Annotated[TokenData, Depends(get_current_user)],
    seat_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a seat (only if no active reservations)"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete seats"
        )
    
    # Check for active reservations
    reservation_query = select(SeatReservation).where(
        and_(
            SeatReservation.seat_id == seat_id,
            SeatReservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
        )
    )
    reservation_result = await db.execute(reservation_query)
    if reservation_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete seat with active reservations"
        )
    
    # Delete the seat
    delete_query = delete(Seat).where(Seat.id == seat_id)
    result = await db.execute(delete_query)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found"
        )
    
    await db.commit()
    return MessageResponse(message="Seat deleted successfully")