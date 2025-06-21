"""
Unit tests for API Gateway utilities
"""
import pytest
import json
from datetime import datetime, timedelta
from jose import jwt

# Test JWT token creation and validation
def test_jwt_token_creation():
    """Test creating and validating a JWT token"""
    # Secret key for testing
    secret_key = "test-secret-key"
    algorithm = "HS256"
    
    # Create token data
    user_data = {
        "sub": "testuser",
        "user_id": "user123",
        "is_admin": False,
        "scopes": ["read", "write"]
    }
    
    # Add expiration
    expiration = datetime.utcnow() + timedelta(minutes=15)
    user_data["exp"] = expiration
    
    # Create token
    token = jwt.encode(user_data, secret_key, algorithm=algorithm)
    
    # Validate token
    decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
    
    # Check data
    assert decoded["sub"] == "testuser"
    assert decoded["user_id"] == "user123"
    assert decoded["is_admin"] is False
    assert "read" in decoded["scopes"]
    assert "write" in decoded["scopes"]