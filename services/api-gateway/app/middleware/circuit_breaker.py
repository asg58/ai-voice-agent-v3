"""
Circuit breaker middleware for the API Gateway.
"""
import time
import asyncio
import re
from enum import Enum
from typing import Dict, Callable, Optional
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from ..core.config import settings

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.middleware.circuit_breaker")

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation, requests flow through
    OPEN = "OPEN"      # Circuit is open, requests are rejected
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back online

class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    """
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        self.half_open_successes = 0
        
        # Add a lock to prevent race conditions
        self._state_lock = asyncio.Lock()
    
    async def record_success(self):
        """Record a successful call."""
        async with self._state_lock:
            if self.state == CircuitState.CLOSED:
                # Reset failure count in closed state
                self.failure_count = 0
            elif self.state == CircuitState.HALF_OPEN:
                # In half-open state, track successful calls
                self.half_open_successes += 1
                
                # If we've had enough successful calls, close the circuit
                if self.half_open_successes >= self.half_open_max_calls:
                    logger.info(f"Circuit {self.name} closing after successful test calls")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.half_open_calls = 0
                    self.half_open_successes = 0
    
    async def record_failure(self):
        """Record a failed call."""
        async with self._state_lock:
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                # In closed state, increment failure count
                self.failure_count += 1
                
                # If we've reached the threshold, open the circuit
                if self.failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit {self.name} opening after {self.failure_count} failures")
                    self.state = CircuitState.OPEN
            
            elif self.state == CircuitState.HALF_OPEN:
                # In half-open state, any failure reopens the circuit
                logger.warning(f"Circuit {self.name} reopening after test call failure")
                
                # Reset counters before changing state to avoid race conditions
                self.half_open_successes = 0
                self.half_open_calls = 0  # Reset all calls counter to avoid stuck counters
                
                # Change state to OPEN
                self.state = CircuitState.OPEN
    
    async def allow_request(self) -> bool:
        """
        Check if a request should be allowed through the circuit.
        
        Returns:
            bool: True if the request should be allowed, False otherwise
        """
        async with self._state_lock:
            current_time = time.time()
            
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if current_time - self.last_failure_time >= self.recovery_timeout:
                    logger.info(f"Circuit {self.name} entering half-open state for testing")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.half_open_successes = 0
                else:
                    # Still in open state and timeout not elapsed
                    return False
            
            if self.state == CircuitState.HALF_OPEN:
                # In half-open state, only allow a limited number of test calls
                # We need to check if we've already reached the maximum number of concurrent test calls
                if self.half_open_calls >= self.half_open_max_calls:
                    return False
                
                # Increment the counter for half-open calls
                self.half_open_calls += 1
                logger.debug(f"Circuit {self.name} allowing test call {self.half_open_calls}/{self.half_open_max_calls}")
            
            # Allow the request in CLOSED state or for test calls in HALF_OPEN state
            return True

# Global circuit breakers for services
circuit_breakers: Dict[str, CircuitBreaker] = {}
max_circuit_breakers = 100  # Maximum number of circuit breakers to keep

# Lock for circuit breakers dictionary
circuit_breakers_lock = asyncio.Lock()

# Define a global variable to track if cleanup is already in progress
_cleanup_in_progress = False

async def cleanup_circuit_breakers():
    """Clean up circuit breakers dictionary if it gets too large."""
    global circuit_breakers
    
    async with circuit_breakers_lock:
        current_size = len(circuit_breakers)
        if current_size <= max_circuit_breakers:
            # No cleanup needed
            return
            
        # Keep only the most recently used circuit breakers
        # This is a simple implementation - in a real system, you might
        # want to use a more sophisticated algorithm
        logger.warning(f"Circuit breakers dictionary exceeds max size ({current_size} > {max_circuit_breakers})")
        
        try:
            # Sort by last failure time (most recent first)
            sorted_breakers = sorted(
                circuit_breakers.items(),
                key=lambda x: x[1].last_failure_time,
                reverse=True
            )
            
            # Create a new dictionary with only the breakers we want to keep
            new_breakers = {}
            for i, (name, breaker) in enumerate(sorted_breakers):
                if i < max_circuit_breakers:
                    new_breakers[name] = breaker
            
            # Replace the old dictionary with the new one
            # This is safer than clearing and repopulating the original dictionary
            circuit_breakers = new_breakers
            
            logger.info(f"Circuit breakers dictionary pruned from {current_size} to {len(circuit_breakers)} entries")
        except Exception as e:
            logger.error(f"Error during circuit breakers cleanup: {str(e)}")
            # Don't modify the dictionary if there was an error

async def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a service.
    
    Args:
        service_name: The name of the service
        
    Returns:
        CircuitBreaker: The circuit breaker for the service
    """
    global _cleanup_in_progress
    
    # Validate service name
    if not service_name:
        logger.error("Empty service name provided to circuit breaker")
        service_name = "unknown_service"
        
    # Sanitize service name to prevent injection attacks
    if not re.match(r'^[a-zA-Z0-9_\-]+$', service_name):
        logger.warning(f"Invalid service name format: {service_name}")
        # Use a sanitized version of the service name
        service_name = re.sub(r'[^a-zA-Z0-9_\-]', '', service_name)
        if not service_name:
            service_name = "invalid_service"
    
    # Use a lock to prevent race conditions
    async with circuit_breakers_lock:
        if service_name not in circuit_breakers:
            circuit_breakers[service_name] = CircuitBreaker(
                name=service_name,
                failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                half_open_max_calls=settings.CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS
                if hasattr(settings, "CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS") else 3
            )
            
            # Check if we need to clean up the circuit breakers dictionary
            if len(circuit_breakers) > max_circuit_breakers and not _cleanup_in_progress:
                # Set flag to prevent multiple cleanup tasks
                _cleanup_in_progress = True
                
                # Schedule cleanup to run in the background
                async def run_cleanup():
                    global _cleanup_in_progress
                    try:
                        await cleanup_circuit_breakers()
                    finally:
                        # Reset flag when done, even if there was an error
                        _cleanup_in_progress = False
                
                asyncio.create_task(run_cleanup())
        
        return circuit_breakers[service_name]

