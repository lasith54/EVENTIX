from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import UserPreferences
from schemas import UserPreferencesResponse, UserPreferencesUpdate
from database import get_async_db
from auth_handler import get_current_user, TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/preference',
    tags=['Preferences']
)

async_db_dependency = Annotated[AsyncSession, Depends(get_async_db)]

@router.get('/preferences', response_model=UserPreferencesResponse)
async def get_user_preferences(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    stmt = select(UserPreferences).where(UserPreferences.user_id == user.user_id)
    result = await db.execute(stmt)
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreferences(user_id=user.user_id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    
    return preferences


@router.put('/preferences', response_model=UserPreferencesResponse)
async def update_user_preferences(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    preferences_data: UserPreferencesUpdate
):
    stmt = select(UserPreferences).where(UserPreferences.user_id == user.user_id)
    result = await db.execute(stmt)
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        preferences = UserPreferences(user_id=user.user_id)
        db.add(preferences)
        await db.flush()
    
    for key, value in preferences_data.dict(exclude_unset=True).items():
        setattr(preferences, key, value)
    
    preferences.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(preferences)
    
    return preferences