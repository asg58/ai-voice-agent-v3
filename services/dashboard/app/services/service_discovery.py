"""
Service Discovery client for Dashboard Service
"""
import requests
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.config import settings
from app.models.dashboard import ServiceStatus
from datetime import datetime


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
        
        logger.info(f"Service Discovery client initialized with URL: {self.discovery_url}")
    
    async def get_all_services(self) -> List[ServiceStatus]:
        """
        Get all registered services.
        
        Returns:
            List[ServiceStatus]: List of service statuses
        """
        try:
            response = requests.get(
                f"{self.discovery_url}/services",
                timeout=5
            )
            
            if response.status_code == 200:
                services_data = response.json()
                services = []
                
                for service_data in services_data:
                    # Convert timestamp string to datetime
                    if "last_heartbeat" in service_data and service_data["last_heartbeat"]:
                        service_data["last_heartbeat"] = datetime.fromisoformat(
                            service_data["last_heartbeat"].replace("Z", "+00:00")
                        )
                    else:
                        service_data["last_heartbeat"] = datetime.now()
                    
                    services.append(ServiceStatus(**service_data))
                
                logger.debug(f"Retrieved {len(services)} services from Service Discovery")
                return services
            else:
                logger.error(f"Failed to retrieve services: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving services: {str(e)}")
            return []
    
    async def get_service(self, service_id: str) -> Optional[ServiceStatus]:
        """
        Get a specific service by ID.
        
        Args:
            service_id: Service ID
            
        Returns:
            Optional[ServiceStatus]: Service status if found, None otherwise
        """
        try:
            response = requests.get(
                f"{self.discovery_url}/services/{service_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                service_data = response.json()
                
                # Convert timestamp string to datetime
                if "last_heartbeat" in service_data and service_data["last_heartbeat"]:
                    service_data["last_heartbeat"] = datetime.fromisoformat(
                        service_data["last_heartbeat"].replace("Z", "+00:00")
                    )
                else:
                    service_data["last_heartbeat"] = datetime.now()
                
                logger.debug(f"Retrieved service {service_id} from Service Discovery")
                return ServiceStatus(**service_data)
            else:
                logger.error(f"Failed to retrieve service {service_id}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving service {service_id}: {str(e)}")
            return None
    
    async def get_service_by_name(self, service_name: str) -> Optional[ServiceStatus]:
        """
        Get a specific service by name.
        
        Args:
            service_name: Service name
            
        Returns:
            Optional[ServiceStatus]: Service status if found, None otherwise
        """
        try:
            services = await self.get_all_services()
            for service in services:
                if service.name == service_name:
                    return service
            
            logger.warning(f"Service {service_name} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving service {service_name}: {str(e)}")
            return None