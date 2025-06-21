"""
Service Discovery client for Service Mesh
"""
import requests
import time
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.config import settings
from app.models.mesh import ServiceInstance, ServiceStatus, ServiceProtocol


class ServiceDiscoveryClient:
    """
    Client for interacting with the Service Discovery service.
    
    This class provides methods for retrieving service information from the
    Service Discovery service.
    """
    
    def __init__(self):
        """Initialize the Service Discovery client."""
        self.discovery_host = settings.SERVICE_DISCOVERY_HOST
        self.discovery_port = settings.SERVICE_DISCOVERY_PORT
        self.discovery_url = f"http://{self.discovery_host}:{self.discovery_port}"
        self.cache = {}
        self.cache_ttl = 10  # Cache TTL in seconds
        self.last_cache_update = 0
        
        logger.info(f"Service Discovery client initialized with URL: {self.discovery_url}")
    
    async def get_all_services(self) -> List[ServiceInstance]:
        """
        Get all registered services.
        
        Returns:
            List[ServiceInstance]: List of service instances
        """
        # Check if cache is valid
        current_time = time.time()
        if current_time - self.last_cache_update < self.cache_ttl and self.cache.get("all_services"):
            return self.cache["all_services"]
        
        try:
            response = requests.get(
                f"{self.discovery_url}/api/v1/services",
                timeout=5
            )
            
            if response.status_code == 200:
                services_data = response.json()
                services = []
                
                for service_data in services_data:
                    # Convert to ServiceInstance model
                    service = ServiceInstance(
                        id=service_data["id"],
                        name=service_data["name"],
                        host=service_data["host"],
                        port=service_data["port"],
                        status=ServiceStatus.HEALTHY if service_data.get("status") == "healthy" else ServiceStatus.UNKNOWN,
                        protocol=ServiceProtocol.HTTP,  # Default to HTTP
                        metadata=service_data.get("metadata", {})
                    )
                    services.append(service)
                
                # Update cache
                self.cache["all_services"] = services
                self.last_cache_update = current_time
                
                logger.debug(f"Retrieved {len(services)} services from Service Discovery")
                return services
            else:
                logger.error(f"Failed to retrieve services: {response.text}")
                # Return cached data if available
                return self.cache.get("all_services", [])
        except Exception as e:
            logger.error(f"Error retrieving services: {str(e)}")
            # Return cached data if available
            return self.cache.get("all_services", [])
    
    async def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """
        Get a specific service by ID.
        
        Args:
            service_id: Service ID
            
        Returns:
            Optional[ServiceInstance]: Service instance if found, None otherwise
        """
        # Check if cache is valid
        cache_key = f"service_{service_id}"
        current_time = time.time()
        if current_time - self.last_cache_update < self.cache_ttl and self.cache.get(cache_key):
            return self.cache[cache_key]
        
        try:
            response = requests.get(
                f"{self.discovery_url}/api/v1/services/{service_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                service_data = response.json()
                
                # Convert to ServiceInstance model
                service = ServiceInstance(
                    id=service_data["id"],
                    name=service_data["name"],
                    host=service_data["host"],
                    port=service_data["port"],
                    status=ServiceStatus.HEALTHY if service_data.get("status") == "healthy" else ServiceStatus.UNKNOWN,
                    protocol=ServiceProtocol.HTTP,  # Default to HTTP
                    metadata=service_data.get("metadata", {})
                )
                
                # Update cache
                self.cache[cache_key] = service
                self.last_cache_update = current_time
                
                logger.debug(f"Retrieved service {service_id} from Service Discovery")
                return service
            else:
                logger.error(f"Failed to retrieve service {service_id}: {response.text}")
                # Return cached data if available
                return self.cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving service {service_id}: {str(e)}")
            # Return cached data if available
            return self.cache.get(cache_key)
    
    async def get_service_by_name(self, service_name: str) -> Optional[ServiceInstance]:
        """
        Get a specific service by name.
        
        Args:
            service_name: Service name
            
        Returns:
            Optional[ServiceInstance]: Service instance if found, None otherwise
        """
        # Check if cache is valid
        cache_key = f"service_name_{service_name}"
        current_time = time.time()
        if current_time - self.last_cache_update < self.cache_ttl and self.cache.get(cache_key):
            return self.cache[cache_key]
        
        try:
            services = await self.get_all_services()
            for service in services:
                if service.name == service_name:
                    # Update cache
                    self.cache[cache_key] = service
                    self.last_cache_update = current_time
                    return service
            
            logger.warning(f"Service {service_name} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving service {service_name}: {str(e)}")
            # Return cached data if available
            return self.cache.get(cache_key)