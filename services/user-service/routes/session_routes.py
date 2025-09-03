import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import timedelta, datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from starlette import status
from models import UserSession
from schemas import MessageResponse, UserSessionResponse
from database import get_async_db
from auth_handler import get_current_user, TokenData
from shared.event_publisher import EventPublisher
import logging
import uuid
import secrets

logger = logging.getLogger(__name__)

event_publisher = EventPublisher("user-service")

router = APIRouter(
    prefix='/session',
    tags=['User Sessions']
)

async_db_dependency = Annotated[AsyncSession, Depends(get_async_db)]

@router.get('/sessions', response_model=List[UserSessionResponse])
async def get_user_sessions(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    active_only: bool = True
):
    """Get all user sessions"""
    try:
        query = select(UserSession).where(UserSession.user_id == user.user_id)

        if active_only:
            query = query.where(
                and_(
                    UserSession.expires_at > datetime.utcnow(),
                    UserSession.revoked_at.is_(None)
                )
            )

        query = query.order_by(UserSession.created_at.desc())
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        # Publish sessions access event
        await event_publisher.publish_user_event("sessions_accessed", {
            "user_id": str(user.user_id),
            "email": user.email,
            "filter_type": "active_only" if active_only else "all",
            "session_count": len(sessions),
            "active_sessions": len([s for s in sessions if s.expires_at > datetime.utcnow() and not s.revoked_at]),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"User {user.email} accessed {len(sessions)} sessions")
        return sessions
        
    except Exception as e:
        logger.error(f"Error fetching sessions for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post('/sessions', response_model=UserSessionResponse)
async def create_session(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    session_data: UserSessionResponse,
    request: Request
):
    """Create a new session"""
    try:
        # Generate session token
        session_token = secrets.token_urlsafe(64)
        
        # Get client information
        user_agent = request.headers.get("User-Agent", "Unknown")
        ip_address = request.client.host if request.client else "Unknown"
        
        # Create session
        new_session = UserSession(
            user_id=user.user_id,
            session_token=session_token,
            device_info=session_data.device_info or user_agent,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(hours=session_data.expires_hours or 24),
            created_at=datetime.utcnow()
        )
        
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        # Publish session creation event
        await event_publisher.publish_user_event("session_created", {
            "user_id": str(user.user_id),
            "email": user.email,
            "session_id": str(new_session.id),
            "device_info": new_session.device_info,
            "ip_address": new_session.ip_address,
            "expires_at": new_session.expires_at.isoformat(),
            "created_at": new_session.created_at.isoformat(),
            "expires_in_hours": session_data.expires_hours or 24,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"New session created for user {user.email}")
        return new_session
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating session for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.get('/sessions/current', response_model=UserSessionResponse)
async def get_current_session(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    request: Request
):
    """Get current session information"""
    try:
        # Try to identify current session by IP and User-Agent
        user_agent = request.headers.get("User-Agent", "Unknown")
        ip_address = request.client.host if request.client else "Unknown"
        
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user.user_id,
                UserSession.ip_address == ip_address,
                UserSession.expires_at > datetime.utcnow(),
                UserSession.revoked_at.is_(None)
            )
        ).order_by(UserSession.created_at.desc())

        result = await db.execute(stmt)
        current_session = result.scalars().first()
        
        if not current_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current session not found"
            )
        
        # Publish current session access event
        await event_publisher.publish_user_event("current_session_accessed", {
            "user_id": str(user.user_id),
            "email": user.email,
            "session_id": str(current_session.id),
            "device_info": current_session.device_info,
            "ip_address": current_session.ip_address,
            "session_age_hours": (datetime.utcnow() - current_session.created_at).total_seconds() / 3600,
            "timestamp": datetime.utcnow().isoformat()
        })

        return current_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current session for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.put('/sessions/{session_id}/revoke', response_model=MessageResponse)
async def revoke_session(
    session_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Revoke a specific session"""
    try:
        stmt = select(UserSession).where(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user.user_id
            )
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session.revoked_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session already revoked"
            )
        
        # Store session data before revoking
        session_data = {
            "id": str(session.id),
            "device_info": session.device_info,
            "ip_address": session.ip_address,
            "created_at": session.created_at.isoformat(),
            "was_active": session.expires_at > datetime.utcnow()
        }
        
        # Revoke session
        session.revoked_at = datetime.utcnow()
        await db.commit()
        
        # Publish session revocation event
        await event_publisher.publish_user_event("session_revoked", {
            "user_id": str(user.user_id),
            "email": user.email,
            "revoked_session": session_data,
            "revoked_at": session.revoked_at.isoformat(),
            "revoked_by": "user",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Session {session_id} revoked by user {user.email}")
        return MessageResponse(message="Session revoked successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error revoking session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.put('/sessions/revoke-all', response_model=MessageResponse)
async def revoke_all_sessions(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    except_current: bool = True
):
    """Revoke all user sessions"""
    try:
        # Get current session if we want to keep it
        current_session_id = None
        if except_current:
            # This would need additional logic to identify current session
            # For now, we'll just revoke all sessions
            pass
        
        # Get all active sessions
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user.user_id,
                UserSession.revoked_at.is_(None)
            )
        )

        if except_current and current_session_id:
            stmt = stmt.where(UserSession.id != current_session_id)
        
        result = await db.execute(stmt)
        sessions_to_revoke = result.scalars().all()
        session_count = len(sessions_to_revoke)
        
        # Store session data before revoking
        revoked_sessions_data = [
            {
                "id": str(session.id),
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "created_at": session.created_at.isoformat()
            }
            for session in sessions_to_revoke
        ]
        
        # Revoke all sessions
        revoked_at = datetime.utcnow()
        for session in sessions_to_revoke:
            session.revoked_at = revoked_at

        await db.commit()
        
        # Publish bulk session revocation event
        await event_publisher.publish_user_event("sessions_bulk_revoked", {
            "user_id": str(user.user_id),
            "email": user.email,
            "revoked_sessions_count": session_count,
            "revoked_sessions": revoked_sessions_data,
            "except_current": except_current,
            "revoked_at": revoked_at.isoformat(),
            "revoked_by": "user",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"User {user.email} revoked {session_count} sessions")
        return MessageResponse(message=f"Revoked {session_count} sessions successfully")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error revoking all sessions for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.delete('/sessions/cleanup', response_model=MessageResponse)
async def cleanup_expired_sessions(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Clean up expired sessions"""
    try:
        # Get expired sessions
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user.user_id,
                UserSession.expires_at <= datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        expired_sessions = result.scalars().all()
        expired_count = len(expired_sessions)
        
        # Store data about expired sessions
        expired_sessions_data = [
            {
                "id": str(session.id),
                "device_info": session.device_info,
                "created_at": session.created_at.isoformat(),
                "expired_at": session.expires_at.isoformat()
            }
            for session in expired_sessions
        ]
        
        # Delete expired sessions
        await db.execute(
            delete(UserSession).where(
                and_(
                    UserSession.user_id == user.user_id,
                    UserSession.expires_at <= datetime.utcnow()
                )
            )
        )
        
        await db.commit()
        
        # Publish session cleanup event
        await event_publisher.publish_user_event("sessions_cleaned_up", {
            "user_id": str(user.user_id),
            "email": user.email,
            "cleaned_sessions_count": expired_count,
            "cleaned_sessions": expired_sessions_data,
            "cleaned_at": datetime.utcnow().isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Cleaned up {expired_count} expired sessions for user {user.email}")
        return MessageResponse(message=f"Cleaned up {expired_count} expired sessions")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error cleaning up sessions for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )