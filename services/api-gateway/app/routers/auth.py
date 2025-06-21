"""
Authentication router for the API Gateway.
"""
import logging
from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from ..core.config import settings
from ..middleware.auth import create_access_token

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.routers.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

# Mock user database for demonstration
# In a real implementation, this would be a database
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        "is_active": True,
        "is_admin": True,
        "user_id": "1",
        "scopes": ["admin", "user"]
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        "is_active": True,
        "is_admin": False,
        "user_id": "2",
        "scopes": ["user"]
    }
}

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    username: str
    is_admin: bool

class UserCreate(BaseModel):
    """User creation model."""
    username: str
    email: str
    password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    In a real implementation, this would use a proper password hashing library.
    For demonstration, we're using a simple comparison.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        bool: True if the password is correct, False otherwise
    """
    # This is a mock implementation for demonstration purposes only
    # In a real app, use passlib.hash or similar for secure password verification
    # For example: return pwd_context.verify(plain_password, hashed_password)
    
    # For demo purposes, we're accepting any user with password "password"
    # This should NEVER be used in a production environment
    try:
        # Add a time delay to prevent timing attacks
        import time
        time.sleep(0.1)  # 100ms delay
        
        # In a real implementation, use a secure password comparison
        # from passlib.hash import bcrypt
        # return bcrypt.verify(plain_password, hashed_password)
        
        return plain_password == "password"
    except Exception as e:
        # Log the error but don't expose details
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_user(username: str) -> Dict[str, Any]:
    """
    Get a user from the database.
    
    Args:
        username: The username to look up
        
    Returns:
        Dict[str, Any]: The user data or None if not found
    """
    return USERS_DB.get(username)

def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        Dict[str, Any]: The user data if authentication is successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        form_data: The OAuth2 form data
        
    Returns:
        Token: The access token
        
    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    logger.info(f"Successful login for user: {form_data.username}")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["user_id"],
            "is_admin": user["is_admin"],
            "scopes": user["scopes"]
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": user["user_id"],
        "username": user["username"],
        "is_admin": user["is_admin"]
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    
    In a real implementation, this would add the user to a database.
    For demonstration, we just return a success message.
    
    Args:
        user_data: The user data
        
    Returns:
        Dict[str, Any]: A success message
        
    Raises:
        HTTPException: If the username is already taken
    """
    logger.info(f"Registration attempt for username: {user_data.username}")
    
    if user_data.username in USERS_DB:
        logger.warning(f"Registration failed: username already exists: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # In a real implementation, we would hash the password and store the user
    logger.info(f"User registered successfully: {user_data.username}")
    
    # In a real implementation, hash the password and store the user
    # For demonstration, we just return a success message
    
    return {
        "message": "User registered successfully",
        "username": user_data.username
    }