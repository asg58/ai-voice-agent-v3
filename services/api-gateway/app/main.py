"""
Main application module for API Gateway Service
"""
import logging
import os
import uuid
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from common.app.base.app_factory import create_app
from common.app.base.logging import configure_logging
from app.core.config import settings
from app.api import health
from app.routers import api, auth
from app.middleware.rate_limiting import rate_limiter, rate_limiting_middleware
from app.middleware.auth import auth_middleware
from app.middleware.logging import logging_middleware, metrics
from app.middleware.circuit_breaker import circuit_breaker_middleware
from app.services.service_discovery import service_discovery

# Configure logging
logger = configure_logging(
    service_name=settings.APP_NAME,
    log_level=settings.LOG_LEVEL
)

# Lifespan handler
async def lifespan_handler(app: FastAPI, event: str) -> None:
    """
    Handle application lifecycle events
    
    Args:
        app: FastAPI application
        event: Lifecycle event ("startup" or "shutdown")
    """
    if event == "startup":
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        # Initialize service-specific components
        await initialize_components()
    else:  # shutdown
        logger.info(f"Shutting down {settings.APP_NAME}")
        # Cleanup service-specific resources
        await cleanup_resources()

async def initialize_components() -> None:
    """Initialize service components"""
    # Use a semaphore to limit concurrent initialization tasks
    semaphore = asyncio.Semaphore(1)
    
    async def init_rate_limiter():
        try:
            # Initialize Redis connection for rate limiting
            await rate_limiter.init_redis()
            logger.info("Rate limiter initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {str(e)}")
            return False
    
    async def register_with_discovery():
        try:
            # Register with service discovery
            service_data = {
                "id": "api-gateway",
                "name": settings.APP_NAME,
                "host": os.environ.get("HOST", "api-gateway"),
                "port": int(os.environ.get("PORT", str(settings.PORT))),
                "health_check": f"{settings.API_V1_STR}/health",
                "status": "healthy"
            }
            
            # Use a semaphore to prevent concurrent registrations
            async with semaphore:
                success = await service_discovery.register_service(service_data)
                
            if success:
                logger.info(f"Registered with service discovery: {service_data['id']}")
                return True
            else:
                logger.warning("Failed to register with service discovery")
                return False
        except Exception as e:
            logger.error(f"Error during service registration: {str(e)}")
            return False
    
    async def refresh_services():
        try:
            # Refresh services from service discovery
            # Use a semaphore to prevent concurrent refreshes
            async with semaphore:
                success = await service_discovery.refresh_services()
                
            if success:
                logger.info("Successfully refreshed services from discovery")
                return True
            else:
                logger.warning("Failed to refresh services from discovery")
                return False
        except Exception as e:
            logger.error(f"Error refreshing services: {str(e)}")
            return False
    
    # Run initialization tasks in sequence to avoid race conditions
    # First initialize rate limiter
    rate_limiter_success = await init_rate_limiter()
    
    # Then ensure service discovery client is initialized before registration
    try:
        service_discovery_initialized = await service_discovery._ensure_client()
        if not service_discovery_initialized:
            logger.warning("Service discovery client initialization failed")
        else:
            logger.info("Service discovery client initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing service discovery client: {str(e)}")
        service_discovery_initialized = False
    
    # Then register with service discovery if client is initialized
    registration_success = False
    if service_discovery_initialized:
        registration_success = await register_with_discovery()
        
        # Only refresh services if registration was successful
        if registration_success:
            try:
                await refresh_services()
            except Exception as e:
                logger.error(f"Error refreshing services: {str(e)}")
    else:
        logger.warning("Skipping service registration: service discovery client not initialized")

