"""
Router service for Service Mesh
"""
import random
from typing import Dict, Any, Optional, List
from loguru import logger
from app.models.mesh import Route, RouteDestination, ServiceInstance
from app.services.service_discovery import ServiceDiscoveryClient

class Router:
    """
    Router implementation.

    This class provides methods for routing requests to services.
    """

    def __init__(self, service_discovery_client: ServiceDiscoveryClient):
        """
        Initialize the router.

        Args:
            service_discovery_client: Service Discovery client
        """
        self.service_discovery_client = service_discovery_client
        self.routes = {}

        logger.info("Router initialized")

    def add_route(self, route: Route):
        """
        Add a route.

        Args:
            route: Route to add
        """
        self.routes[route.name] = route
        logger.info(f"Added route '{route.name}'")

    def add_routes(self, routes: List[Route]):
        """
        Add multiple routes.

        Args:
            routes: Routes to add
        """
        for route in routes:
            self.add_route(route)

    def get_route(self, route_name: str) -> Optional[Route]:
        """
        Get a route by name.

        Args:
            route_name: Route name

        Returns:
            Optional[Route]: Route if found, None otherwise
        """
        return self.routes.get(route_name)

    async def match_route(self, path: str, method: str, headers: Dict[str, str]) -> Optional[Route]:
        """
        Match a request to a route.

        Args:
            path: Request path
            method: HTTP method
            headers: Request headers

        Returns:
            Optional[Route]: Matching route if found, None otherwise
        """
        logger.debug(f"Attempting to match route for {method} {path}")
        
        for route in self.routes.values():
            logger.debug(f"Checking route '{route.name}' for {method} {path}")
            
            # Check path match
            if route.match.path:
                # Handle exact path match or path prefix match
                if route.match.path.endswith('$'):
                    # Exact match ($ at the end indicates exact match)
                    exact_path = route.match.path[:-1]  # Remove the $ character
                    if path != exact_path:
                        logger.debug(f"Exact path mismatch: {path} does not match {exact_path}")
                        continue
                elif not path.startswith(route.match.path):
                    # Prefix match
                    logger.debug(f"Path prefix mismatch: {path} does not start with {route.match.path}")
                    continue

            # Check method match
            if route.match.method and method.upper() != route.match.method.upper():
                logger.debug(f"Method mismatch: {method} does not match {route.match.method}")
                continue

            # Check headers match
            if route.match.headers:
                headers_match = True
                for header_name, header_value in route.match.headers.items():
                    if header_name.lower() not in headers or headers[header_name.lower()] != header_value:
                        logger.debug(f"Header mismatch: {header_name}={header_value} not found in request headers")
                        headers_match = False
                        break
                if not headers_match:
                    continue

            # Route matches
            logger.debug(f"Route '{route.name}' matches {method} {path}")
            return route

        logger.debug(f"No matching route found for {method} {path}")
        return None

    async def select_destination(self, route: Route) -> Optional[ServiceInstance]:   
        """
        Select a destination for a route.

        Args:
            route: Route

        Returns:
            Optional[ServiceInstance]: Selected service instance if found, None otherwise
        """
        if not route.destinations:
            logger.warning(f"Route '{route.name}' has no destinations")
            return None

        # Weighted random selection
        total_weight = sum(dest.weight for dest in route.destinations)
        if total_weight <= 0:
            logger.warning(f"Route '{route.name}' has no valid destinations")        
            return None

        # Select a destination based on weight
        random_value = random.randint(1, total_weight)
        current_weight = 0
        selected_destination = None

        for dest in route.destinations:
            current_weight += dest.weight
            if random_value <= current_weight:
                selected_destination = dest
                break

        if not selected_destination:
            logger.warning(f"Failed to select destination for route '{route.name}'") 
            return None

        # Get service instance from service discovery
        service_instance = await self.service_discovery_client.get_service_by_name(selected_destination.service_name)
        if not service_instance:
            logger.warning(f"Service '{selected_destination.service_name}' not found")
            return None

        return service_instance

    async def route_request(self, path: str, method: str, headers: Dict[str, str]) -> Optional[ServiceInstance]:
        """
        Route a request to a service.

        Args:
            path: Request path
            method: HTTP method
            headers: Request headers

        Returns:
            Optional[ServiceInstance]: Selected service instance if found, None otherwise
        """
        # Match route
        route = await self.match_route(path, method, headers)
        if not route:
            logger.warning(f"No route found for {method} {path}")
            return None
        
        # Select destination
        service_instance = await self.select_destination(route)
        if not service_instance:
            logger.warning(f"No destination found for route '{route.name}'")
            return None

        logger.info(f"Routing {method} {path} to {service_instance.name} ({service_instance.host}:{service_instance.port})")
        return service_instance