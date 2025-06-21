"""
Standard health check endpoints
"""
import time
import platform
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

# Create router
router = APIRouter()

class HealthCheck:
    """Health check service"""
    
    def __init__(self, service_name: str, version: str, start_time: datetime = None):
        """
        Initialize health check service
        
        Args:
            service_name: Name of the service
            version: Service version
            start_time: Service start time
        """
        self.service_name = service_name
        self.version = version
        self.start_time = start_time or datetime.now()
        self.components = []
    
    def add_component(self, name: str, check_func: callable, critical: bool = True):
        """
        Add component to health check
        
        Args:
            name: Component name
            check_func: Function to check component health
            critical: Whether component is critical for service operation
        """
        self.components.append({
            "name": name,
            "check_func": check_func,
            "critical": critical
        })
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of all components
        
        Returns:
            Health check result
        """
        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Get system info
        try:
            # Use appropriate root path based on OS
            root_path = "C:\\" if platform.system() == "Windows" else "/"
            disk_usage = psutil.disk_usage(root_path).percent
        except Exception:
            disk_usage = None
        
        # Get CPU usage safely
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu_usage = None
            
        # Get memory usage safely
        try:
            memory_usage = psutil.virtual_memory().percent
        except Exception:
            memory_usage = None
            
        system_info = {
            "os": platform.system(),
            "python_version": platform.python_version(),
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage
        }
        
        # Check components
        components_status = []
        all_healthy = True
        
        for component in self.components:
            try:
                result = await component["check_func"]()
                status = "healthy" if result.get("status", True) else "unhealthy"
                
                if status == "unhealthy" and component["critical"]:
                    all_healthy = False
                
                components_status.append({
                    "name": component["name"],
                    "status": status,
                    "details": result.get("details", {}),
                    "critical": component["critical"]
                })
            except Exception as e:
                if component["critical"]:
                    all_healthy = False
                
                components_status.append({
                    "name": component["name"],
                    "status": "unhealthy",
                    "details": {"error": str(e)},
                    "critical": component["critical"]
                })
        
        # Create response
        return {
            "service": self.service_name,
            "version": self.version,
            "status": "healthy" if all_healthy else "unhealthy",
            "uptime": uptime,
            "timestamp": datetime.now().isoformat(),
            "system": system_info,
            "components": components_status
        }

def create_health_router(
    service_name: str,
    version: str,
    start_time: Optional[datetime] = None,
    components: List[Dict[str, Any]] = None
) -> APIRouter:
    """
    Create health check router
    
    Args:
        service_name: Name of the service
        version: Service version
        start_time: Service start time
        components: List of components to check
        
    Returns:
        Health check router
    """
    # Create health check service
    health_check = HealthCheck(service_name, version, start_time)
    
    # Add components
    if components:
        for component in components:
            health_check.add_component(
                name=component["name"],
                check_func=component["check_func"],
                critical=component.get("critical", True)
            )
    
    # Create router
    router = APIRouter(tags=["Health"])
    
    @router.get("/health", summary="Get service health")
    async def get_health():
        """
        Get service health status
        
        Returns:
            Health check result
        """
        result = await health_check.check_health()
        
        if result["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result
            )
        
        return result
    
    @router.get("/health/live", summary="Liveness probe")
    async def get_liveness():
        """
        Liveness probe for Kubernetes
        
        Returns:
            Simple health status
        """
        return {"status": "alive"}
    
    @router.get("/health/ready", summary="Readiness probe")
    async def get_readiness():
        """
        Readiness probe for Kubernetes
        
        Returns:
            Health check result
        """
        result = await health_check.check_health()
        
        if result["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "not ready"}
            )
        
        return {"status": "ready"}
    
    return router