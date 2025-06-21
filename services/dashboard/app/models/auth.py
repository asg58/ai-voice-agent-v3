"""
Authentication models for Dashboard Service
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """
    Token model.
    
    Attributes:
        access_token: JWT access token
        token_type: Token type
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Token data model.
    
    Attributes:
        username: Username from token
        role: User role from token
    """
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """
    Login request model.
    
    Attributes:
        username: Username
        password: Password
    """
    username: str
    password: str