async def cleanup_resources() -> None:
    """Cleanup service resources"""
    # Use a semaphore to limit concurrent cleanup tasks
    semaphore = asyncio.Semaphore(1)
    
    async def deregister_from_discovery():
        try:
            # Deregister from service discovery
            async with semaphore:
                success = await service_discovery.deregister_service("api-gateway")
                
            if success:
                logger.info("Successfully deregistered from service discovery")
            else:
                logger.warning("Failed to deregister from service discovery")
        except Exception as e:
            logger.error(f"Error during service deregistration: {str(e)}")
    
    async def close_service_discovery():
        try:
            # Close HTTP client
            async with semaphore:
                await service_discovery.close()
                
            logger.info("Closed service discovery HTTP client")
        except Exception as e:
            logger.error(f"Error closing service discovery client: {str(e)}")
    
    async def close_rate_limiter():
        try:
            # Close Redis connection for rate limiter
            await rate_limiter.close()
            logger.info("Closed rate limiter Redis connection")
        except Exception as e:
            logger.error(f"Error closing rate limiter: {str(e)}")
    
    # First ensure service discovery client is initialized
    try:
        service_discovery_initialized = await service_discovery._ensure_client()
        
        # Only attempt to deregister if client is initialized
        if service_discovery_initialized:
            # First deregister from service discovery
            await deregister_from_discovery()
        else:
            logger.warning("Skipping deregistration: service discovery client not initialized")
    except Exception as e:
        logger.error(f"Error initializing service discovery client during cleanup: {str(e)}")
        service_discovery_initialized = False
        logger.warning("Skipping deregistration due to client initialization error")
    
    # Close resources sequentially to ensure proper cleanup
    try:
        # First close service discovery to ensure deregistration completes
        await close_service_discovery()
        
        # Then close rate limiter
        await close_rate_limiter()
        
        logger.info("All cleanup tasks completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        
    # Final safety check - force close any remaining connections
    try:
        # Use a timeout to prevent hanging during final cleanup
        await asyncio.wait_for(
            asyncio.gather(
                service_discovery.close(),
                rate_limiter.close(),
                return_exceptions=True
            ), 
            timeout=5.0
        )
    except Exception:
        # Ignore any errors in final cleanup
        pass

# Create FastAPI application
app = create_app(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan_handler=lifespan_handler,
    cors_origins=settings.CORS_ORIGINS,
    enable_metrics=settings.ENABLE_METRICS,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Add metrics middleware if enabled
if settings.ENABLE_METRICS:
    MetricsMiddleware = metrics.create_middleware()
    app.add_middleware(MetricsMiddleware)

# Include API health router (for API versioned health checks)
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"])

# Include other API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(api.router, prefix=settings.API_V1_STR)

# Include root health router for direct health checks (e.g., for Kubernetes probes)
from app.routers.health import router as health_router
app.include_router(health_router, prefix="/health", tags=["Health"], include_in_schema=False)

# Add custom middleware
@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    """
    Custom middleware chain for the API Gateway
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The response from the next handler
    """
    # Apply middleware in order - from outermost to innermost
    # The correct order is:
    # 1. Logging (outermost) - logs all requests and responses
    # 2. Authentication - authenticates the user
    # 3. Rate Limiting - limits request rate based on user or IP
    # 4. Circuit Breaker (innermost) - prevents cascading failures
      # Define the middleware chain from innermost to outermost
    async def circuit_breaker_handler(req):
        # Circuit breaker is the innermost middleware, closest to the actual handler
        return await circuit_breaker_middleware(req, call_next)
    
    async def rate_limiting_handler(req):
        # Rate limiting comes after authentication but before circuit breaker
        return await rate_limiting_middleware(req, circuit_breaker_handler)
    
    async def auth_handler(req):
        # Authentication comes after logging but before rate limiting
        return await auth_middleware(req, rate_limiting_handler)
    
    # Start with the outermost middleware (logging)
    # Logging is the outermost middleware, it should see all requests and responses
    return await logging_middleware(request, auth_handler)

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions
    
    Args:
        request: The incoming request
        exc: The HTTP exception
        
    Returns:
        JSONResponse: A JSON response with the error details
    """
    # Log client errors (4xx) as warnings and server errors (5xx) as errors
    if 400 <= exc.status_code < 500:
        logger.warning(f"HTTP {exc.status_code} error: {exc.detail}")
    else:
        logger.error(f"HTTP {exc.status_code} error: {exc.detail}")
    
    # Return the exception details
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

# Global exception handler for all other exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for the API Gateway
    
    Args:
        request: The incoming request
        exc: The exception
        
    Returns:
        JSONResponse: A JSON response with the error details
    """
    # Generate a unique error ID for tracking
    error_id = str(uuid.uuid4())
    
    # Log the exception with the error ID
    logger.error(
        f"Unhandled exception (ID: {error_id}): {str(exc)}", 
        exc_info=True,
        extra={"error_id": error_id, "path": request.url.path}
    )
    
    # Return a generic error message in production, more details in debug mode
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "error_id": error_id,  # Include the error ID for tracking
            "status_code": 500
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint for the API Gateway
    
    Returns:
        Dict: A welcome message with links to documentation and health check
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to the AI Voice Agent API Gateway",
        "documentation": {
            "swagger": f"{settings.API_V1_STR}/docs",
            "redoc": f"{settings.API_V1_STR}/redoc",
            "openapi": f"{settings.API_V1_STR}/openapi.json"
        },
        "health": f"{settings.API_V1_STR}/health",
        "status": "operational"
    }

# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )