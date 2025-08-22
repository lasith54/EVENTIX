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

router = APIRouter(prefix="/payments", tags=["Payments"])

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