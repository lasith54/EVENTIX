from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as SQLEnum
from database import Base  # Your SQLAlchemy Base from database.py
from enum import Enum
import uuid
from datetime import datetime

class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    SOLD_OUT = "sold_out"

class EventType(str, Enum):
    CONCERT = "concert"
    SPORTS = "sports"
    THEATER = "theater"
    CONFERENCE = "conference"
    COMEDY = "comedy"
    EXHIBITION = "exhibition"
    OTHER = "other"


class SeatType(str, Enum):
    REGULAR = "regular"
    VIP = "vip"
    PREMIUM = "premium"
    WHEELCHAIR_ACCESSIBLE = "wheelchair_accessible"


class VenueType(str, Enum):
    STADIUM = "stadium"
    ARENA = "arena"
    THEATER = "theater"
    CONCERT_HALL = "concert_hall"
    CONFERENCE_CENTER = "conference_center"
    OUTDOOR = "outdoor"
    OTHER = "other"


class SeatStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

# Database Models
class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    venue_type = Column(SQLEnum(VenueType), nullable=False, index=True)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    capacity = Column(Integer, nullable=False)
    image_urls = Column(JSONB, nullable=True)  # Array of image URLs
    amenities = Column(JSONB, nullable=True)  # Array of amenities
    contact_info = Column(JSONB, nullable=True)  # Contact details
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sections = relationship("VenueSection", back_populates="venue", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="venue")


class VenueSection(Base):
    __tablename__ = "venue_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Section A", "VIP", "General Admission"
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)
    seat_map = Column(JSONB, nullable=True)  # Detailed seat layout
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    venue = relationship("Venue", back_populates="sections")
    pricing_tiers = relationship("EventPricingTier", back_populates="venue_section")
    seats = relationship("Seat", back_populates="venue_section", cascade="all, delete-orphan")


class EventCategory(Base):
    __tablename__ = "event_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("event_categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Self-referential relationship for category hierarchy
    parent = relationship("EventCategory", remote_side=[id], backref="subcategories")
    events = relationship("Event", back_populates="category")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    status = Column(SQLEnum(EventStatus), default=EventStatus.DRAFT, nullable=False, index=True)
    
    # Venue and Category
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("event_categories.id"), nullable=True, index=True)
    
    # Event Details
    artist_performer = Column(String(255), nullable=True)
    organizer = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    age_restriction = Column(String(50), nullable=True)  # e.g., "18+", "All Ages"
    
    # Media
    poster_image_url = Column(String(500), nullable=True)
    banner_image_url = Column(String(500), nullable=True)
    gallery_images = Column(JSONB, nullable=True)  # Array of image URLs
    video_urls = Column(JSONB, nullable=True)  # Array of video URLs
    
    # SEO and metadata
    slug = Column(String(255), nullable=True, unique=True, index=True)
    tags = Column(JSONB, nullable=True)  # Array of tags for search
    event_metadata = Column(JSONB, nullable=True)  # Additional flexible data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    venue = relationship("Venue", back_populates="events")
    category = relationship("EventCategory", back_populates="events")
    schedules = relationship("EventSchedule", back_populates="event", cascade="all, delete-orphan")
    pricing_tiers = relationship("EventPricingTier", back_populates="event", cascade="all, delete-orphan")
    seat_reservations = relationship("SeatReservation", back_populates="event", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_venue_status', 'venue_id', 'status'),
        Index('idx_event_type_status', 'event_type', 'status'),
    )


class EventSchedule(Base):
    __tablename__ = "event_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    
    # Schedule Details
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=True, index=True)
    doors_open_time = Column(DateTime, nullable=True)
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Booking Details
    booking_opens_at = Column(DateTime, nullable=True, index=True)
    booking_closes_at = Column(DateTime, nullable=True, index=True)
    early_bird_ends_at = Column(DateTime, nullable=True)
    
    # Status
    is_cancelled = Column(Boolean, default=False, nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    is_sold_out = Column(Boolean, default=False, nullable=False)
    
    # Notes
    special_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="schedules")
    
    # Indexes
    __table_args__ = (
        Index('idx_schedule_datetime', 'start_datetime', 'end_datetime'),
        Index('idx_schedule_booking', 'booking_opens_at', 'booking_closes_at'),
    )


