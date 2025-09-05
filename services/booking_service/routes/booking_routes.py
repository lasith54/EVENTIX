import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_async_db
from models import Booking, BookingItem, BookingStatus
from schemas import (
    BookingCreate, BookingResponse, BookingUpdate,
    BookingItemCreate, BookingItemResponse
)
from auth import get_current_user, TokenData

from shared.event_publisher import EventPublisher
from shared.event_schemas import EventType
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

publisher = EventPublisher("booking-service")

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_request: BookingCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        correlation_id = str(uuid.uuid4())

        logger.info(f"Booking request data: {booking_request.dict()}")
        
        booking = Booking(
            booking_reference=Booking.generate_reference(),
            user_id=str(current_user.user_id),
            **booking_request.dict(exclude={'items', 'payment_method'})
        )

        db.add(booking)
        await db.flush()
        logger.info("Booking added to database successfully")

        seats = [
            {
                'seat_id': item.seat_id,
                'section_name': getattr(item, 'section_name', 'Unknown'),
                'price': item.unit_price
            }
            for item in booking_request.items
        ]

        booking_data = {
            'booking_id': booking.id,
            'user_id': str(current_user.user_id),
            'event_id': str(booking_request.event_id),
            'seats': seats,
            'total_amount': booking_request.total_amount,
            'status': 'pending',
            'expires_at': (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
            'user_email': booking_request.customer_email,
            'payment_method': booking_request.payment_method
        }
        
        # Create booking items
        try:
            logger.info(f"Creating {len(booking_request.items)} booking items")
            for i, item_data in enumerate(booking_request.items):
                logger.info(f"Processing item {i+1}: {item_data.dict()}")
                
                item_dict = item_data.dict()
                item_dict['total_price'] = item_dict['unit_price'] * item_dict['quantity']
                logger.info(f"Item dict after exclusions: {item_dict}")
                
                booking_item = BookingItem(
                    booking_id=booking.id, 
                    **item_dict
                )
                db.add(booking_item)
                logger.info(f"Item {i+1} added successfully")
        except Exception as item_error:
            logger.error(f"Failed to create booking items: {str(item_error)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create booking items: {str(item_error)}"
            )
        

        logger.info("Committing transaction")
        await db.commit()
        await db.refresh(booking)
        logger.info("Booking committed successfully")
        
        try:
            await publisher.publish_booking_initiated(booking_data, correlation_id)
            logger.info("Event published successfully")
        except Exception as event_error:
            logger.error(f"Failed to publish booking initiated event: {str(event_error)}", exc_info=True)

        return {
            "booking_id": booking.id,
            "status": "initiated",
            "correlation_id": correlation_id,
            "message": "Booking initiated successfully"
        }
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error in create_booking: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")

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
    try:
        booking = await db.get(Booking, booking_id)
        if not booking or booking.user_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
        
        booking_data = {
            'booking_id': booking_id,
            'status': 'cancelled',
            'cancelled_at': datetime.utcnow().isoformat(),
            'reason': 'user_cancelled'
        }
        
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        await db.commit()
        
        await publisher.publish_booking_cancelled(booking_data)
            
        return {
            "booking_id": booking_id,
            "status": "cancelled",
            "message": "Booking cancelled successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel booking: {str(e)}")