from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from models import BookingStatus, SagaTransactionStatus, SagaStepStatus

class BookingItemCreate(BaseModel):
    seat_id: int
    venue_section_id: int
    unit_price: Decimal
    quantity: int = Field(default=1, gt=0)
    section_name: str
    seat_row: Optional[str] = None
    seat_number: Optional[str] = None
    pricing_tier: Optional[str] = None

class BookingCreate(BaseModel):
    event_id: int
    total_amount: Decimal
    currency: str = "LKR"
    special_requests: Optional[str] = None
    customer_email: str
    customer_phone: Optional[str] = None
    customer_name: str
    items: List[BookingItemCreate]

class BookingItemUpdate(BaseModel):
    quantity: Optional[int] = Field(default=None, gt=0)
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = None

class BookingUpdate(BaseModel):
    special_requests: Optional[str] = None
    booking_notes: Optional[str] = None
    customer_phone: Optional[str] = None
    status: Optional[BookingStatus] = None

class BookingItemResponse(BookingItemCreate):
    id: int
    booking_id: int
    total_price: Decimal
    is_cancelled: bool
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    user_id: int
    event_id: int
    status: BookingStatus
    total_amount: Decimal
    currency: str
    booking_date: datetime
    expiry_date: Optional[datetime]
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    items: List[BookingItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Saga-related schemas
class SagaStepResponse(BaseModel):
    id: int
    step_name: str
    step_order: int
    service_name: str
    status: SagaStepStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class SagaTransactionResponse(BaseModel):
    id: int
    saga_id: str
    booking_id: int
    transaction_type: str
    status: SagaTransactionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    steps: List[SagaStepResponse]

    class Config:
        from_attributes = True

class SagaStepCreate(BaseModel):
    step_name: str
    step_order: int
    service_name: str
    action: str
    compensation_action: Optional[str] = None
    payload: Optional[dict] = None

class SagaTransactionCreate(BaseModel):
    saga_id: str
    booking_id: int
    transaction_type: str
    steps: List[SagaStepCreate]
    metadata: Optional[dict] = None

class SagaStepUpdate(BaseModel):
    status: SagaStepStatus
    error_message: Optional[str] = None
    result_payload: Optional[dict] = None

class SagaTransactionUpdate(BaseModel):
    status: SagaTransactionStatus
    error_message: Optional[str] = None
    metadata: Optional[dict] = None

class MessageResponse(BaseModel):
    message: str
    details: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[dict] = None