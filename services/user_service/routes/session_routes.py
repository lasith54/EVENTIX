from datetime import timedelta, datetime
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from starlette import status
from models import UserSession
from schemas import MessageResponse, UserSessionResponse
from database import get_async_db
from auth_handler import get_current_user, TokenData
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

async_db_dependency = Annotated[AsyncSession, Depends(get_async_db)]

@router.get('/', response_model=List[UserSessionResponse])
async def get_user_sessions(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    active_only: bool = True
):
    """Get user's active sessions"""
    query = select(UserSession).where(UserSession.user_id == user.user_id)
    
    if active_only:
        query = query.where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
    
    result = await db.execute(query.order_by(UserSession.last_accessed.desc()))
    sessions = result.scalars().all()
    
    return sessions


@router.delete('/{session_id}', response_model=MessageResponse)
async def terminate_session(
    session_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Terminate a specific user session"""
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
    
    session.is_active = False
    await db.commit()
    
    return MessageResponse(message="Session terminated successfully")


@router.delete('/all', response_model=MessageResponse)
async def terminate_all_sessions(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    exclude_current: bool = True
):
    """Terminate all user sessions"""
    if exclude_current:
        # This would require passing current session token - simplified for now
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.user_id)
            .values(is_active=False)
        )
    else:
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.user_id)
            .values(is_active=False)
        )
    
    await db.commit()
    return MessageResponse(message="All sessions terminated successfully")