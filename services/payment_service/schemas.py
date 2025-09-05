from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from models import PaymentStatus, PaymentMethodType, TransactionType

class PaymentCreate(BaseModel):
    booking_id: UUID
    payment_method_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    description: Optional[str] = None
    metadata: Optional[Dict] = None

class PaymentResponse(BaseModel):
    id: UUID
    booking_id: UUID
    user_id: UUID
    payment_method_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    reference_number: str
    description: Optional[str]
    metadata: Optional[Dict]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentMethodCreate(BaseModel):
    method_type: PaymentMethodType
    provider: str
    card_last_four: Optional[str]
    card_expiry: Optional[str]
    billing_details: Optional[Dict]

class PaymentMethodResponse(BaseModel):
    id: UUID
    user_id: UUID
    method_type: PaymentMethodType
    provider: str
    is_default: bool
    is_active: bool
    last_used_at: Optional[datetime]
    card_last_four: Optional[str]
    card_expiry: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RefundCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    reason: str
    metadata: Optional[Dict] = None

class RefundResponse(BaseModel):
    id: UUID
    payment_id: UUID
    amount: Decimal
    currency: str
    reason: str
    status: str
    metadata: Optional[Dict]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True