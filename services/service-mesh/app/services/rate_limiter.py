"""
Rate Limiter service for Service Mesh
"""
import time
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
from loguru import logger


class RateLimiter:
    """
    Rate Limiter implementation.
    
    This class provides methods for implementing rate limiting.
    """
    
    def __init__(self, name: str, requests: int = 100, window: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            name: Rate limiter name
            requests: Number of requests allowed in the window
            window: Time window in seconds
        """
        self.name = name
        self.requests = requests
        self.window = window
        self.request_timestamps = deque()
        
        logger.info(f"Rate limiter '{name}' initialized with requests={requests}, window={window}")
    
    def allow_request(self) -> bool:
        """
        Check if a request is allowed.
        
        Returns:
            bool: True if the request is allowed, False otherwise
        """
        current_time = time.time()
        
        # Remove expired timestamps from the left side of deque (more efficient)
        while self.request_timestamps and current_time - self.request_timestamps[0] >= self.window:
            self.request_timestamps.popleft()
        
        # Check if the number of requests is below the limit
        if len(self.request_timestamps) < self.requests:
            self.request_timestamps.append(current_time)
            return True
        
        return False
    
    def get_remaining(self) -> int:
        """
        Get the number of remaining requests.
        
        Returns:
            int: Number of remaining requests
        """
        current_time = time.time()
        
        # Remove expired timestamps from the left side of deque (more efficient)
        while self.request_timestamps and current_time - self.request_timestamps[0] >= self.window:
            self.request_timestamps.popleft()
        
        return max(0, self.requests - len(self.request_timestamps))
    
    def get_reset_time(self) -> float:
        """
        Get the time until the rate limit resets.
        
        Returns:
            float: Time in seconds until the rate limit resets
        """
        if not self.request_timestamps:
            return 0
        
        current_time = time.time()
        oldest_timestamp = min(self.request_timestamps)
        
        return max(0, self.window - (current_time - oldest_timestamp))
    
    def reset(self):
        """Reset the rate limiter."""
        logger.info(f"Rate limiter '{self.name}' reset")
        self.request_timestamps.clear()


class RateLimiterRegistry:
    """
    Registry for rate limiters.
    
    This class provides methods for managing rate limiters.
    """
    
    def __init__(self):
        """Initialize the rate limiter registry."""
        self.rate_limiters = {}
        logger.info("Rate limiter registry initialized")
    
    def get_rate_limiter(self, name: str, requests: int = 100, window: int = 60) -> RateLimiter:
        """
        Get a rate limiter by name.
        
        Args:
            name: Rate limiter name
            requests: Number of requests allowed in the window
            window: Time window in seconds
            
        Returns:
            RateLimiter: Rate limiter instance
        """
        if name not in self.rate_limiters:
            self.rate_limiters[name] = RateLimiter(name, requests, window)
        return self.rate_limiters[name]
    
    def reset_all(self):
        """Reset all rate limiters."""
        for rate_limiter in self.rate_limiters.values():
            rate_limiter.reset()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of all rate limiters.
        
        Returns:
            Dict[str, Any]: Status of all rate limiters
        """
        status = {}
        for name, rate_limiter in self.rate_limiters.items():
            status[name] = {
                "requests": rate_limiter.requests,
                "window": rate_limiter.window,
                "remaining": rate_limiter.get_remaining(),
                "reset": rate_limiter.get_reset_time()
            }
        return status