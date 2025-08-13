# schemas.py
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from models import EventStatus, EventType, SeatType, VenueType


# Base Schemas
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class SearchFilters(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    event_type: Optional[EventType] = None
    category_id: Optional[uuid.UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    tags: Optional[List[str]] = None


# Venue Schemas
class VenueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    venue_type: VenueType
    address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    capacity: int = Field(..., gt=0)
    image_urls: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    contact_info: Optional[Dict[str, Any]] = None


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    venue_type: Optional[VenueType] = None
    address: Optional[str] = Field(None, min_length=1)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    capacity: Optional[int] = Field(None, gt=0)
    image_urls: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    contact_info: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class VenueSectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    capacity: int = Field(..., gt=0)
    seat_map: Optional[Dict[str, Any]] = None


class VenueSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    venue_id: uuid.UUID
    name: str
    description: Optional[str]
    capacity: int
    seat_map: Optional[Dict[str, Any]]
    created_at: datetime


class VenueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    description: Optional[str]
    venue_type: VenueType
    address: str
    city: str
    state: Optional[str]
    country: str
    postal_code: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    capacity: int
    image_urls: Optional[List[str]]
    amenities: Optional[List[str]]
    contact_info: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sections: Optional[List[VenueSectionResponse]] = None


# Event Category Schemas
class EventCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class EventCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class EventCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    description: Optional[str]
    parent_id: Optional[uuid.UUID]
    is_active: bool
    created_at: datetime
    subcategories: Optional[List['EventCategoryResponse']] = None


# Event Schedule Schemas
class EventScheduleCreate(BaseModel):
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    doors_open_time: Optional[datetime] = None
    timezone: str = Field(default="UTC", max_length=50)
    booking_opens_at: Optional[datetime] = None
    booking_closes_at: Optional[datetime] = None
    early_bird_ends_at: Optional[datetime] = None
    special_notes: Optional[str] = None


class EventScheduleUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    doors_open_time: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=50)
    booking_opens_at: Optional[datetime] = None
    booking_closes_at: Optional[datetime] = None
    early_bird_ends_at: Optional[datetime] = None
    special_notes: Optional[str] = None
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = None


class EventScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    event_id: uuid.UUID
    start_datetime: datetime
    end_datetime: Optional[datetime]
    doors_open_time: Optional[datetime]
    timezone: str
    booking_opens_at: Optional[datetime]
    booking_closes_at: Optional[datetime]
    early_bird_ends_at: Optional[datetime]
    is_cancelled: bool
    cancellation_reason: Optional[str]
    is_sold_out: bool
    special_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# Event Pricing Schemas
class EventPricingTierCreate(BaseModel):
    venue_section_id: uuid.UUID
    tier_name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_seats: int = Field(..., gt=0)
    min_purchase: int = Field(default=1, gt=0)
    max_purchase: int = Field(default=10, gt=0)
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None
    includes_benefits: Optional[List[str]] = None
    seat_type: SeatType = Field(default=SeatType.REGULAR)


class EventPricingTierUpdate(BaseModel):
    tier_name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    total_seats: Optional[int] = Field(None, gt=0)
    min_purchase: Optional[int] = Field(None, gt=0)
    max_purchase: Optional[int] = Field(None, gt=0)
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None
    includes_benefits: Optional[List[str]] = None
    seat_type: Optional[SeatType] = None
    is_active: Optional[bool] = None


class EventPricingTierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    event_id: uuid.UUID
    venue_section_id: uuid.UUID
    tier_name: str
    price: Decimal
    currency: str
    total_seats: int
    available_seats: int
    min_purchase: int
    max_purchase: int
    sale_starts_at: Optional[datetime]
    sale_ends_at: Optional[datetime]
    includes_benefits: Optional[List[str]]
    seat_type: SeatType
    is_active: bool
    is_sold_out: bool
    created_at: datetime
    updated_at: datetime
    venue_section: Optional[VenueSectionResponse] = None


# Event Schemas
class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    event_type: EventType
    venue_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    artist_performer: Optional[str] = Field(None, max_length=255)
    organizer: Optional[str] = Field(None, max_length=255)
    duration_minutes: Optional[int] = Field(None, gt=0)
    age_restriction: Optional[str] = Field(None, max_length=50)
    poster_image_url: Optional[str] = Field(None, max_length=500)
    banner_image_url: Optional[str] = Field(None, max_length=500)
    gallery_images: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None
    slug: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    schedules: Optional[List[EventScheduleCreate]] = None
    pricing_tiers: Optional[List[EventPricingTierCreate]] = None


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    venue_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    artist_performer: Optional[str] = Field(None, max_length=255)
    organizer: Optional[str] = Field(None, max_length=255)
    duration_minutes: Optional[int] = Field(None, gt=0)
    age_restriction: Optional[str] = Field(None, max_length=50)
    poster_image_url: Optional[str] = Field(None, max_length=500)
    banner_image_url: Optional[str] = Field(None, max_length=500)
    gallery_images: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None
    slug: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    description: Optional[str]
    short_description: Optional[str]
    event_type: EventType
    status: EventStatus
    venue_id: uuid.UUID
    category_id: Optional[uuid.UUID]
    artist_performer: Optional[str]
    organizer: Optional[str]
    duration_minutes: Optional[int]
    age_restriction: Optional[str]
    poster_image_url: Optional[str]
    banner_image_url: Optional[str]
    gallery_images: Optional[List[str]]
    video_urls: Optional[List[str]]
    slug: Optional[str]
    tags: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    venue: Optional[VenueResponse] = None
    category: Optional[EventCategoryResponse] = None
    schedules: Optional[List[EventScheduleResponse]] = None
    pricing_tiers: Optional[List[EventPricingTierResponse]] = None


class EventListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    short_description: Optional[str]
    event_type: EventType
    status: EventStatus
    artist_performer: Optional[str]
    poster_image_url: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    venue: Optional[VenueResponse] = None
    next_schedule: Optional[EventScheduleResponse] = None
    min_price: Optional[Decimal] = None


# Paginated Response
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


class EventListPaginatedResponse(BaseModel):
    items: List[EventListResponse]
    total: int
    page: int
    size: int
    pages: int


# Search Response
class EventSearchResponse(BaseModel):
    events: List[EventListResponse]
    total: int
    filters_applied: SearchFilters
    suggestions: Optional[List[str]] = None


# Error and Success Responses
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    status: str = "success"


EventCategoryResponse.model_rebuild()