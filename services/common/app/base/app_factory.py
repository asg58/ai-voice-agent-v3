"""
FastAPI Application Factory
Provides standardized way to create FastAPI applications
"""
import logging
from contextlib import asynccontextmanager
from typing import Callable, List, Optional, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

def create_app(
    title: str,
    description: str,
    version: str,
    lifespan_handler: Optional[Callable] = None,
    cors_origins: List[str] = None,
    enable_metrics: bool = True,
    middleware_list: List[Dict[str, Any]] = None,
    openapi_url: str = "/openapi.json",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
) -> FastAPI:
    """
    Create a standardized FastAPI application
    
    Args:
        title: Application title
        description: Application description
        version: Application version
        lifespan_handler: Optional async function for lifespan management
        cors_origins: List of allowed CORS origins
        enable_metrics: Whether to enable Prometheus metrics
        middleware_list: List of middleware configurations
        openapi_url: URL for OpenAPI schema
        docs_url: URL for Swagger UI
        redoc_url: URL for ReDoc UI
        
    Returns:
        FastAPI application instance
    """
    # Create lifespan context manager if handler provided
    lifespan = None
    if lifespan_handler:
        @asynccontextmanager
        async def lifespan_context(app: FastAPI):
            await lifespan_handler(app, "startup")
            yield
            await lifespan_handler(app, "shutdown")
        lifespan = lifespan_context
    
    # Create FastAPI app
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    if middleware_list:
        for middleware_config in middleware_list:
            middleware_class = middleware_config.pop("class")
            app.add_middleware(middleware_class, **middleware_config)
    
    # Add Prometheus metrics
    if enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
    
    return app