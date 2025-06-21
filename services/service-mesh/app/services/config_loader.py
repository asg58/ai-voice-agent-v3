"""
Configuration loader for Service Mesh
"""
import yaml
import os
import json
from typing import Dict, Any, Optional
from loguru import logger
from app.core.config import settings
from app.models.mesh import MeshConfig, ServiceConfig, Route, RouteMatch, RouteDestination
from app.models.mesh import CircuitBreakerSettings, RateLimitSettings


class ConfigLoader:
    """
    Configuration loader for Service Mesh.
    
    This class provides methods for loading and validating mesh configuration.
    """
    
    def __init__(self):
        """Initialize the configuration loader."""
        self.config_file = settings.CONFIG_FILE
        self.config = None
        self.last_modified = 0
        
        logger.info(f"Configuration loader initialized with file: {self.config_file}")
    
    def load_config(self) -> Optional[MeshConfig]:
        """
        Load the mesh configuration from file.
        
        Returns:
            Optional[MeshConfig]: Mesh configuration if loaded successfully, None otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(self.config_file):
                logger.error(f"Configuration file not found: {self.config_file}")
                return None
            
            # Check if file has been modified
            current_modified = os.path.getmtime(self.config_file)
            if self.config and current_modified <= self.last_modified:
                return self.config
            
            # Load configuration from file
            with open(self.config_file, 'r') as file:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    config_data = yaml.safe_load(file)
                elif self.config_file.endswith('.json'):
                    config_data = json.load(file)
                else:
                    logger.error(f"Unsupported configuration file format: {self.config_file}")
                    return None
            
            # Parse configuration
            mesh_config = self._parse_config(config_data)
            if not mesh_config:
                return None
            
            # Validate configuration
            if not self.validate_config(mesh_config):
                logger.error("Invalid mesh configuration")
                return None
            
            # Update last modified time
            self.last_modified = current_modified
            self.config = mesh_config
            
            logger.info(f"Loaded mesh configuration with {len(mesh_config.services)} services")
            return mesh_config
        except Exception as e:
            logger.error(f"Error loading mesh configuration: {str(e)}")
            return None
            
    def validate_config(self, config: MeshConfig) -> bool:
        """
        Validate the mesh configuration.
        
        Args:
            config: Mesh configuration
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Check if there are any services
            if not config.services:
                logger.warning("No services defined in configuration")
                return False
            
            # Check if service names are unique
            service_names = [service.name for service in config.services]
            if len(service_names) != len(set(service_names)):
                logger.error("Duplicate service names in configuration")
                return False
            
            # Check if routes are valid
            for service in config.services:
                route_names = [route.name for route in service.routes]
                if len(route_names) != len(set(route_names)):
                    logger.error(f"Duplicate route names in service '{service.name}'")
                    return False
                
                for route in service.routes:
                    if not route.destinations:
                        logger.warning(f"Route '{route.name}' in service '{service.name}' has no destinations")
                    
                    # Check if destination service names exist
                    for destination in route.destinations:
                        if destination.service_name not in service_names:
                            logger.warning(f"Route '{route.name}' in service '{service.name}' references unknown service '{destination.service_name}'")
                
                # Check circuit breaker settings
                if service.circuit_breaker.threshold <= 0:
                    logger.warning(f"Service '{service.name}' has invalid circuit breaker threshold: {service.circuit_breaker.threshold}")
                
                # Check rate limit settings
                if service.rate_limit.requests <= 0:
                    logger.warning(f"Service '{service.name}' has invalid rate limit requests: {service.rate_limit.requests}")
                if service.rate_limit.window <= 0:
                    logger.warning(f"Service '{service.name}' has invalid rate limit window: {service.rate_limit.window}")
            
            return True
        except Exception as e:
            logger.error(f"Error validating configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: Dict[str, Any]) -> Optional[MeshConfig]:
        """
        Parse configuration data into MeshConfig model.
        
        Args:
            config_data: Configuration data
            
        Returns:
            Optional[MeshConfig]: Mesh configuration if parsed successfully, None otherwise
        """
        try:
            # Check if configuration is in the expected format
            if not isinstance(config_data, dict):
                logger.error("Configuration data is not a dictionary")
                return None
            
            # Parse services
            services = []
            for service_data in config_data.get('services', []):
                service = self._parse_service(service_data)
                if service:
                    services.append(service)
            
            # Create mesh configuration
            mesh_config = MeshConfig(services=services)
            
            return mesh_config
        except Exception as e:
            logger.error(f"Error parsing mesh configuration: {str(e)}")
            return None
    
    def _parse_service(self, service_data: Dict[str, Any]) -> Optional[ServiceConfig]:
        """
        Parse service data into ServiceConfig model.
        
        Args:
            service_data: Service data
            
        Returns:
            Optional[ServiceConfig]: Service configuration if parsed successfully, None otherwise
        """
        try:
            # Check if service data is in the expected format
            if not isinstance(service_data, dict) or 'name' not in service_data:
                logger.error("Service data is not valid")
                return None
            
            # Parse circuit breaker settings
            circuit_breaker_data = service_data.get('circuit_breaker', {})
            circuit_breaker = CircuitBreakerSettings(
                enabled=circuit_breaker_data.get('enabled', settings.CIRCUIT_BREAKER_ENABLED),
                threshold=circuit_breaker_data.get('threshold', settings.CIRCUIT_BREAKER_THRESHOLD),
                timeout=circuit_breaker_data.get('timeout', settings.CIRCUIT_BREAKER_TIMEOUT)
            )
            
            # Parse rate limit settings
            rate_limit_data = service_data.get('rate_limit', {})
            rate_limit = RateLimitSettings(
                enabled=rate_limit_data.get('enabled', settings.RATE_LIMIT_ENABLED),
                requests=rate_limit_data.get('requests', settings.RATE_LIMIT_REQUESTS),
                window=rate_limit_data.get('window', settings.RATE_LIMIT_WINDOW)
            )
            
            # Parse routes
            routes = []
            for route_data in service_data.get('routes', []):
                route = self._parse_route(route_data)
                if route:
                    routes.append(route)
            
            # Create service configuration
            service_config = ServiceConfig(
                name=service_data['name'],
                circuit_breaker=circuit_breaker,
                rate_limit=rate_limit,
                routes=routes
            )
            
            # Set service reference for each route
            for route in service_config.routes:
                route.service = service_config
            
            return service_config
        except Exception as e:
            logger.error(f"Error parsing service configuration: {str(e)}")
            return None
    
    def _parse_route(self, route_data: Dict[str, Any]) -> Optional[Route]:
        """
        Parse route data into Route model.
        
        Args:
            route_data: Route data
            
        Returns:
            Optional[Route]: Route if parsed successfully, None otherwise
        """
        try:
            # Check if route data is in the expected format
            if not isinstance(route_data, dict) or 'name' not in route_data:
                logger.error("Route data is not valid")
                return None
            
            # Parse match criteria
            match_data = route_data.get('match', {})
            match = RouteMatch(
                path=match_data.get('path'),
                method=match_data.get('method'),
                headers=match_data.get('headers', {})
            )
            
            # Parse destinations
            destinations = []
            for dest_data in route_data.get('destinations', []):
                if not isinstance(dest_data, dict) or 'service_name' not in dest_data:
                    logger.error("Destination data is not valid")
                    continue
                
                destination = RouteDestination(
                    service_name=dest_data['service_name'],
                    weight=dest_data.get('weight', 100)
                )
                destinations.append(destination)
            
            # Create route
            route = Route(
                name=route_data['name'],
                match=match,
                destinations=destinations
            )
            
            return route
        except Exception as e:
            logger.error(f"Error parsing route configuration: {str(e)}")
            return None