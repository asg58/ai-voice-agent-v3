"""
Authentication router for Dashboard Service
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.config import settings
from app.models.auth import Token, LoginRequest
from app.models.user import User
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    fake_users_db
)
from loguru import logger

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token.
    
    Args:
        form_data: OAuth2 password request form
        
    Returns:
        Token: Access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    logger.info(f"User {user.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """
    Login endpoint.
    
    Args:
        login_request: Login request
        
    Returns:
        Token: Access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(fake_users_db, login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    logger.info(f"User {user.username} logged in")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user.
    
    Args:
        current_user: Current user
        
    Returns:
        User: Current user
    """
    return current_user