"""
Authentication service for Dashboard Service
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.models.user import User, UserInDB, UserRole
from app.models.auth import TokenData
from loguru import logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Mock user database - in a real application, this would be a database
fake_users_db = {
    "admin": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": pwd_context.hash("admin"),
        "disabled": False,
        "role": UserRole.ADMIN,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    "user": {
        "id": "2",
        "username": "user",
        "email": "user@example.com",
        "full_name": "Regular User",
        "hashed_password": pwd_context.hash("user"),
        "disabled": False,
        "role": UserRole.USER,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    "viewer": {
        "id": "3",
        "username": "viewer",
        "email": "viewer@example.com",
        "full_name": "Viewer User",
        "hashed_password": pwd_context.hash("viewer"),
        "disabled": False,
        "role": UserRole.VIEWER,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def get_user(db, username: str) -> Optional[UserInDB]:
    """
    Get a user from the database.
    
    Args:
        db: User database
        username: Username to look up
        
    Returns:
        Optional[UserInDB]: User if found, None otherwise
    """
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(db, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user.
    
    Args:
        db: User database
        username: Username
        password: Password
        
    Returns:
        Optional[User]: User if authentication succeeds, None otherwise
    """
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        User: Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If the user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user