import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from starlette import status
from models import User, UserProfile
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from schemas import UserRegister, UserLogin, UserResponse, Token, TokenRefresh, AccessToken, MessageResponse, UserProfileResponse, UserProfileUpdate, PasswordUpdate
from database import get_async_db
from auth_handler import get_current_user, TokenData
import logging

from shared.event_publisher import EventPublisher

logger = logging.getLogger(__name__)

event_publisher = EventPublisher("user-service")

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

async_db_dependency = Annotated[AsyncSession, Depends(get_async_db)]

SECRET_KEY = 'b2b1b1925b5b4e0afccbce63ea4c447c'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", ""),
        "device_info": request.headers.get("x-device-info", "Unknown Device")
    }

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def create_user(db: async_db_dependency, 
                      create_user_request: UserRegister):
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == create_user_request.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Create new user
        create_user_model = User(
            email=create_user_request.email,
            first_name=create_user_request.first_name,
            last_name=create_user_request.last_name,
            hashed_password=bcrypt_context.hash(create_user_request.password),
            phone_number=create_user_request.phone_number,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=None,
        )

        db.add(create_user_model)
        await db.flush()

        # Create user profile
        user_profile = UserProfile(user_id=create_user_model.id)
        db.add(user_profile)
        await db.commit()

        await event_publisher.publish_user_event("created", {
            "user_id": str(create_user_model.id),
            "email": create_user_model.email,
            "first_name": create_user_model.first_name,
            "last_name": create_user_model.last_name
        })

        logger.info(f"New User Registered: {create_user_model.email}")
        return MessageResponse(message="User Registered Successfully.")
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post('/login', response_model=Token)
async def login_user(db: async_db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    try:
        stmt = select(User).where(User.email == form_data.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not bcrypt_context.verify(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for email: {form_data.username}")
            await event_publisher.publish_user_event("login_failed", {
                "email": form_data.username,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "invalid_credentials"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            await event_publisher.publish_user_event("login_failed", {
                "user_id": str(user.id),
                "email": user.email,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "account_deactivated"
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            username=user.email,
            user_id=user.id,
            role = user.role,
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(user.id)

        user.last_login = datetime.utcnow()
        await db.commit()

        # Publish successful login event
        await event_publisher.publish_user_event("login_successful", {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "last_login": user.last_login.isoformat(),
            "session_info": {
                "access_token_expires": access_token_expires.total_seconds()
            }
        })
        
        logger.info(f"User logged in successfully: {user.email}")
        return Token(access_token=access_token, refresh_token=refresh_token, expires_in=access_token_expires.total_seconds())
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post('/refresh', response_model=AccessToken)
async def refresh_token(db: async_db_dependency, token_data: TokenRefresh):
    try:
        # Decode refresh token
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            await event_publisher.publish_user_event("token_refresh_failed", {
                "reason": "invalid_token",
                "timestamp": datetime.utcnow().isoformat()
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Find user
        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            await event_publisher.publish_user_event("token_refresh_failed", {
                "user_id": user_id,
                "reason": "user_not_found_or_inactive",
                "timestamp": datetime.utcnow().isoformat()
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            username=user.email,
            user_id=user.id,
            role=user.role,
            expires_delta=access_token_expires
        )

        await event_publisher.publish_user_event("token_refreshed", {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "new_token_expires": access_token_expires.total_seconds(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return AccessToken(
            access_token=access_token,
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': str(user_id), 'role': role, 'type': 'access'}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int):
    refresh_token = jwt.encode(
        {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=1), "iat": datetime.utcnow(), "type": "refresh"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return refresh_token

@router.post('/logout', response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def logout_user(user: Annotated[TokenData, Depends(get_current_user)]):
    try:
        await event_publisher.publish_user_event("logout", {
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role,
            "logout_timestamp": datetime.utcnow().isoformat()
        }) 

        logger.info(f"User logged out: {user.email}")
        return MessageResponse(message="Successfully logged out")
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@router.get('/me', response_model=UserResponse, dependencies=[Depends(get_current_user)])
async def get_current_user_info(user: Annotated[TokenData, Depends(get_current_user)], db: async_db_dependency):
    stmt = select(User).where(User.id == user.user_id)
    result = await db.execute(stmt)
    current_user = result.scalar_one_or_none()
    return current_user

@router.get('/profile', response_model=UserProfileResponse, dependencies=[Depends(get_current_user)])
async def get_user_profile(user: Annotated[TokenData, Depends(get_current_user)], db: async_db_dependency):
    stmt = select(UserProfile).where(UserProfile.user_id == user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile

@router.put('/profile', response_model=UserProfileResponse, dependencies=[Depends(get_current_user)])
async def update_user_profile(
    user: Annotated[TokenData, Depends(get_current_user)],
    db: async_db_dependency,
    profile_data: UserProfileUpdate 
):
    stmt = select(UserProfile).where(UserProfile.user_id == user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Store old values for comparison
    old_profile_data = {
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "preferences": profile.preferences
    }
    
    for key, value in profile_data.dict().items():
        setattr(profile, key, value)
    
    profile.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(profile)
    
    await event_publisher.publish_user_event("profile_updated", {
        "user_id": str(user.user_id),
        "email": user.email,
        "updated_fields": list(profile_data.dict(exclude_unset=True).keys()),
        "old_data": old_profile_data,
        "new_data": {
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "preferences": profile.preferences
        },
        "timestamp": datetime.utcnow().isoformat()
    })
        
    logger.info(f"Profile updated for user: {user.email}")
    return profile

@router.put('change-password', response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def change_password(
                          user: Annotated[TokenData, Depends(get_current_user)],
                          db: async_db_dependency,
                          password_data: PasswordUpdate 
                          ):
    stmt = select(User).where(User.id == user.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not bcrypt_context.verify(password_data.current_password, user.hashed_password):
        await event_publisher.publish_user_event("password_change_failed", {
            "user_id": str(user.user_id),
            "email": user.email,
            "reason": "invalid_current_password",
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    user.hashed_password = bcrypt_context.hash(password_data.new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()

    await event_publisher.publish_user_event("password_changed", {
        "user_id": str(user.id),
        "email": user.email,
        "timestamp": datetime.utcnow().isoformat(),
        "security_note": "User should be notified via email"
    })
    
    logger.info(f"Password changed successfully for user: {user.email}")
    return MessageResponse(message="Password changed successfully")