async def circuit_breaker_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to apply circuit breaking to service requests.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The response from the next handler or a 503 if circuit is open
    """
    # Determine target service from path
    path = request.url.path
    
    # Sanitize path to prevent injection attacks
    if not re.match(r'^[a-zA-Z0-9_\-/]+$', path):
        logger.warning(f"Invalid path format for circuit breaker: {path}")
        # Use a sanitized version of the path
        path = re.sub(r'[^a-zA-Z0-9_\-/]', '', path)
        if not path:
            path = "/"
            
    target_service = None
    
    # Check if the path matches any service route
    for service, config in settings.SERVICE_ROUTES.items():
        if path.startswith(config["prefix"]):
            target_service = service
            break
    
    # If no target service found, just pass through
    if not target_service:
        return await call_next(request)
    
    # Get circuit breaker for the service
    circuit = await get_circuit_breaker(target_service)
    
    # Check if request should be allowed
    allow_request = False
    try:
        allow_request = await circuit.allow_request()
    except Exception as e:
        # Log the error but don't block the request on circuit breaker errors
        logger.error(f"Circuit breaker error for {target_service}: {str(e)}")
        # Default to allowing the request if there's an error in the circuit breaker
        allow_request = True
    
    if not allow_request:
        logger.warning(f"Circuit breaker rejecting request to {target_service}: circuit is {circuit.state.value}")
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Service {target_service} is currently unavailable. Please try again later."
            },
            headers={
                "Retry-After": str(circuit.recovery_timeout)
            }
        )
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Record success or failure based on response status
        try:
            if response.status_code < 500:
                await circuit.record_success()
            else:
                # Record failure - the state lock is already handled inside record_failure
                await circuit.record_failure()
        except Exception as e:
            # Log the error but don't affect the response
            logger.error(f"Error recording circuit breaker result for {target_service}: {str(e)}")
            # Ensure we decrement half_open_calls if we're in HALF_OPEN state to prevent stuck counters
            if circuit.state == CircuitState.HALF_OPEN:
                try:
                    async with circuit._state_lock:
                        if circuit.half_open_calls > 0:
                            circuit.half_open_calls -= 1
                except Exception:
                    pass  # Ignore errors in the cleanup attempt
        
        return response
    except Exception as e:
        # Record failure on exception
        try:
            await circuit.record_failure()
        except Exception as record_error:
            # Log the error but don't affect the exception handling
            logger.error(f"Error recording circuit breaker failure for {target_service}: {str(record_error)}")
            # Ensure we decrement half_open_calls if we're in HALF_OPEN state to prevent stuck counters
            if circuit.state == CircuitState.HALF_OPEN:
                try:
                    async with circuit._state_lock:
                        if circuit.half_open_calls > 0:
                            circuit.half_open_calls -= 1
                except Exception:
                    pass  # Ignore errors in the cleanup attempt
        
        logger.error(f"Error in request to {target_service}: {str(e)}")
        raise