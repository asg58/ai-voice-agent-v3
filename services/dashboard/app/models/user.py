"""
User models for Dashboard Service
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """User role enum"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """
    Base user model.
    
    Attributes:
        email: User email
        username: Username
        full_name: User's full name
        disabled: Whether the user is disabled
    """
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = False


class UserCreate(UserBase):
    """
    User creation model.
    
    Attributes:
        password: User password
        role: User role
    """
    password: str
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """
    User update model.
    
    Attributes:
        email: User email
        username: Username
        full_name: User's full name
        disabled: Whether the user is disabled
        role: User role
    """
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: Optional[UserRole] = None


class User(UserBase):
    """
    User model.
    
    Attributes:
        id: User ID
        role: User role
        created_at: User creation timestamp
        updated_at: User update timestamp
    """
    id: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config class"""
        orm_mode = True


class UserInDB(User):
    """
    User model with hashed password.
    
    Attributes:
        hashed_password: Hashed user password
    """
    hashed_password: str