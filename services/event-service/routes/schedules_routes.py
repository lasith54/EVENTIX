from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Annotated
from auth import get_current_user, TokenData
import uuid
from datetime import datetime, timezone

from database import get_async_db
from models import (
    Venue, VenueSection, EventCategory, Event, EventSchedule, 
    EventPricingTier, EventStatus, EventType, VenueType
)
from schemas import (
    # Schedule schemas
    EventScheduleCreate, EventScheduleUpdate, EventScheduleResponse,
    # Utility schemas
    PaginationParams, SearchFilters, EventSearchResponse, MessageResponse, ErrorResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])

def make_datetime_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Converts a timezone-aware datetime object to a timezone-naive UTC datetime.
    If the input is None, it returns None.
    """
    if dt and dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

@router.post("/{event_id}/schedules", response_model=EventScheduleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_schedule(
    user: Annotated[TokenData, Depends(get_current_user)],
    event_id: uuid.UUID,
    schedule_data: EventScheduleCreate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Create a new schedule for an event"""
    # Verify event exists
    event_query = select(Event).where(Event.id == event_id)
    event_result = await db.execute(event_query)
    if not event_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    schedule_dict = schedule_data.model_dump()
    
    # Convert all timezone-aware datetimes to timezone-naive UTC
    for key, value in schedule_dict.items():
        if isinstance(value, datetime):
            schedule_dict[key] = make_datetime_naive_utc(value)
    
    schedule = EventSchedule(event_id=event_id, **schedule_dict)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.put("/schedules/{schedule_id}", response_model=EventScheduleResponse, dependencies=[Depends(get_current_user)])
async def update_schedule(
    user: Annotated[TokenData, Depends(get_current_user)],
    schedule_id: uuid.UUID,
    schedule_data: EventScheduleUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Update an event schedule"""
    query = select(EventSchedule).where(EventSchedule.id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, datetime):
            # Convert the timezone-aware datetime to timezone-naive UTC
            setattr(schedule, field, make_datetime_naive_utc(value))
        else:
            # For non-datetime fields, set the value directly
            setattr(schedule, field, value)
    
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/schedules/{schedule_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_schedule(
    user: Annotated[TokenData, Depends(get_current_user)],
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Cancel a schedule"""
    query = select(EventSchedule).where(EventSchedule.id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    schedule.is_cancelled = True
    await db.commit()
    return MessageResponse(message="Schedule cancelled successfully")