class EventPricingTier(Base):
    __tablename__ = "event_pricing_tiers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    venue_section_id = Column(UUID(as_uuid=True), ForeignKey("venue_sections.id"), nullable=False, index=True)
    
    # Pricing Details
    tier_name = Column(String(100), nullable=False)  # e.g., "Early Bird", "Regular", "VIP"
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Availability
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    min_purchase = Column(Integer, default=1, nullable=False)
    max_purchase = Column(Integer, default=10, nullable=False)
    
    # Timing
    sale_starts_at = Column(DateTime, nullable=True)
    sale_ends_at = Column(DateTime, nullable=True)
    
    # Features
    includes_benefits = Column(JSONB, nullable=True)  # Array of benefits
    seat_type = Column(SQLEnum(SeatType), default=SeatType.REGULAR, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_sold_out = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="pricing_tiers")
    venue_section = relationship("VenueSection", back_populates="pricing_tiers")
    
    # Indexes
    __table_args__ = (
        Index('idx_pricing_event_section', 'event_id', 'venue_section_id'),
        Index('idx_pricing_sale_period', 'sale_starts_at', 'sale_ends_at'),
    )


class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_section_id = Column(UUID(as_uuid=True), ForeignKey("venue_sections.id"), nullable=False, index=True)
    
    # Seat Identification
    row_number = Column(String(10), nullable=False)  # e.g., "A", "1", "AA"
    seat_number = Column(String(10), nullable=False)  # e.g., "1", "12", "101"
    seat_label = Column(String(20), nullable=True)    # e.g., "A1", "Row 1 Seat 12"
    
    # Seat Properties
    seat_type = Column(SQLEnum(SeatType), default=SeatType.REGULAR, nullable=False)
    status = Column(SQLEnum(SeatStatus), default=SeatStatus.AVAILABLE, nullable=False, index=True)
    
    # Physical Properties
    x_coordinate = Column(Numeric(8, 4), nullable=True)  # For seat mapping visualization
    y_coordinate = Column(Numeric(8, 4), nullable=True)  # For seat mapping visualization
    is_accessible = Column(Boolean, default=False, nullable=False)
    has_table = Column(Boolean, default=False, nullable=False)
    
    # Additional Properties
    attributes = Column(JSONB, nullable=True)  # Flexible attributes (e.g., {"view": "stage", "amenities": ["cup_holder"]})
    notes = Column(Text, nullable=True)
    
    # Status Management
    blocked_reason = Column(Text, nullable=True)  # Reason if status is BLOCKED or MAINTENANCE
    blocked_until = Column(DateTime, nullable=True)  # Temporary blocks
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    venue_section = relationship("VenueSection", back_populates="seats")
    reservations = relationship("SeatReservation", back_populates="seat", cascade="all, delete-orphan")
    
    # Indexes and Constraints
    __table_args__ = (
        Index('idx_seat_type_status', 'seat_type', 'status'),
        Index('idx_seat_status', 'status'),
        Index('idx_unique_seat_per_section', 'venue_section_id', 'row_number', 'seat_number', unique=True),
    )


class SeatReservation(Base):
    __tablename__ = "seat_reservations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    seat_id = Column(UUID(as_uuid=True), ForeignKey("seats.id"), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    
    # Reservation Details
    reservation_id = Column(String(100), nullable=False, unique=True, index=True)  # External booking reference
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # User who made the reservation (from User Service)
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False, index=True)
    
    # Timing
    reserved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)  # When this reservation expires
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Pricing Information
    reserved_price = Column(Numeric(10, 2), nullable=False)  # Price at time of reservation
    currency = Column(String(3), nullable=False, default="USD")
    pricing_tier_id = Column(UUID(as_uuid=True), ForeignKey("event_pricing_tiers.id"), nullable=True)
    
    # Additional Details
    reservation_source = Column(String(50), nullable=True)  # e.g., "web", "mobile", "box_office", "api"
    special_requirements = Column(JSONB, nullable=True)  # e.g., accessibility needs, dietary requirements
    customer_notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Metadata
    reservation_metadata = Column(JSONB, nullable=True)  # Flexible data storage
    
    # Status History
    status_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_changed_by = Column(String(100), nullable=True)  # User ID or system identifier
    cancellation_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    seat = relationship("Seat", back_populates="reservations")
    event = relationship("Event", back_populates="seat_reservations")
    pricing_tier = relationship("EventPricingTier")
    
    # Indexes
    __table_args__ = (
        Index('idx_reservation_seat_event', 'seat_id', 'event_id'),
        Index('idx_reservation_status_expires', 'status', 'expires_at'),
        Index('idx_reservation_user_status', 'user_id', 'status'),
        Index('idx_reservation_event_status', 'event_id', 'status'),
        Index('idx_reservation_expires_at', 'expires_at'),  # For cleanup jobs
        # Prevent duplicate active reservations for same seat/event
        Index('idx_unique_active_reservation', 'seat_id', 'event_id', 'status', 
              postgresql_where=text("status IN ('PENDING', 'CONFIRMED')"))
    )