"""
Circuit Breaker service for Service Mesh
"""
import time
from enum import Enum
from typing import Dict, Any, Optional
from loguru import logger


class CircuitState(str, Enum):
    """Circuit state enum"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit Breaker implementation.
    
    This class provides methods for implementing the circuit breaker pattern.
    """
    
    def __init__(self, name: str, threshold: int = 5, timeout: int = 30):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Circuit breaker name
            threshold: Number of consecutive failures before opening the circuit
            timeout: Time in seconds before trying to close the circuit
        """
        self.name = name
        self.threshold = threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
        logger.info(f"Circuit breaker '{name}' initialized with threshold={threshold}, timeout={timeout}")
    
    def is_closed(self) -> bool:
        """
        Check if the circuit is closed.
        
        Returns:
            bool: True if the circuit is closed, False otherwise
        """
        return self.state == CircuitState.CLOSED
    
    def is_open(self) -> bool:
        """
        Check if the circuit is open.
        
        Returns:
            bool: True if the circuit is open, False otherwise
        """
        return self.state == CircuitState.OPEN
    
    def is_half_open(self) -> bool:
        """
        Check if the circuit is half-open.
        
        Returns:
            bool: True if the circuit is half-open, False otherwise
        """
        return self.state == CircuitState.HALF_OPEN
    
    def allow_request(self) -> bool:
        """
        Check if a request is allowed.
        
        Returns:
            bool: True if the request is allowed, False otherwise
        """
        # If the circuit is closed, allow the request
        if self.state == CircuitState.CLOSED:
            return True
        
        # If the circuit is open, check if the timeout has elapsed
        if self.state == CircuitState.OPEN:
            current_time = time.time()
            if current_time - self.last_failure_time >= self.timeout:
                logger.info(f"Circuit breaker '{self.name}' transitioning from OPEN to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        # If the circuit is half-open, allow one request to test the service
        return True
    
    def record_success(self):
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' transitioning from HALF_OPEN to CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed request."""
        current_time = time.time()
        self.last_failure_time = current_time
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                logger.warning(f"Circuit breaker '{self.name}' transitioning from CLOSED to OPEN")
                self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}' transitioning from HALF_OPEN to OPEN")
            self.state = CircuitState.OPEN
    
    def reset(self):
        """Reset the circuit breaker."""
        logger.info(f"Circuit breaker '{self.name}' reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0


class CircuitBreakerRegistry:
    """
    Registry for circuit breakers.
    
    This class provides methods for managing circuit breakers.
    """
    
    def __init__(self):
        """Initialize the circuit breaker registry."""
        self.circuit_breakers = {}
        logger.info("Circuit breaker registry initialized")
    
    def get_circuit_breaker(self, name: str, threshold: int = 5, timeout: int = 30) -> CircuitBreaker:
        """
        Get a circuit breaker by name.
        
        Args:
            name: Circuit breaker name
            threshold: Number of consecutive failures before opening the circuit
            timeout: Time in seconds before trying to close the circuit
            
        Returns:
            CircuitBreaker: Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, threshold, timeout)
        return self.circuit_breakers[name]
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for circuit_breaker in self.circuit_breakers.values():
            circuit_breaker.reset()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of all circuit breakers.
        
        Returns:
            Dict[str, Any]: Status of all circuit breakers
        """
        status = {}
        for name, circuit_breaker in self.circuit_breakers.items():
            status[name] = {
                "state": circuit_breaker.state,
                "failure_count": circuit_breaker.failure_count,
                "last_failure_time": circuit_breaker.last_failure_time,
                "threshold": circuit_breaker.threshold,
                "timeout": circuit_breaker.timeout
            }
        return status