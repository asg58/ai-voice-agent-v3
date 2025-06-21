"""
Service discovery client for the API Gateway.
"""
import asyncio
import logging
import time
import re
import sys
from typing import Dict, Any, List, Optional
import httpx
from httpx import TimeoutException, ConnectError
from ..core.config import settings

# Handle different asyncio timeout implementations based on Python version
if sys.version_info >= (3, 11):
    from asyncio import timeout
else:
    # For Python 3.10 and earlier
    from asyncio import wait_for

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.services.service_discovery")

class ServiceDiscoveryClient:
    """
    Client for interacting with the service discovery service.
    """
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.SERVICE_DISCOVERY_URL
        self.services_cache: Dict[str, Dict[str, Any]] = {}
        self.last_refresh = time.time() - 3600  # Force refresh on first use
        self.refresh_interval = 60  # seconds
        self.max_cache_size = 100  # Maximum number of services to cache
        
        # Create HTTP client with appropriate timeouts and limits
        self.client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True
        )
        
        self.initialized = True  # Flag to track if the client is initialized
        self._refresh_lock = asyncio.Lock()  # Lock to prevent concurrent refreshes
        self._client_lock = asyncio.Lock()  # Lock for client operations
    
    async def refresh_services(self) -> bool:
        """
        Refresh the services cache from the service discovery service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Use a lock to prevent concurrent refreshes
        async with self._refresh_lock:
            # Ensure client is initialized
            if not await self._ensure_client():
                logger.error("Cannot refresh services: client not initialized")
                return False
                
            try:
                # Use a timeout for the request based on Python version
                if sys.version_info >= (3, 11):
                    async with timeout(5.0):
                        response = await self.client.get(f"{self.base_url}/services")
                        response.raise_for_status()
                        
                        services_data = response.json()
                else:
                    # For Python 3.10 and earlier
                    response = await wait_for(
                        self.client.get(f"{self.base_url}/services"),
                        timeout=5.0
                    )
                    response.raise_for_status()
                    
                    services_data = response.json()
                
                # Update cache with validation
                new_cache = {}
                for service in services_data:
                    # Validate required fields
                    service_id = service.get("id")
                    if not service_id:
                        logger.warning("Skipping service with missing ID")
                        continue
                        
                    # Validate host and port
                    host = service.get("host")
                    port = service.get("port")
                    if not host or not port:
                        logger.warning(f"Skipping service {service_id} with missing host or port")
                        continue
                        
                    # Validate health check endpoint
                    health_check = service.get("health_check")
                    if not health_check:
                        logger.warning(f"Service {service_id} has no health check endpoint, using default")
                        service["health_check"] = "/health"
                    
                    # Add to cache
                    new_cache[service_id] = service
                
                # Check if we need to limit the cache size
                if len(new_cache) > self.max_cache_size:
                    logger.warning(f"Service cache exceeds max size ({len(new_cache)} > {self.max_cache_size})")
                    
                    # Prioritize essential services (if any)
                    essential_services = ["api-gateway", "auth", "service-discovery"]
                    truncated_cache = {}
                    
                    # First add essential services
                    for service_id in essential_services:
                        if service_id in new_cache:
                            truncated_cache[service_id] = new_cache[service_id]
                    
                    # Then add remaining services up to the limit
                    remaining_slots = self.max_cache_size - len(truncated_cache)
                    if remaining_slots > 0:
                        # Create a list of non-essential services
                        other_services = [(sid, sdata) for sid, sdata in new_cache.items() 
                                         if sid not in essential_services]
                        
                        # Add remaining services up to the limit
                        for i in range(min(remaining_slots, len(other_services))):
                            service_id, service_data = other_services[i]
                            truncated_cache[service_id] = service_data
                    
                    # Safely update the cache
                    self.services_cache = truncated_cache
                    logger.info(f"Truncated service cache to {len(self.services_cache)} services")
                else:
                    # Safely update the cache
                    self.services_cache = new_cache
                
                logger.info(f"Refreshed services from discovery: {len(self.services_cache)} services found")
                return True
            except asyncio.TimeoutError:
                logger.error("Timeout while refreshing services from discovery")
                return False
            except Exception as e:
                logger.error(f"Failed to refresh services from discovery: {str(e)}")
                return False
    
    async def _cleanup_stale_services(self) -> None:
        """
        Clean up stale services from the cache.
        
        A service is considered stale if it hasn't been seen in a while or
        if it fails a health check.
        """
        async with self._refresh_lock:
            # Create a copy of the keys to avoid modification during iteration
            service_ids = list(self.services_cache.keys())
            
            for service_id in service_ids:
                # Skip essential services
                if service_id in ["api-gateway", "auth", "service-discovery"]:
                    continue
                
                # Check if the service is healthy
                try:
                    is_healthy = await self.check_health(service_id)
                    if not is_healthy and service_id in self.services_cache:
                        logger.warning(f"Removing unhealthy service from cache: {service_id}")
                        del self.services_cache[service_id]
                except Exception as e:
                    logger.error(f"Error checking health of service {service_id}: {str(e)}")
                    # Don't remove the service on error, wait for next cleanup
    
    async def _ensure_cache_fresh(self) -> bool:
        """
        Ensure the service cache is fresh.
        
        Returns:
            bool: True if cache is fresh, False if refresh failed
        """
        current_time = time.time()
        needs_refresh = current_time - self.last_refresh > self.refresh_interval
        
        if needs_refresh:
            # Use a lock to prevent multiple concurrent refreshes
            async with self._refresh_lock:
                # Check again after acquiring the lock in case another task already refreshed
                current_time = time.time()  # Get current time again after acquiring lock
                if current_time - self.last_refresh > self.refresh_interval:
                    success = await self.refresh_services()
                    current_time = time.time()  # Update time after refresh
                    
                    if success:
                        self.last_refresh = current_time
                        
                        # Periodically clean up stale services (every 5 refreshes)
                        if int(self.last_refresh / self.refresh_interval) % 5 == 0:
                            asyncio.create_task(self._cleanup_stale_services())
                            
                        return True
                    else:
                        # If refresh failed, only retry after a shorter interval
                        self.last_refresh = current_time - (self.refresh_interval * 0.8)
                        return False
        return True
    
    async def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Get service details by ID.
        
        Args:
            service_id: The ID of the service
            
        Returns:
            Optional[Dict[str, Any]]: The service details or None if not found
        """
        # Validate service ID
        if not service_id:
            logger.error("Cannot get service without ID")
            return None
            
        # Sanitize service ID to prevent injection attacks
        # Only allow alphanumeric characters, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', service_id):
            logger.error(f"Invalid service ID format: {service_id}")
            return None
            
        # Ensure cache is fresh
        await self._ensure_cache_fresh()
        
        # Return service from cache
        return self.services_cache.get(service_id)
    
    async def get_all_services(self) -> List[Dict[str, Any]]:
        """
        Get all registered services.
        
        Returns:
            List[Dict[str, Any]]: List of all services
        """
        # Ensure cache is fresh
        await self._ensure_cache_fresh()
        
        # Return all services from cache
        return list(self.services_cache.values())
    
    async def register_service(self, service_data: Dict[str, Any]) -> bool:
        """
        Register a new service with the discovery service.
        
        Args:
            service_data: The service data to register
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate service data before registering
        service_id = service_data.get("id")
        if not service_id:
            logger.error("Cannot register service without ID")
            return False
            
        host = service_data.get("host")
        port = service_data.get("port")
        if not host or not port:
            logger.error(f"Cannot register service {service_id} without host or port")
            return False
            
        # Ensure health check endpoint is present
        if "health_check" not in service_data:
            logger.warning(f"Service {service_id} has no health check endpoint, using default")
            service_data["health_check"] = "/health"
        
        # Ensure client is initialized
        if not await self._ensure_client():
            logger.error(f"Cannot register service {service_id}: client not initialized")
            return False
            
        try:
            # Use a timeout for the request based on Python version
            if sys.version_info >= (3, 11):
                async with timeout(5.0):
                    response = await self.client.post(
                        f"{self.base_url}/services",
                        json=service_data
                    )
                    response.raise_for_status()
            else:
                # For Python 3.10 and earlier
                response = await wait_for(
                    self.client.post(
                        f"{self.base_url}/services",
                        json=service_data
                    ),
                    timeout=5.0
                )
                response.raise_for_status()
            
            # Refresh cache after registration
            await self.refresh_services()
            
            logger.info(f"Registered service: {service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service: {str(e)}")
            return False
    
    async def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service from the discovery service.
        
        Args:
            service_id: The ID of the service to deregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate service ID
        if not service_id:
            logger.error("Cannot deregister service without ID")
            return False
            
        # Sanitize service ID to prevent injection attacks
        # Only allow alphanumeric characters, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', service_id):
            logger.error(f"Invalid service ID format: {service_id}")
            return False
        
        # Ensure client is initialized
        if not await self._ensure_client():
            logger.error(f"Cannot deregister service {service_id}: client not initialized")
            return False
            
        try:
            # Use a timeout for the request based on Python version
            if sys.version_info >= (3, 11):
                async with timeout(5.0):
                    response = await self.client.delete(f"{self.base_url}/services/{service_id}")
                    response.raise_for_status()
            else:
                # For Python 3.10 and earlier
                response = await wait_for(
                    self.client.delete(f"{self.base_url}/services/{service_id}"),
                    timeout=5.0
                )
                response.raise_for_status()
            
            # Remove from cache
            if service_id in self.services_cache:
                del self.services_cache[service_id]
            
            logger.info(f"Deregistered service: {service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service: {str(e)}")
            return False
    
    async def check_health(self, service_id: str) -> bool:
        """
        Check the health of a service.
        
        Args:
            service_id: The ID of the service to check
            
        Returns:
            bool: True if healthy, False otherwise
        """
        # Validate service ID
        if not service_id:
            logger.error("Cannot check health of service without ID")
            return False
            
        # Sanitize service ID to prevent injection attacks
        # Only allow alphanumeric characters, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', service_id):
            logger.error(f"Invalid service ID format: {service_id}")
            return False
        
        # Ensure client is initialized
        if not await self._ensure_client():
            logger.error(f"Cannot check health of service {service_id}: client not initialized")
            return False
            
        service = await self.get_service(service_id)
        if not service:
            logger.warning(f"Service {service_id} not found in service registry")
            return False
        
        try:
            host = service.get("host", "")
            if not host:
                logger.warning(f"Service {service_id} has no host defined")
                return False
                
            port = service.get("port", 80)
            health_check = service.get("health_check", "/health")
            
            # Validate health check path
            if not health_check.startswith("/"):
                health_check = f"/{health_check}"
                
            # Sanitize health check path to prevent injection attacks
            # Only allow alphanumeric characters, hyphens, underscores, and forward slashes
            if not re.match(r'^[a-zA-Z0-9_\-/]+$', health_check):
                logger.warning(f"Invalid health check path format for service {service_id}: {health_check}")
                health_check = "/health"  # Use default if invalid
                
            url = f"http://{host}:{port}{health_check}"
            logger.debug(f"Checking health of service {service_id} at {url}")
            
            # Use a timeout for the health check request based on Python version
            if sys.version_info >= (3, 11):
                async with timeout(5.0):
                    response = await self.client.get(url, follow_redirects=True)
            else:
                # For Python 3.10 and earlier
                response = await wait_for(
                    self.client.get(url, follow_redirects=True),
                    timeout=5.0
                )
                
                # Check if the response indicates the service is healthy
                # A service is considered healthy if:
                # 1. Status code is 200 OK
                # 2. OR status code is 2xx and response contains {"status": "healthy"} or similar
                
                # First check status code
                is_healthy = 200 <= response.status_code < 300
                
                # If status code is not 2xx, service is definitely not healthy
                if not is_healthy:
                    logger.warning(f"Health check for service {service_id} returned status code {response.status_code}")
                    try:
                        response_data = response.json()
                        if isinstance(response_data, dict) and "detail" in response_data:
                            logger.warning(f"Service {service_id} health check details: {response_data['detail']}")
                    except Exception:
                        # If we can't parse the response, just log the status code
                        pass
                    return False
                
                # If status code is 2xx, check response content for additional health info
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        # Check for status field
                        status = response_data.get("status", "").lower()
                        if status in ["unhealthy", "down", "critical", "error"]:
                            logger.warning(f"Service {service_id} reports unhealthy status: {status}")
                            return False
                        
                        # Check for detailed health info
                        if "components" in response_data and isinstance(response_data["components"], list):
                            unhealthy_components = [
                                c for c in response_data["components"] 
                                if isinstance(c, dict) and c.get("status", "").lower() != "healthy"
                                and c.get("critical", False)  # Only consider critical components
                            ]
                            if unhealthy_components:
                                logger.warning(f"Service {service_id} reports unhealthy critical components: {len(unhealthy_components)}")
                                return False
                except Exception:
                    # If we can't parse the response, assume it's healthy based on status code
                    pass
                
                return is_healthy
                
        except asyncio.TimeoutError:
            logger.error(f"Health check timed out for service {service_id}")
            return False
        except httpx.ConnectError:
            logger.error(f"Connection error during health check for service {service_id}")
            return False
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during health check for service {service_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Health check failed for service {service_id}: {str(e)}")
            return False
    
    async def _ensure_client(self) -> bool:
        """
        Ensure the HTTP client is initialized.
        
        Returns:
            bool: True if client is initialized, False otherwise
        """
        async with self._client_lock:
            if not self.client:
                try:
                    # Use a timeout for client initialization based on Python version
                    if sys.version_info >= (3, 11):
                        async with timeout(5.0):
                            # Recreate the client
                            self.client = httpx.AsyncClient(
                                timeout=10.0,
                                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                                follow_redirects=True
                            )
                    else:
                        # For Python 3.10 and earlier
                        # Create client without timeout first
                        client_creation = httpx.AsyncClient(
                            timeout=10.0,
                            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                            follow_redirects=True
                        )
                        # Then apply timeout to the whole operation
                        self.client = await wait_for(asyncio.sleep(0, result=client_creation), timeout=5.0)
                    
                    self.initialized = True
                    logger.info("Service discovery client reinitialized")
                    return True
                except asyncio.TimeoutError:
                    logger.error("Timeout while initializing service discovery client")
                    self.initialized = False
                    return False
                except Exception as e:
                    logger.error(f"Failed to reinitialize service discovery client: {str(e)}")
                    self.initialized = False
                    return False
            
            # Check if the client is still valid by testing a simple operation
            try:
                # Use a short timeout for the ping based on Python version
                if sys.version_info >= (3, 11):
                    async with timeout(2.0):
                        # Try to make a simple request to check if the client is still valid
                        # This is a no-op that just checks if the client can be used
                        self.client._transport
                else:
                    # For Python 3.10 and earlier
                    # Create a simple async function to check the transport
                    async def check_transport():
                        return self.client._transport
                    
                    await wait_for(check_transport(), timeout=2.0)
                
                return True
            except Exception as e:
                logger.warning(f"Service discovery client appears to be invalid, will reinitialize: {str(e)}")
                try:
                    # Close the existing client if possible
                    await self.client.aclose()
                except Exception:
                    pass
                
                # Set to None so it will be reinitialized on next call
                self.client = None
                self.initialized = False
                return False
    
    async def close(self):
        """Close the HTTP client."""
        async with self._client_lock:
            if self.client:
                try:
                    await self.client.aclose()
                except Exception as e:
                    logger.error(f"Error closing service discovery client: {str(e)}")
                finally:
                    self.client = None
                    self.initialized = False
                    logger.info("Service discovery client closed")

# Create global service discovery client
service_discovery = ServiceDiscoveryClient()