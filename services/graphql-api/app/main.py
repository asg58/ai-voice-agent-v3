"""
Main application module for GraphQL API Service
"""
import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp
from app.api.schema import schema
from app.core.config import settings
from app.core.database import init_db
from app.services.event_service import publish_event

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("graphql-api")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="GraphQL API for AI Voice Agent Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL endpoint
app.add_route("/graphql", GraphQLApp(schema=schema))


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("Starting GraphQL API service")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    
    # Wait for RabbitMQ to be ready
    logger.info("Waiting for RabbitMQ to be ready...")
    time.sleep(5)
    
    # Publish startup event
    publish_event("startup", {"service": "graphql-api"})


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("Shutting down GraphQL API service")
    publish_event("shutdown", {"service": "graphql-api"})


@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns:
        dict: Service information
    """
    return {
        "service": "GraphQL API",
        "version": "1.0.0",
        "endpoints": {
            "graphql": "/graphql",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Health status
    """
    # TODO: Add more health checks (database, RabbitMQ, etc.)
    return {
        "status": "healthy",
        "service": "graphql-api"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    
    Args:
        request (Request): Request object
        exc (Exception): Exception
    
    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )