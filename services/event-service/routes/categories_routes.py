from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
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
    # Category schemas
    EventCategoryCreate, EventCategoryUpdate, EventCategoryResponse,
    # Utility schemas
    PaginationParams, SearchFilters, EventSearchResponse, MessageResponse, ErrorResponse
)

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_category(
    user: Annotated[TokenData, Depends(get_current_user)],
    category_data: EventCategoryCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new event category"""
    print(f"User ID: {user.user_id}, Role: {user.role}")
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    if category_data.parent_id:
        parent_query = select(EventCategory).where(EventCategory.id == category_data.parent_id)
        parent_result = await db.execute(parent_query)
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
    
    category = EventCategory(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    logger.info(f"Created new category: {category.name}")
    return MessageResponse(message="Category created successfully")


@router.get("/", response_model=List[EventCategoryResponse])
async def get_categories(
    include_inactive: bool = False,
    parent_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get all event categories"""
    query = select(EventCategory)
    
    filters = []
    if not include_inactive:
        filters.append(EventCategory.is_active == True)
    if parent_id:
        filters.append(EventCategory.parent_id == parent_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(EventCategory.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{category_id}", response_model=EventCategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific category by ID"""
    # Get the main category
    query = select(EventCategory).where(EventCategory.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Get subcategories separately
    subcategories_query = select(EventCategory).where(EventCategory.parent_id == category_id)
    subcategories_result = await db.execute(subcategories_query)
    subcategories = subcategories_result.scalars().all()
    
    # Convert to dictionary to avoid SQLAlchemy relationship issues
    category_dict = {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "parent_id": category.parent_id,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "subcategories": [
            {
                "id": sub.id,
                "name": sub.name,
                "description": sub.description,
                "parent_id": sub.parent_id,
                "is_active": sub.is_active,
                "created_at": sub.created_at,
                "subcategories": None
            } for sub in subcategories
        ]
    }
    
    return category_dict


@router.put("/{category_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def update_category(
    user: Annotated[TokenData, Depends(get_current_user)],
    category_id: uuid.UUID,
    category_data: EventCategoryUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a category"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    query = select(EventCategory).where(EventCategory.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    await db.commit()
    await db.refresh(category)
    
    logger.info(f"Updated category: {category.name}")
    return MessageResponse(message="Category updated successfully.")
