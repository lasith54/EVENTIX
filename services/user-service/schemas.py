# schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


# User Registration Schema
class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")


# User Login Schema
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


# User Response Schema
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]


# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    refresh_token: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# User Profile Schemas
class UserProfileCreate(BaseModel):
    date_of_birth: Optional[datetime] = None
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    preferences: Optional[str] = None


class UserProfileUpdate(BaseModel):
    date_of_birth: Optional[datetime] = None
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    preferences: Optional[str] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: Optional[datetime]
    bio: Optional[str]
    avatar_url: Optional[str]
    preferences: Optional[str]
    created_at: datetime
    updated_at: datetime


# Password Update Schema
class PasswordUpdate(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")


# User Update Schema
class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


# Error Response Schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# Success Response Schema
class MessageResponse(BaseModel):
    message: str
    status: str = "success"