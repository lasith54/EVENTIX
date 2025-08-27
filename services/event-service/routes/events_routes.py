import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from typing_extensions import Annotated
from auth import get_current_user, TokenData
import uuid
from datetime import datetime

from database import get_async_db
from models import (
    Venue, VenueSection, EventCategory, Event, EventSchedule, 
    EventPricingTier, EventStatus, EventType, VenueType
)
from schemas import (
    # Event schemas
    EventCreate, EventUpdate, EventResponse, EventListResponse, EventListPaginatedResponse,
    # Utility schemas
    PaginationParams, SearchFilters, EventSearchResponse, MessageResponse, ErrorResponse
)
import logging

from shared.event_publisher import EventPublisher

logger = logging.getLogger(__name__)

event_publisher = EventPublisher("event-service")


router = APIRouter(prefix="/events", tags=["events"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_event(
    user: Annotated[TokenData, Depends(get_current_user)],
    event_data: EventCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new event with schedules and pricing tiers"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    # Verify venue exists
    venue_query = select(Venue).where(Venue.id == event_data.venue_id)
    venue_result = await db.execute(venue_query)
    if not venue_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    # Verify category exists if provided
    if event_data.category_id:
        category_query = select(EventCategory).where(EventCategory.id == event_data.category_id)
        category_result = await db.execute(category_query)
        if not category_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Create event
    event_dict = event_data.model_dump(exclude={'schedules', 'pricing_tiers'})
    event = Event(**event_dict)
    db.add(event)
    await db.flush()  # Get event ID without committing
    
    # Create schedules if provided
    if event_data.schedules:
        for schedule_data in event_data.schedules:
            schedule = EventSchedule(event_id=event.id, **schedule_data.model_dump())
            db.add(schedule)
    
    # Create pricing tiers if provided
    if event_data.pricing_tiers:
        for pricing_data in event_data.pricing_tiers:
            # Verify venue section exists
            section_query = select(VenueSection).where(
                and_(
                    VenueSection.id == pricing_data.venue_section_id,
                    VenueSection.venue_id == event_data.venue_id
                )
            )
            section_result = await db.execute(section_query)
            if not section_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Venue section {pricing_data.venue_section_id} not found for this venue"
                )
            
            pricing_dict = pricing_data.model_dump()
            pricing_dict['available_seats'] = pricing_dict['total_seats']  # Initialize available seats
            pricing = EventPricingTier(event_id=event.id, **pricing_dict)
            db.add(pricing)
    
    await db.commit()
    await db.refresh(event)
    
    # Return event with relationships
    # return await get_event(event.id, db)
    logger.info(f"Event created with ID: {event.id}")

    await event_publisher.publish_event_event("created", {
        "event_id": event.id,
        "title": event_data.get("title"),
        # "event_date": event_data.get("event_date"),
        "event_type": event_data.get("event_type"),
        "venue": event_data.get("venue_id"),
        "category": event_data.get("category_id"),
        "artist_performer": event_data.get("artist_performer"),
        "organizer": event_data.get("organizer"),
        "duration_minutes": event_data.get("duration_minutes"),
    })

    return MessageResponse(message="Event created successfully")


@router.get("/", response_model=EventListPaginatedResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[EventStatus] = None,
    event_type: Optional[EventType] = None,
    venue_id: Optional[uuid.UUID] = None,
    category_id: Optional[uuid.UUID] = None,
    city: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get events with pagination and filters"""
    
    # Base query with joins
    query = select(Event).options(
        joinedload(Event.venue).selectinload(Venue.sections),
        selectinload(Event.schedules),
        selectinload(Event.pricing_tiers)
    )
    
    # Count query
    count_query = select(func.count(Event.id))
    
    # Apply filters
    filters = []
    if status:
        filters.append(Event.status == status)
    if event_type:
        filters.append(Event.event_type == event_type)
    if venue_id:
        filters.append(Event.venue_id == venue_id)
    if category_id:
        filters.append(Event.category_id == category_id)
    if city:
        query = query.join(Venue).filter(Venue.city.ilike(f"%{city}%"))
        count_query = count_query.join(Venue).filter(Venue.city.ilike(f"%{city}%"))
    
    # Date filters (check schedules)
    if date_from or date_to:
        schedule_filters = []
        if date_from:
            schedule_filters.append(EventSchedule.start_datetime >= date_from)
        if date_to:
            schedule_filters.append(EventSchedule.start_datetime <= date_to)
        
        query = query.join(EventSchedule).filter(and_(*schedule_filters))
        count_query = count_query.join(EventSchedule).filter(and_(*schedule_filters))
    
    if filters:
        query = query.filter(and_(*filters))
        count_query = count_query.filter(and_(*filters))
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Event.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    events = result.scalars().unique().all()
    
    # Transform to list response format
    event_list = []
    for event in events:
        # Get next schedule
        next_schedule = None
        if event.schedules:
            future_schedules = [s for s in event.schedules if s.start_datetime > datetime.utcnow()]
            if future_schedules:
                next_schedule = min(future_schedules, key=lambda x: x.start_datetime)
        
        # Get minimum price
        min_price = None
        if event.pricing_tiers:
            min_price = min(tier.price for tier in event.pricing_tiers if tier.is_active)
        
        event_list.append(EventListResponse(
            id=event.id,
            title=event.title,
            short_description=event.short_description,
            event_type=event.event_type,
            status=event.status,
            artist_performer=event.artist_performer,
            poster_image_url=event.poster_image_url,
            tags=event.tags,
            created_at=event.created_at,
            venue=event.venue,
            next_schedule=next_schedule,
            min_price=min_price
        ))
    
    pages = (total + limit - 1) // limit
    
    return EventListPaginatedResponse(
        items=event_list,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages
    )


@router.post("/search", response_model=EventSearchResponse)
async def search_events(
    filters: SearchFilters,
    q: Optional[str] = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """Search events with full-text search and filters"""
    
    # Base search query
    search_conditions = [
        Event.title.ilike(f"%{q}%"),
        Event.description.ilike(f"%{q}%"),
        Event.artist_performer.ilike(f"%{q}%")
    ]
    
    query = select(Event).options(
        joinedload(Event.venue).joinedload(Venue.sections),
        selectinload(Event.schedules)
    ).filter(or_(*search_conditions))
    
    # Apply additional filters
    filter_conditions = []
    if filters.city:
        query = query.join(Venue).filter(Venue.city.ilike(f"%{filters.city}%"))
    if filters.country:
        if not any(isinstance(item, Venue) for item in query.column_descriptions):
            query = query.join(Venue)
        filter_conditions.append(Venue.country.ilike(f"%{filters.country}%"))
    if filters.event_type:
        filter_conditions.append(Event.event_type == filters.event_type)
    if filters.category_id:
        filter_conditions.append(Event.category_id == filters.category_id)
    
    if filter_conditions:
        query = query.filter(and_(*filter_conditions))
    
    # Date filters
    if filters.date_from or filters.date_to:
        schedule_filters = []
        if filters.date_from:
            schedule_filters.append(EventSchedule.start_datetime >= filters.date_from)
        if filters.date_to:
            schedule_filters.append(EventSchedule.start_datetime <= filters.date_to)
        
        query = query.join(EventSchedule).filter(and_(*schedule_filters))
    
    # Price filters
    if filters.price_min or filters.price_max:
        price_filters = []
        if filters.price_min:
            price_filters.append(EventPricingTier.price >= filters.price_min)
        if filters.price_max:
            price_filters.append(EventPricingTier.price <= filters.price_max)
        
        query = query.join(EventPricingTier).filter(and_(*price_filters))
    
    # Execute query
    query = query.order_by(Event.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    events = result.scalars().unique().all()
    
    # Convert to list response format
    event_list = []
    for event in events:
        next_schedule = None
        if event.schedules:
            future_schedules = [s for s in event.schedules if s.start_datetime > datetime.utcnow()]
            if future_schedules:
                next_schedule = min(future_schedules, key=lambda x: x.start_datetime)
        
        event_list.append(EventListResponse(
            id=event.id,
            title=event.title,
            short_description=event.short_description,
            event_type=event.event_type,
            status=event.status,
            artist_performer=event.artist_performer,
            poster_image_url=event.poster_image_url,
            tags=event.tags,
            created_at=event.created_at,
            venue=event.venue,
            next_schedule=next_schedule,
            min_price=None  # Could be calculated from pricing tiers
        ))
    
    return EventSearchResponse(
        events=event_list,
        total=len(event_list),
        filters_applied=filters
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific event by ID with all relationships"""
    query = select(Event).options(
        joinedload(Event.venue).selectinload(Venue.sections),
        joinedload(Event.category).selectinload(EventCategory.subcategories),
        selectinload(Event.schedules),
        selectinload(Event.pricing_tiers).selectinload(EventPricingTier.venue_section)
    ).where(Event.id == event_id)
    
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    print(event)
    event_response = EventResponse(
        id=event.id,
        title=event.title,
        short_description=event.short_description,
        description=event.description,
        event_type=event.event_type,
        status=event.status,
        venue_id=event.venue_id,
        category_id=event.category_id,
        artist_performer=event.artist_performer,
        organizer=event.organizer,
        duration_minutes=event.duration_minutes,
        age_restriction=event.age_restriction,
        poster_image_url=event.poster_image_url,
        banner_image_url=event.banner_image_url,
        gallery_images=event.gallery_images,
        video_urls=event.video_urls,
        slug=event.slug,
        tags=event.tags,
        metadata=event.event_metadata,
        created_at=event.created_at,
        updated_at=event.updated_at,
        venue=event.venue,
        category=event.category,
        schedules=event.schedules,
        pricing_tiers=event.pricing_tiers
    )
    return event_response


@router.put("/{event_id}", response_model=EventResponse, dependencies=[Depends(get_current_user)])
async def update_event(
    user: Annotated[TokenData, Depends(get_current_user)],
    event_id: uuid.UUID,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    """Update an event"""
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update fields
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await db.commit()
    return await get_event(event_id, db)


@router.delete("/{event_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_event(
    user: Annotated[TokenData, Depends(get_current_user)],
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    """Delete an event (set status to cancelled)"""
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event.status = EventStatus.CANCELLED
    await db.commit()
    return MessageResponse(message="Event cancelled successfully")