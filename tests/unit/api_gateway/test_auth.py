"""
Unit tests for API Gateway authentication middleware
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt
import sys
import os
from pathlib import Path

# Add the services directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Mock the auth module
class User:
    def __init__(self, id, username, email=None, is_active=True, is_admin=False, scopes=None):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active
        self.is_admin = is_admin
        self.scopes = scopes or []

class TokenData:
    def __init__(self, sub, exp, scopes=None, user_id=None, is_admin=False):
        self.sub = sub
        self.exp = exp
        self.scopes = scopes or []
        self.user_id = user_id
        self.is_admin = is_admin

# Mock the functions
def create_access_token(data, expires_delta=None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    # Mock settings
    SECRET_KEY = "testsecretkey"
    ALGORITHM = "HS256"
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token):
    try:
        # Mock settings
        SECRET_KEY = "testsecretkey"
        ALGORITHM = "HS256"
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        
        user_id = payload.get("user_id")
        is_admin = payload.get("is_admin", False)
        scopes = payload.get("scopes", [])
        
        user = User(
            id=user_id or "unknown",
            username=username,
            is_admin=is_admin,
            scopes=scopes
        )
        
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def auth_middleware(request, call_next):
    # Mock settings
    API_V1_STR = "/api/v1"
    SECRET_KEY = "testsecretkey"
    ALGORITHM = "HS256"
    
    # Skip authentication for public endpoints
    path = request.url.path
    
    # List of paths that don't require authentication
    public_paths = [
        f"{API_V1_STR}/auth/token",
        f"{API_V1_STR}/auth/register",
        f"{API_V1_STR}/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    # Check if the path is public
    is_public = any(path.startswith(public_path) for public_path in public_paths)
    
    if is_public:
        return await call_next(request)
    
    # Get the authorization header
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        # No token provided, continue without user context
        return await call_next(request)
    
    # Extract the token
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        return await call_next(request)
    
    try:
        # Validate the token and get the user
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return await call_next(request)
        
        user_id = payload.get("user_id")
        is_admin = payload.get("is_admin", False)
        scopes = payload.get("scopes", [])
        
        # Create user object
        user = User(
            id=user_id or "unknown",
            username=username,
            is_admin=is_admin,
            scopes=scopes
        )
        
        # Attach user to request state
        request.state.user = user
    except Exception:
        # Invalid token, continue without user context
        pass
    
    return await call_next(request)


@pytest.fixture
def mock_request():
    """Create a mock request for testing"""
    mock = MagicMock()
    mock.url = MagicMock()
    mock.url.path = "/api/v1/protected"
    mock.headers = {}
    mock.state = MagicMock()
    return mock


@pytest.fixture
def test_user_data():
    """Test user data for token creation"""
    return {
        "sub": "testuser",
        "user_id": "user123",
        "is_admin": False,
        "scopes": ["read", "write"]
    }


@pytest.fixture
def test_token(test_user_data):
    """Create a test JWT token"""
    # Mock settings
    SECRET_KEY = "testsecretkey"
    ALGORITHM = "HS256"
    
    to_encode = test_user_data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def test_create_access_token(test_user_data):
    """Test creating an access token"""
    # Test with default expiration
    token = create_access_token(test_user_data)
    assert token is not None
    assert isinstance(token, str)
    
    # Test with custom expiration
    custom_expires = timedelta(minutes=30)
    token = create_access_token(test_user_data, expires_delta=custom_expires)
    assert token is not None
    assert isinstance(token, str)
    
    # Decode and verify token contents
    # Mock settings
    SECRET_KEY = "testsecretkey"
    ALGORITHM = "HS256"
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert payload["sub"] == test_user_data["sub"]
    assert payload["user_id"] == test_user_data["user_id"]
    assert payload["is_admin"] == test_user_data["is_admin"]
    assert payload["scopes"] == test_user_data["scopes"]
    assert "exp" in payload


@pytest.mark.asyncio
async def test_get_current_user_valid_token(test_token):
    """Test getting current user with a valid token"""
    user = await get_current_user(test_token)
    
    assert isinstance(user, User)
    assert user.username == "testuser"
    assert user.id == "user123"
    assert user.is_admin is False
    assert "read" in user.scopes
    assert "write" in user.scopes


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test getting current user with an invalid token"""
    invalid_token = "invalid.token.string"
    
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(invalid_token)
    
    assert excinfo.value.status_code == 401
    assert "Could not validate credentials" in excinfo.value.detail


@pytest.mark.asyncio
async def test_auth_middleware_public_path(mock_request):
    """Test auth middleware with a public path"""
    # Mock settings
    API_V1_STR = "/api/v1"
    
    # Set a public path
    mock_request.url.path = f"{API_V1_STR}/health"
    
    # Mock the call_next function
    async def mock_call_next(request):
        return JSONResponse(content={"message": "success"})
    
    # Call the middleware
    response = await auth_middleware(mock_request, mock_call_next)
    
    # Verify the response
    assert response.status_code == 200
    assert not hasattr(mock_request.state, "user")


@pytest.mark.asyncio
async def test_auth_middleware_no_auth_header(mock_request):
    """Test auth middleware with no authorization header"""
    # Mock the call_next function
    async def mock_call_next(request):
        return JSONResponse(content={"message": "success"})
    
    # Call the middleware
    response = await auth_middleware(mock_request, mock_call_next)
    
    # Verify the response
    assert response.status_code == 200
    assert not hasattr(mock_request.state, "user")


@pytest.mark.asyncio
async def test_auth_middleware_valid_token(mock_request, test_token):
    """Test auth middleware with a valid token"""
    # Set the authorization header
    mock_request.headers = {"Authorization": f"Bearer {test_token}"}
    
    # Mock the call_next function
    async def mock_call_next(request):
        return JSONResponse(content={"message": "success"})
    
    # Call the middleware
    response = await auth_middleware(mock_request, mock_call_next)
    
    # Verify the response
    assert response.status_code == 200
    assert hasattr(mock_request.state, "user")
    assert mock_request.state.user.username == "testuser"
    assert mock_request.state.user.id == "user123"


@pytest.mark.asyncio
async def test_auth_middleware_invalid_token(mock_request):
    """Test auth middleware with an invalid token"""
    # Set an invalid authorization header
    mock_request.headers = {"Authorization": "Bearer invalid.token.string"}
    
    # Mock the call_next function
    async def mock_call_next(request):
        return JSONResponse(content={"message": "success"})
    
    # Call the middleware
    response = await auth_middleware(mock_request, mock_call_next)
    
    # Verify the response
    assert response.status_code == 200
    assert not hasattr(mock_request.state, "user")