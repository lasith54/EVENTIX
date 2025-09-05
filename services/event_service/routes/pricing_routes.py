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
    # Pricing schemas
    EventPricingTierCreate, EventPricingTierUpdate, EventPricingTierResponse,
    # Utility schemas
    PaginationParams, SearchFilters, EventSearchResponse, MessageResponse, ErrorResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pricing", tags=["pricing"])

def make_datetime_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    # Check if dt is not None and has timezone information
    if dt and dt.tzinfo is not None:
        # Convert to UTC and remove timezone information
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

@router.post("/{event_id}/pricing", response_model=EventPricingTierResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_pricing_tier(
    user: Annotated[TokenData, Depends(get_current_user)],
    event_id: uuid.UUID,
    pricing_data: EventPricingTierCreate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Create a new pricing tier for an event"""
    # Verify event exists
    event_query = select(Event).where(Event.id == event_id)
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Verify venue section exists and belongs to event's venue
    section_query = select(VenueSection).where(
        and_(
            VenueSection.id == pricing_data.venue_section_id,
            VenueSection.venue_id == event.venue_id
        )
    )
    section_result = await db.execute(section_query)
    if not section_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue section not found for this event's venue"
        )
    
    pricing_dict = pricing_data.model_dump()
    for key, value in pricing_dict.items():
        if isinstance(value, datetime):
            pricing_dict[key] = make_datetime_naive_utc(value)
    pricing_dict['available_seats'] = pricing_dict['total_seats']  # Initialize available seats
    pricing = EventPricingTier(event_id=event_id, **pricing_dict)
    db.add(pricing)
    await db.commit()
    
    query_with_joinedload = select(EventPricingTier).options(
        joinedload(EventPricingTier.venue_section)
    ).where(EventPricingTier.id == pricing.id)
    
    pricing_with_section_result = await db.execute(query_with_joinedload)
    pricing_with_section = pricing_with_section_result.scalar_one_or_none()

    # The result should not be None, but it's good practice to check
    if not pricing_with_section:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Newly created pricing tier not found"
        )

    return pricing_with_section


@router.put("/{pricing_id}", response_model=EventPricingTierResponse, dependencies=[Depends(get_current_user)])
async def update_pricing_tier(
    user: Annotated[TokenData, Depends(get_current_user)],
    pricing_id: uuid.UUID,
    pricing_data: EventPricingTierUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Update a pricing tier"""
    query = select(EventPricingTier).where(EventPricingTier.id == pricing_id)
    result = await db.execute(query)
    pricing = result.scalar_one_or_none()
    
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing tier not found"
        )
    
    # Update fields
    update_data = pricing_data.model_dump(exclude_unset=True)
    
    # Special handling for total_seats - update available_seats proportionally
    if 'total_seats' in update_data:
        old_total = pricing.total_seats
        new_total = update_data['total_seats']
        old_available = pricing.available_seats
        
        if old_total > 0:
            # Maintain the same ratio of available seats
            ratio = old_available / old_total
            pricing.available_seats = int(new_total * ratio)
    
    for field, value in update_data.items():
        if isinstance(value, datetime):
            update_data[field] = make_datetime_naive_utc(value)

    for field, value in update_data.items():
        setattr(pricing, field, value)
    
    await db.commit()
    
    eager_load_query = select(EventPricingTier).options(
        joinedload(EventPricingTier.venue_section)
    ).where(EventPricingTier.id == pricing_id)
    
    eager_load_result = await db.execute(eager_load_query)
    updated_pricing_tier = eager_load_result.scalar_one_or_none()
    
    if not updated_pricing_tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Updated pricing tier not found"
        )
    
    return updated_pricing_tier


@router.delete("/{pricing_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_pricing_tier(
    user: Annotated[TokenData, Depends(get_current_user)],
    pricing_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Deactivate a pricing tier"""
    query = select(EventPricingTier).where(EventPricingTier.id == pricing_id)
    result = await db.execute(query)
    pricing = result.scalar_one_or_none()
    
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing tier not found"
        )
    
    pricing.is_active = False
    await db.commit()
    return MessageResponse(message="Pricing tier deactivated successfully")
