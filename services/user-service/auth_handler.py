from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Annotated
from uuid import UUID

from config import settings

# This dependency is responsible for extracting the token from the header
security_scheme = HTTPBearer()
SECRET_KEY = "b2b1b1925b5b4e0afccbce63ea4c447c"

# A simple Pydantic model for the authenticated user
class TokenData(BaseModel):
    email: str
    user_id: UUID
    role: str

async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials ,Depends(security_scheme)]) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        user_email: str = payload.get("sub")
        user_id_str: str = payload.get("id")
        user_role: str = payload.get("role")

        print(f"User ID: {user_id_str}, Role: {user_role}")
        
        if user_id_str is None or user_role is None:
            raise credentials_exception
        
        user_id = UUID(user_id_str)
        token_data = TokenData(email=user_email, user_id=user_id, role=user_role)
        
    except (ValueError, JWTError):
        raise credentials_exception
        
    return token_data