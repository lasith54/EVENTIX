from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select

from database import get_async_db
from models import SagaTransaction, SagaTransactionStep
from schemas import (
    SagaTransactionResponse,
    SagaStepResponse,
    SagaTransactionCreate
)
from auth import get_current_user, TokenData

router = APIRouter(prefix="/saga", tags=["Saga Transactions"])

@router.get("/transactions/{saga_id}", response_model=SagaTransactionResponse)
async def get_saga_transaction(
    saga_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(SagaTransaction).where(SagaTransaction.saga_id == saga_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.get("/transactions/{saga_id}/steps", response_model=List[SagaStepResponse])
async def get_saga_steps(
    saga_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(SagaTransaction).where(SagaTransaction.saga_id == saga_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction.steps