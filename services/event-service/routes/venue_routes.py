from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Annotated
from auth import get_current_user, TokenData
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from database import get_async_db
from models import (
    Venue, VenueSection, EventCategory, Event, EventSchedule, 
    EventPricingTier, EventStatus, EventType, VenueType
)
from schemas import (
    # Venue schemas
    VenueCreate, VenueUpdate, VenueResponse, VenueSectionCreate, VenueSectionResponse,
    # Utility schemas
    PaginationParams, SearchFilters, EventSearchResponse, MessageResponse, ErrorResponse
)

router = APIRouter(prefix="/venues", tags=["venues"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_venue(
    user: Annotated[TokenData, Depends(get_current_user)],
    venue_data: VenueCreate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Create a new venue"""
    venue = Venue(**venue_data.model_dump())
    db.add(venue)
    await db.commit()
    await db.refresh(venue)

    logger.info(f"Venue added: {venue_data.name}")
    return MessageResponse(message="Venue Added Successfully.")


@router.get("/", response_model=List[VenueResponse])
async def get_venues(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = None,
    country: Optional[str] = None,
    venue_type: Optional[VenueType] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_async_db)
):
    """Get all venues with optional filters"""
    query = select(Venue).options(selectinload(Venue.sections))
    
    # Apply filters
    filters = [Venue.is_active == is_active] if is_active is not None else []
    if city:
        filters.append(Venue.city.ilike(f"%{city}%"))
    if country:
        filters.append(Venue.country.ilike(f"%{country}%"))
    if venue_type:
        filters.append(Venue.venue_type == venue_type)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(Venue.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific venue by ID"""
    query = select(Venue).options(selectinload(Venue.sections)).where(Venue.id == venue_id)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()
    
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    return venue


@router.put("/{venue_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def update_venue(
    user: Annotated[TokenData, Depends(get_current_user)],
    venue_id: uuid.UUID,
    venue_data: VenueUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Update a venue"""
    query = select(Venue).where(Venue.id == venue_id)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()
    
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    # Update fields
    update_data = venue_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(venue, field, value)
    
    await db.commit()
    await db.refresh(venue)
    
    
    logger.info(f"Venue updated: {venue_data.name}")
    return MessageResponse(message="Venue Updated Successfully.")


@router.delete("/{venue_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_venue(
    user: Annotated[TokenData, Depends(get_current_user)],
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Delete a venue (soft delete by setting is_active to False)"""
    query = select(Venue).where(Venue.id == venue_id)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()
    
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    venue.is_active = False
    await db.commit()
    return MessageResponse(message="Venue deleted successfully")


@router.post("/{venue_id}/sections", response_model=VenueSectionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_venue_section(
    user: Annotated[TokenData, Depends(get_current_user)],
    venue_id: uuid.UUID,
    section_data: VenueSectionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Create a new section for a venue"""
    # Verify venue exists
    venue_query = select(Venue).where(Venue.id == venue_id)
    venue_result = await db.execute(venue_query)
    venue = venue_result.scalar_one_or_none()
    
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    section = VenueSection(venue_id=venue_id, **section_data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section