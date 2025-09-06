import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import time
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from sqlalchemy import select

from database import get_async_db
from models import Payment, PaymentStatus
from schemas import (
    PaymentCreate,
    PaymentResponse,
    PaymentMethodResponse
)
from auth import get_current_user, TokenData

from shared.event_publisher import EventPublisher

router = APIRouter(prefix="/payments", tags=["Payments"])
event_publisher = EventPublisher("payment-service")

def generate_reference_number() -> str:
    """Generate a unique reference number for payment"""
    prefix = "PAY"
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{timestamp}{random_suffix}"

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new payment"""
    reference_number = generate_reference_number()

    payment = Payment(
        user_id=current_user.user_id,
        reference_number=reference_number,
        **payment_data.dict()
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    try:
        # Try different possible method names based on your EventPublisher implementation
        if hasattr(event_publisher, 'publish_payment_completed'):
            await event_publisher.publish_payment_completed({
                "payment_id": str(payment.id),
                "booking_id": payment_data.booking_id,
                "payment_method_id": str(payment_data.payment_method_id),
                "user_id": str(current_user.user_id),
                "amount": float(payment_data.amount),
                "description": payment_data.description,
                "status": "completed",
                "reference_number": reference_number
            })
        elif hasattr(event_publisher, 'publish'):
            # Generic publish method
            await event_publisher.publish("payment_completed", {
                "payment_id": str(payment.id),
                "booking_id": payment_data.booking_id,
                "payment_method_id": str(payment_data.payment_method_id),
                "user_id": str(current_user.user_id),
                "amount": float(payment_data.amount),
                "description": payment_data.description,
                "status": "completed",
                "reference_number": reference_number
            })
        else:
            # If no suitable method found, just log it
            print(f"Payment created successfully: {payment.id}")

    except Exception as e:
        # Don't fail the payment creation if event publishing fails
        print(f"Failed to publish payment event: {e}")

    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get payment details"""
    payment = await db.get(Payment, payment_id)
    if not payment or payment.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 20,
    status: PaymentStatus = None
):
    """List user payments"""
    query = select(Payment).where(Payment.user_id == current_user.user_id)
    if status:
        query = query.where(Payment.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()