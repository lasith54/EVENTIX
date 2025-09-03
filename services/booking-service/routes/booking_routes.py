import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from database import get_async_db
from models import Booking, BookingItem, BookingStatus
from schemas import (
    BookingCreate, BookingResponse, BookingUpdate,
    BookingItemCreate, BookingItemResponse
)
from auth import get_current_user, TokenData
from workflow_handler import BookingWorkflowHandler

from shared.event_publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Bookings"])
workflow_handler = BookingWorkflowHandler()

@router.post("/create", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    workflow_id = await workflow_handler.start_booking_workflow(booking_data)

    return {
        "message": "Booking creation workflow started",
        "workflow_id": workflow_id
    }

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    status: Optional[BookingStatus] = None,
    skip: int = 0,
    limit: int = 20
):
    query = select(Booking).where(Booking.user_id == current_user.user_id)
    if status:
        query = query.where(Booking.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    booking = await db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
    
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    await db.commit()
    return booking