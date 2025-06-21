"""
Main application module for Service Mesh
"""
import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
import time

from app.core.config import settings
from app.api import health, proxy, config, telemetry
from app.services.service_discovery import ServiceDiscoveryClient
from app.services.config_loader import ConfigLoader
from app.services.circuit_breaker import CircuitBreakerRegistry
from app.services.rate_limiter import RateLimiterRegistry
from app.services.router import Router
from app.services.proxy import ProxyService
from app.services.telemetry import TelemetryService

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Service Mesh for the AI Voice Agent platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
methods = settings.CORS_METHODS.split(",") if settings.CORS_METHODS != "*" else ["*"]
headers = settings.CORS_HEADERS.split(",") if settings.CORS_HEADERS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers,
)


# Dependency injection
@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize services
    app.state.service_discovery_client = ServiceDiscoveryClient()
    app.state.config_loader = ConfigLoader()
    app.state.circuit_breaker_registry = CircuitBreakerRegistry()
    app.state.rate_limiter_registry = RateLimiterRegistry()
    app.state.router = Router(app.state.service_discovery_client)
    app.state.proxy_service = ProxyService(
        app.state.router,
        app.state.circuit_breaker_registry,
        app.state.rate_limiter_registry
    )
    app.state.telemetry_service = TelemetryService()
    
    # Load configuration
    config = app.state.config_loader.load_config()
    if config:
        # Add routes from configuration
        for service in config.services:
            app.state.router.add_routes(service.routes)
    
    logger.info(f"{settings.APP_NAME} started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    """
    logger.info(f"Shutting down {settings.APP_NAME}")


# Add middleware for request timing and telemetry
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add process time header and collect telemetry.
    
    Args:
        request: Request object
        call_next: Next middleware function
        
    Returns:
        Response: Response object
    """
    # Start timer
    start_time = time.time()
      # Create span for request
    telemetry_service = app.state.telemetry_service
    span = telemetry_service.create_span(
        name=f"{request.method} {request.url.path}",
        service_name=settings.APP_NAME
    )
    
    # Add request information to span
    telemetry_service.add_span_tag(span, "method", request.method)
    telemetry_service.add_span_tag(span, "path", request.url.path)
    telemetry_service.add_span_tag(span, "client_host", request.client.host)
    
    # Process request
    try:
        response = await call_next(request)
        
        # Add response information to span
        telemetry_service.add_span_tag(span, "status_code", str(response.status_code))
        
        # Add process time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Record metric
        telemetry_service.record_metric(
            name="request_duration_seconds",
            value=process_time,
            labels={
                "method": request.method,
                "path": request.url.path,
                "status_code": str(response.status_code)
            }
        )
        
        return response
    except Exception as e:
        # Log error
        logger.error(f"Error processing request: {str(e)}")
        
        # Add error information to span
        telemetry_service.add_span_tag(span, "error", "true")
        telemetry_service.add_span_tag(span, "error_message", str(e))
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    finally:
        # End span
        telemetry_service.end_span(span)


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(proxy.router, prefix="/api/v1", tags=["Proxy"])
app.include_router(config.router, prefix="/api/v1", tags=["Config"])
app.include_router(telemetry.router, prefix="/api/v1", tags=["Telemetry"])


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: Service information
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Service Mesh for the AI Voice Agent platform"
    }