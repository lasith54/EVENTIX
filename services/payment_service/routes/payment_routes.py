import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

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

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new payment"""
    payment = Payment(
        user_id=current_user.user_id,
        **payment_data.dict()
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    await event_publisher.publish_payment_event("completed", {
        "payment_id": payment.id,
        "booking_id": payment_data.get("booking_id"),
        "payment_method_id": payment_data.get("payment_method_id"),
        "user_id": current_user.user_id,
        "amount": payment_data.get("amount"),
        "description": payment_data.get("description"),
        "status": "completed"
    })

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