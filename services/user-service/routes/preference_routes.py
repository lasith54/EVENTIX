import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import timedelta, datetime
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette import status
from models import UserPreferences, UserProfile
from schemas import UserPreferencesResponse, UserPreferencesUpdate, MessageResponse
from database import get_async_db
from auth_handler import get_current_user, TokenData
from shared.event_publisher import EventPublisher
import logging
import json

logger = logging.getLogger(__name__)

event_publisher = EventPublisher("user-service")

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
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    preferences = json.loads(profile.preferences) if profile.preferences else {}
    
    # Publish preferences access event
    await event_publisher.publish_user_event("preferences_accessed", {
        "user_id": str(user.user_id),
        "email": user.email,
        "preferences_count": len(preferences),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return UserPreferencesResponse(
        user_id=str(profile.user_id),
        preferences=preferences,
        updated_at=profile.updated_at
    )


@router.put('/preferences', response_model=UserPreferencesResponse)
async def update_user_preferences(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    preferences_update: UserPreferencesUpdate
):
    stmt = select(UserPreferences).where(UserPreferences.user_id == user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
    # Get old preferences for comparison
    old_preferences = json.loads(profile.preferences) if profile.preferences else {}
    
    # Update preferences
    new_preferences = preferences_update.preferences
    profile.preferences = json.dumps(new_preferences)
    profile.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Analyze what changed
    added_keys = set(new_preferences.keys()) - set(old_preferences.keys())
    removed_keys = set(old_preferences.keys()) - set(new_preferences.keys())
    modified_keys = {
        key for key in set(new_preferences.keys()) & set(old_preferences.keys())
        if new_preferences[key] != old_preferences[key]
    }
    
    # Publish preferences update event
    await event_publisher.publish_user_event("preferences_updated", {
        "user_id": str(user.user_id),
        "email": user.email,
        "old_preferences": old_preferences,
        "new_preferences": new_preferences,
        "changes": {
            "added": list(added_keys),
            "removed": list(removed_keys),
            "modified": list(modified_keys)
        },
        "total_preferences": len(new_preferences),
        "updated_at": profile.updated_at.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info(f"Preferences updated for user {user.email}")
    return MessageResponse(message="Preferences updated successfully")

@router.put('/preferences/{preference_key}', response_model=MessageResponse)
async def update_single_preference(
    preference_key: str,
    preference_value: Any,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Update a single preference key"""
    try:
        stmt = select(UserProfile).where(UserProfile.user_id == user.user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        current_preferences = json.loads(profile.preferences) if profile.preferences else {}
        old_value = current_preferences.get(preference_key)
        
        # Update the specific preference
        current_preferences[preference_key] = preference_value
        profile.preferences = json.dumps(current_preferences)
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Publish single preference update event
        await event_publisher.publish_user_event("single_preference_updated", {
            "user_id": str(user.user_id),
            "email": user.email,
            "preference_key": preference_key,
            "old_value": old_value,
            "new_value": preference_value,
            "was_new_key": old_value is None,
            "updated_at": profile.updated_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"Single preference '{preference_key}' updated for user {user.email}")
        return MessageResponse(message=f"Preference '{preference_key}' updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating single preference for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.delete('/preferences/{preference_key}', response_model=MessageResponse)
async def delete_preference(
    preference_key: str,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Delete a specific preference"""
    try:
        stmt = select(UserProfile).where(UserProfile.user_id == user.user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Get current preferences
        current_preferences = json.loads(profile.preferences) if profile.preferences else {}
        
        if preference_key not in current_preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preference '{preference_key}' not found"
            )
        
        # Store old value before deletion
        deleted_value = current_preferences.pop(preference_key)
        
        # Update preferences
        profile.preferences = json.dumps(current_preferences)
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Publish preference deletion event
        await event_publisher.publish_user_event("preference_deleted", {
            "user_id": str(user.user_id),
            "email": user.email,
            "deleted_preference_key": preference_key,
            "deleted_value": deleted_value,
            "remaining_preferences_count": len(current_preferences),
            "updated_at": profile.updated_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Preference '{preference_key}' deleted for user {user.email}")
        return MessageResponse(message=f"Preference '{preference_key}' deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting preference for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.delete('/preferences', response_model=MessageResponse)
async def clear_all_preferences(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency
):
    """Clear all user preferences"""
    try:
        stmt = select(UserProfile).where(UserProfile.user_id == user.user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Store old preferences before clearing
        old_preferences = json.loads(profile.preferences) if profile.preferences else {}
        preferences_count = len(old_preferences)

        # Clear preferences
        profile.preferences = json.dumps({})
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Publish preferences clear event
        await event_publisher.publish_user_event("preferences_cleared", {
            "user_id": str(user.user_id),
            "email": user.email,
            "cleared_preferences": old_preferences,
            "preferences_count_cleared": preferences_count,
            "cleared_at": profile.updated_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"All preferences cleared for user {user.email}")
        return MessageResponse(message="All preferences cleared successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error clearing preferences for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )