"""
Rate limiting middleware for the API Gateway.
"""
import time
import logging
import re
from typing import Callable, Dict, Optional
import asyncio
from redis.asyncio import Redis
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from ..core.config import settings

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.middleware.rate_limiting")

class RateLimiter:
    """
    Rate limiting implementation using Redis as a backend.
    """
    def __init__(self):
        self.redis_pool = None
        self.initialized = False
        self.local_cache: Dict[str, Dict] = {}
        self.last_cleanup = time.time()
        self.max_cache_size = 10000  # Maximum number of items in the local cache
        self._cache_lock = asyncio.Lock()  # Lock to prevent race conditions
    
    async def init_redis(self):
        """Initialize Redis connection pool."""
        if not self.initialized:
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            if settings.REDIS_PASSWORD:
                redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            
            try:
                # Close existing connection if any
                if self.redis_pool:
                    try:
                        await self.redis_pool.close()
                    except Exception:
                        pass
                
                # Create new connection
                self.redis_pool = Redis.from_url(
                    redis_url, 
                    encoding="utf-8", 
                    decode_responses=True,
                    socket_timeout=5.0,  # Add timeout to prevent hanging
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection
                await self.redis_pool.ping()
                
                self.initialized = True
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Fall back to local memory cache
                self.initialized = False
                self.redis_pool = None
    
    async def _cleanup_local_cache(self):
        """Clean up expired entries in local cache."""
        now = time.time()
        if now - self.last_cleanup > 60:  # Cleanup every minute
            # Use a lock to prevent race conditions during cleanup
            async with self._cache_lock:
                # Check again after acquiring the lock
                if now - self.last_cleanup <= 60:
                    return
                
                # Create a safe copy of keys to avoid modification during iteration
                cache_keys = list(self.local_cache.keys())
                expired_keys = []
                
                for key in cache_keys:
                    # Check if key still exists (might have been removed by another thread)
                    if key in self.local_cache:
                        data = self.local_cache[key]
                        if data["expires"] < now:
                            expired_keys.append(key)
                
                # Remove expired keys
                for key in expired_keys:
                    if key in self.local_cache:  # Check again before deleting
                        del self.local_cache[key]
                
                # If cache is still too large, remove oldest entries
                if len(self.local_cache) > self.max_cache_size:
                    # Get current cache keys again after removing expired entries
                    current_keys = list(self.local_cache.keys())
                    
                    # Create a list of (key, expiration) tuples
                    expiration_times = []
                    for key in current_keys:
                        if key in self.local_cache:  # Check again before accessing
                            expiration_times.append((key, self.local_cache[key]["expires"]))
                    
                    # Sort by expiration time (oldest first)
                    expiration_times.sort(key=lambda x: x[1])
                    
                    # Calculate how many items to remove
                    items_to_remove = len(self.local_cache) - self.max_cache_size
                    
                    # Remove the oldest items
                    for i in range(min(items_to_remove, len(expiration_times))):
                        key_to_remove = expiration_times[i][0]
                        if key_to_remove in self.local_cache:
                            del self.local_cache[key_to_remove]
                    
                    logger.warning(f"Rate limiter cache pruned to {len(self.local_cache)} entries")
                
                self.last_cleanup = now
                logger.debug(f"Rate limiter cache cleanup completed. {len(self.local_cache)} entries remaining.")
    
    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """
        Check if a request should be rate limited.
        
        Args:
            key: The rate limiting key (usually IP or user ID)
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        # Validate inputs
        if not key:
            logger.error("Empty rate limit key provided")
            return False  # Default to not rate limiting on error
            
        # Sanitize key to prevent injection attacks
        # Only allow alphanumeric characters, hyphens, underscores, colons, and dots
        if not isinstance(key, str) or not re.match(r'^[a-zA-Z0-9_\-:.]+$', key):
            logger.warning(f"Invalid rate limit key format: {key}")
            # Convert to string if not already and sanitize
            key = str(key)
            key = re.sub(r'[^a-zA-Z0-9_\-:.]', '', key)
            if not key:
                key = "invalid_key"
                
        # Validate limit and window
        if limit <= 0 or window <= 0:
            logger.error(f"Invalid rate limit parameters: limit={limit}, window={window}")
            return False  # Default to not rate limiting on error
            
        await self._cleanup_local_cache()
        
        # Try Redis first if available
        if self.initialized and self.redis_pool:
            try:
                current_time = int(time.time())
                key_name = f"rate_limit:{key}"
                
                # Check if Redis is still connected
                try:
                    # Use a short timeout for the ping
                    await asyncio.wait_for(self.redis_pool.ping(), timeout=1.0)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Redis ping failed, reinitializing connection: {str(e)}")
                    await self.init_redis()
                    # If reinitialization failed, fall back to local cache
                    if not self.initialized or not self.redis_pool:
                        raise Exception("Redis reinitialization failed")
                
                # Use Redis sorted set to track requests
                pipeline = self.redis_pool.pipeline()
                pipeline.zadd(key_name, {current_time: current_time})
                pipeline.zremrangebyscore(key_name, 0, current_time - window)
                pipeline.zcard(key_name)
                pipeline.expire(key_name, window)
                
                # Execute with timeout to prevent hanging
                results = await asyncio.wait_for(pipeline.execute(), timeout=2.0)
                
                request_count = results[2]
                # Check if we've exceeded the limit
                return request_count > limit
            except asyncio.TimeoutError:
                logger.error("Redis operation timed out, falling back to local cache")
                # Fall back to local cache
            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}")
                # Fall back to local cache
        
        # Use local memory cache as fallback
        now = time.time()
        
        # Use a lock to prevent race conditions
        async with self._cache_lock:
            if key not in self.local_cache:
                # First request for this key
                self.local_cache[key] = {
                    "count": 1,
                    "expires": now + window,
                    "window": window
                }
                # First request is never rate limited
                return False
            
            data = self.local_cache[key]
            if data["expires"] < now:
                # Window expired, reset counter
                data["count"] = 1
                data["expires"] = now + window
                return False
            
            # Check if we've exceeded the limit before incrementing
            is_limited = data["count"] >= limit
            
            # Increment count even if limited (to track abuse)
            data["count"] += 1
            
            return is_limited

    async def close(self):
        """Close Redis connection and clean up resources."""
        if self.redis_pool:
            try:
                await self.redis_pool.close()
                logger.info("Rate limiter Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
        
        # Always clean up resources, even if closing Redis failed
        self.redis_pool = None
        self.initialized = False
        
        # Clear the local cache
        try:
            async with self._cache_lock:
                self.local_cache.clear()
                logger.debug("Rate limiter local cache cleared")
        except Exception as e:
            logger.error(f"Error clearing rate limiter cache: {str(e)}")

rate_limiter = RateLimiter()

async def rate_limiting_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to apply rate limiting to requests.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The response from the next handler or a 429 if rate limited
    """
    # Initialize Redis connection if not already done
    if not rate_limiter.initialized:
        await rate_limiter.init_redis()
    
    # Get client IP or user ID for rate limiting
    client_ip = "unknown"
    if request.client:
        client_ip = request.client.host
        
        # Validate IP address format
        # Simple regex for IPv4 and IPv6
        if not re.match(r'^[0-9a-fA-F.:]+$', client_ip):
            logger.warning(f"Invalid client IP format: {client_ip}")
            client_ip = "invalid_ip"
    
    user_id = None
    
    # If authenticated, use user ID instead of IP
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.id
        
        # Validate user ID format
        if user_id is not None:
            user_id_str = str(user_id)
            if not re.match(r'^[a-zA-Z0-9_\-]+$', user_id_str):
                logger.warning(f"Invalid user ID format: {user_id}")
                user_id = "invalid_user"
    
    # Create rate limit key
    rate_limit_key = f"user:{user_id}" if user_id else f"ip:{client_ip}"
    
    # Apply different limits based on path or user role
    path = request.url.path
    
    # Sanitize path to prevent injection attacks
    if not re.match(r'^[a-zA-Z0-9_\-/]+$', path):
        logger.warning(f"Invalid path format for rate limiting: {path}")
        # Use a sanitized version of the path
        path = re.sub(r'[^a-zA-Z0-9_\-/]', '', path)
        if not path:
            path = "/"
    
    # Default limits
    limit = 100  # requests
    window = 60  # seconds
    
    # Adjust limits for specific endpoints
    if path.startswith("/api/v1/auth"):
        limit = 20
        window = 60
    elif path.startswith("/api/v1/admin"):
        limit = 50
        window = 60
    
    # Special case for health check endpoints - higher limits
    if path.startswith("/health") or path.endswith("/health"):
        limit = 500
        window = 60
    
    # Check if rate limited
    try:
        is_limited = await rate_limiter.is_rate_limited(rate_limit_key, limit, window)
        
        if is_limited:
            # Add retry-after header to help clients
            retry_after = window
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(retry_after)}
            )
    except Exception as e:
        # Log the error but don't block the request on rate limiting errors
        logger.error(f"Rate limiting error: {str(e)}")
        # Continue processing the request
    
    # Process the request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise  # Re-raise the exception to be handled by global exception handlers
    
    # Add rate limit headers to response
    try:
        # Get current rate limit status
        current_count = 0
        reset_time = int(time.time() + window)
        
        if rate_limiter.initialized and rate_limiter.redis_pool:
            # Try to get rate limit info from Redis
            key_name = f"rate_limit:{rate_limit_key}"
            try:
                # Use a single pipeline to reduce network round trips
                pipeline = rate_limiter.redis_pool.pipeline()
                pipeline.zcard(key_name)
                pipeline.ttl(key_name)
                
                # Execute with timeout to prevent hanging
                results = await asyncio.wait_for(pipeline.execute(), timeout=2.0)
                
                # Extract results
                current_count = results[0]
                ttl = results[1]
                
                if ttl > 0:
                    reset_time = int(time.time() + ttl)
            except asyncio.TimeoutError:
                logger.warning("Redis operation timed out when getting rate limit info")
            except Exception as e:
                logger.error(f"Error getting rate limit info from Redis: {str(e)}")
        else:
            # Fallback to local cache
            async with rate_limiter._cache_lock:
                if rate_limit_key in rate_limiter.local_cache:
                    data = rate_limiter.local_cache[rate_limit_key]
                    current_count = data.get("count", 0)
                    reset_time = int(data.get("expires", reset_time))
        
        # Validate values before adding headers
        if limit <= 0:
            limit = 100  # Default fallback
        
        if current_count < 0:
            current_count = 0
            
        remaining = max(0, limit - current_count)
        
        # Add headers with validated values
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        # Add retry-after header if close to limit (80% or more)
        if remaining <= (limit * 0.2):
            response.headers["Retry-After"] = str(window)
        
    except Exception as e:
        logger.error(f"Error adding rate limit headers: {str(e)}")
        # Fallback to basic headers if there was an error
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Window"] = str(window)
    
    return response