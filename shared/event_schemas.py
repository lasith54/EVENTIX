from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    # User Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    
    # Event Events
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    EVENT_PUBLISHED = "event.published"
    EVENT_CANCELLED = "event.cancelled"
    
    # Booking Events
    BOOKING_INITIATED = "booking.initiated"
    BOOKING_CONFIRMED = "booking.confirmed"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_EXPIRED = "booking.expired"
    SEAT_RESERVED = "seat.reserved"
    SEAT_RELEASED = "seat.released"
    
    # Payment Events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Notification Events
    EMAIL_NOTIFICATION = "notification.email"
    SMS_NOTIFICATION = "notification.sms"
    PUSH_NOTIFICATION = "notification.push"

class BaseEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of the event")
    service_name: str = Field(..., description="Service that generated the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    user_id: Optional[str] = Field(None, description="User associated with the event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class UserEvent(BaseEvent):
    user_id: str
    email: str
    user_data: Optional[Dict[str, Any]] = None

class EventEvent(BaseEvent):
    event_id: str
    title: str
    venue_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None

class BookingEvent(BaseEvent):
    booking_id: str
    user_id: str
    event_id: str
    seats: List[Dict[str, Any]] = []
    total_amount: Optional[float] = None
    booking_data: Optional[Dict[str, Any]] = None

class PaymentEvent(BaseEvent):
    payment_id: str
    booking_id: str
    user_id: str
    amount: float
    payment_method: str
    payment_status: str
    payment_data: Optional[Dict[str, Any]] = None

class NotificationEvent(BaseEvent):
    recipient: str
    subject: Optional[str] = None
    content: str
    notification_type: str
    notification_data: Optional[Dict[str, Any]] = None