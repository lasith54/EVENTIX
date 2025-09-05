from datetime import timedelta, datetime
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from starlette import status
from models import Notification
from schemas import MessageResponse, NotificationResponse
from database import get_async_db
from auth_handler import get_current_user, TokenData
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

async_db_dependency = Annotated[AsyncSession, Depends(get_async_db)]

@router.get('/', response_model=List[NotificationResponse])
async def get_user_notifications(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    """Get user notifications"""
    query = select(Notification).where(Notification.user_id == user.user_id)
    
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    
    query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return notifications


@router.put('/{notification_id}/read', response_model=MessageResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Mark a notification as read"""
    stmt = select(Notification).where(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user.user_id
        )
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if not notification.read_at:
        notification.read_at = datetime.utcnow()
        await db.commit()
    
    return MessageResponse(message="Notification marked as read")


@router.put('/read-all', response_model=MessageResponse)
async def mark_all_notifications_read(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Mark all user notifications as read"""
    await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.user_id == user.user_id,
                Notification.read_at.is_(None)
            )
        )
        .values(read_at=datetime.utcnow())
    )
    
    await db.commit()
    return MessageResponse(message="All notifications marked as read")


@router.get('/unread-count')
async def get_unread_notification_count(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Get count of unread notifications"""
    from sqlalchemy import func
    
    stmt = select(func.count(Notification.id)).where(
        and_(
            Notification.user_id == user.user_id,
            Notification.read_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    count = result.scalar()
    
    return {"unread_count": count}