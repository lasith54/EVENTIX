from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select
from uuid import UUID

from database import get_async_db
from models import PaymentMethod
from schemas import PaymentMethodCreate, PaymentMethodResponse
from auth import get_current_user, TokenData

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])

@router.post("/", response_model=PaymentMethodResponse)
async def create_payment_method(
    method_data: PaymentMethodCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Add a new payment method"""
    method = PaymentMethod(
        user_id=current_user.user_id,
        **method_data.dict()
    )
    db.add(method)
    await db.commit()
    await db.refresh(method)
    return method

@router.get("/", response_model=List[PaymentMethodResponse])
async def list_payment_methods(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List user's payment methods"""
    query = select(PaymentMethod).where(PaymentMethod.user_id == current_user.user_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    method_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a payment method"""
    method = await db.get(PaymentMethod, method_id)
    if not method or method.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Payment method not found")
    await db.delete(method)
    await db.commit()