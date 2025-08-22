from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from sqlalchemy import select

from database import get_async_db
from models import Refund, Payment, PaymentStatus
from schemas import RefundCreate, RefundResponse
from auth import get_current_user, TokenData

router = APIRouter(prefix="/refunds", tags=["Refunds"])

@router.post("/payments/{payment_id}/refund", response_model=RefundResponse)
async def create_refund(
    payment_id: UUID,
    refund_data: RefundCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a refund for a payment"""
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Payment cannot be refunded")
    
    refund = Refund(
        payment_id=payment_id,
        **refund_data.dict()
    )
    db.add(refund)
    await db.commit()
    await db.refresh(refund)
    return refund

@router.get("/payments/{payment_id}/refunds", response_model=List[RefundResponse])
async def list_refunds(
    payment_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List refunds for a payment"""
    query = select(Refund).where(Refund.payment_id == payment_id)
    result = await db.execute(query)
    return result.scalars().all()