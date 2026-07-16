"""
Authentication API endpoints for user login and signup.
"""

import logging
import re
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator

from app.db.session import get_db
from app.models.db_models import User
from app.utils.auth_utils import encrypt_password, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    """Signup request model."""
    email: str
    username: str
    password: str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class AuthResponse(BaseModel):
    """Authentication response model."""
    status: str
    message: str
    user_id: str = None
    username: str = None


@router.post("/signup", response_model=AuthResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up a new user.
    
    Args:
        request: Signup request with email, username, password
        db: Database session
        
    Returns:
        Authentication response
    """
    try:
        # Check if user already exists
        query = select(User).where(
            (User.email == request.email) | (User.username == request.username)
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Create new user with encrypted password
        encrypted_pwd = encrypt_password(request.password)
        new_user = User(
            email=request.email,
            username=request.username,
            encrypted_password=encrypted_pwd,
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user signed up: {request.username} ({request.email})")
        
        return AuthResponse(
            status="success",
            message="User registered successfully",
            user_id=str(new_user.id),
            username=new_user.username
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login a user.
    
    Args:
        request: Login request with username and password
        db: Database session
        
    Returns:
        Authentication response
    """
    try:
        # Find user by username
        query = select(User).where(User.username == request.username)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Verify password
        if not verify_password(request.password, user.encrypted_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        logger.info(f"User logged in: {user.username}")
        
        return AuthResponse(
            status="success",
            message="Login successful",
            user_id=str(user.id),
            username=user.username
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/verify/{user_id}")
async def verify_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify if a user exists.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        User existence confirmation
    """
    try:
        query = select(User).where(User.id == UUID(user_id))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "status": "success",
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )
