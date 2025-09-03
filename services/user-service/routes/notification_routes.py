import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

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
from shared.event_publisher import EventPublisher
import logging
import uuid

logger = logging.getLogger(__name__)

event_publisher = EventPublisher("user-service")

router = APIRouter(
    prefix='/notification',
    tags=['User Notifications']
)

async_db_dependency = Annotated[AsyncSession, Depends(get_async_db)]

@router.get('/notifications', response_model=List[NotificationResponse])
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

    await event_publisher.publish_user_event("notifications_accessed", {
        "user_id": str(user.user_id),
        "email": user.email,
        "filter_type": "unread_only" if unread_only else "all",
        "notification_count": len(notifications),
        "limit": limit,
        "offset": offset,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info(f"User {user.email} accessed {len(notifications)} notifications")
    
    return notifications


@router.put('/notifications/{notification_id}/read', response_model=MessageResponse)
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
        await event_publisher.publish_user_event("notification_read_failed", {
            "user_id": str(user.user_id),
            "email": user.email,
            "notification_id": str(notification_id),
            "reason": "notification_not_found",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    was_unread = notification.read_at is None
    
    if not notification.read_at:
        notification.read_at = datetime.utcnow()
        await db.commit()

        await event_publisher.publish_user_event("notification_read", {
            "user_id": str(user.user_id),
            "email": user.email,
            "notification_id": str(notification.id),
            "notification_type": notification.type,
            "notification_title": notification.title,
            "read_at": notification.read_at.isoformat(),
            "was_previously_unread": was_unread,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    logger.info(f"Notification {notification_id} marked as read by user {user.email}")
    
    return MessageResponse(message="Notification marked as read")


@router.put('/notifications/read-all', response_model=MessageResponse)
async def mark_all_notifications_read(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    # Get count of unread notifications first
    unread_count_stmt = select(Notification).where(
        and_(
            Notification.user_id == user.user_id,
            Notification.read_at.is_(None)
        )
    )
    unread_result = await db.execute(unread_count_stmt)
    unread_notifications = unread_result.scalars().all()
    unread_count = len(unread_notifications)

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

    await event_publisher.publish_user_event("notifications_bulk_read", {
        "user_id": str(user.user_id),
        "email": user.email,
        "notifications_marked_read": unread_count,
        "notification_ids": [str(n.id) for n in unread_notifications],
        "marked_read_at": datetime.utcnow().isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info(f"User {user.email} marked {unread_count} notifications as read")
    return MessageResponse(message="All notifications marked as read")


@router.get('/notifications/unread-count')
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

    await event_publisher.publish_user_event("unread_count_checked", {
        "user_id": str(user.user_id),
        "email": user.email,
        "unread_count": count,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"unread_count": count}

@router.delete('/notifications/{notification_id}', response_model=MessageResponse)
async def delete_notification(
    notification_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Delete a specific notification"""
    try:
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
        
        notification_data = {
            "id": str(notification.id),
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "was_read": notification.read_at is not None
        }
        
        await db.delete(notification)
        await db.commit()
        
        # Publish notification deletion event
        await event_publisher.publish_user_event("notification_deleted", {
            "user_id": str(user.user_id),
            "email": user.email,
            "deleted_notification": notification_data,
            "deleted_at": datetime.utcnow().isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"Notification {notification_id} deleted by user {user.email}")
        return MessageResponse(message="Notification deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )