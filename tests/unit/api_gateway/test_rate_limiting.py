"""
Unit tests for API Gateway rate limiting middleware
"""
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Import the module to test
from services.api_gateway.app.middleware.rate_limiting import RateLimiter, rate_limiting_middleware


@pytest.fixture
def mock_redis_pool():
    """Mock Redis pool for testing"""
    mock = AsyncMock()
    mock.pipeline.return_value = mock
    mock.zadd = AsyncMock()
    mock.zremrangebyscore = AsyncMock()
    mock.zcard = AsyncMock()
    mock.expire = AsyncMock()
    mock.execute = AsyncMock(return_value=[1, 1, 5, 1])  # 5 is the request count
    return mock


@pytest.fixture
def mock_request():
    """Create a mock request for testing"""
    mock = MagicMock()
    mock.client = MagicMock()
    mock.client.host = "127.0.0.1"
    mock.url = MagicMock()
    mock.url.path = "/api/v1/test"
    mock.state = MagicMock()
    mock.state.user = None
    return mock


@pytest.fixture
def mock_response():
    """Create a mock response for testing"""
    mock = MagicMock()
    mock.headers = {}
    return mock


@pytest.mark.asyncio
async def test_rate_limiter_init_redis():
    """Test initializing Redis connection"""
    rate_limiter = RateLimiter()
    
    # Mock aioredis.from_url
    with patch('services.api_gateway.app.middleware.rate_limiting.aioredis.from_url', 
               AsyncMock()) as mock_from_url:
        await rate_limiter.init_redis()
        
        # Verify Redis was initialized
        assert mock_from_url.called
        assert rate_limiter.initialized is True


@pytest.mark.asyncio
async def test_rate_limiter_init_redis_failure():
    """Test Redis initialization failure"""
    rate_limiter = RateLimiter()
    
    # Mock aioredis.from_url to raise an exception
    with patch('services.api_gateway.app.middleware.rate_limiting.aioredis.from_url', 
               AsyncMock(side_effect=Exception("Connection error"))) as mock_from_url:
        await rate_limiter.init_redis()
        
        # Verify Redis was not initialized
        assert mock_from_url.called
        assert rate_limiter.initialized is False


@pytest.mark.asyncio
async def test_is_rate_limited_redis(mock_redis_pool):
    """Test rate limiting using Redis"""
    rate_limiter = RateLimiter()
    rate_limiter.initialized = True
    rate_limiter.redis_pool = mock_redis_pool
    
    # Test under limit
    mock_redis_pool.execute.return_value = [1, 1, 5, 1]  # 5 requests (under limit of 10)
    result = await rate_limiter.is_rate_limited("test_key", 10, 60)
    assert result is False
    
    # Test over limit
    mock_redis_pool.execute.return_value = [1, 1, 15, 1]  # 15 requests (over limit of 10)
    result = await rate_limiter.is_rate_limited("test_key", 10, 60)
    assert result is True


@pytest.mark.asyncio
async def test_is_rate_limited_local_cache():
    """Test rate limiting using local cache"""
    rate_limiter = RateLimiter()
    rate_limiter.initialized = False  # Force local cache usage
    
    # First request (under limit)
    result = await rate_limiter.is_rate_limited("test_key", 2, 60)
    assert result is False
    assert "test_key" in rate_limiter.local_cache
    assert rate_limiter.local_cache["test_key"]["count"] == 1
    
    # Second request (still under limit)
    result = await rate_limiter.is_rate_limited("test_key", 2, 60)
    assert result is False
    assert rate_limiter.local_cache["test_key"]["count"] == 2
    
    # Third request (over limit)
    result = await rate_limiter.is_rate_limited("test_key", 2, 60)
    assert result is True
    assert rate_limiter.local_cache["test_key"]["count"] == 3


@pytest.mark.asyncio
async def test_rate_limiting_middleware_not_limited(mock_request):
    """Test rate limiting middleware when not rate limited"""
    # Mock the call_next function
    async def mock_call_next(request):
        return JSONResponse(content={"message": "success"})
    
    # Mock the rate limiter
    with patch('services.api_gateway.app.middleware.rate_limiting.rate_limiter') as mock_limiter:
        mock_limiter.initialized = True
        mock_limiter.is_rate_limited = AsyncMock(return_value=False)
        
        # Call the middleware
        response = await rate_limiting_middleware(mock_request, mock_call_next)
        
        # Verify the response
        assert response.status_code == 200
        assert "X-Rate-Limit-Limit" in response.headers
        assert "X-Rate-Limit-Window" in response.headers


@pytest.mark.asyncio
async def test_rate_limiting_middleware_limited(mock_request):
    """Test rate limiting middleware when rate limited"""
    # Mock the call_next function
    async def mock_call_next(request):
        return JSONResponse(content={"message": "success"})
    
    # Mock the rate limiter
    with patch('services.api_gateway.app.middleware.rate_limiting.rate_limiter') as mock_limiter:
        mock_limiter.initialized = True
        mock_limiter.is_rate_limited = AsyncMock(return_value=True)
        
        # Call the middleware
        response = await rate_limiting_middleware(mock_request, mock_call_next)
        
        # Verify the response
        assert response.status_code == 429
        assert "detail" in response.json()
        assert "Rate limit exceeded" in response.json()["detail"]