"""
Real-time Voice AI Service
Main FastAPI application entry point
"""
import logging
import sys
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

try:
    from common.app.base.app_factory import create_app
    from common.app.base.logging import configure_logging
except ImportError:
    # Fallback if common module is not available
    def create_app(title, description, version, lifespan_handler, cors_origins, enable_metrics):
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await lifespan_handler(app, "startup")
            yield
            await lifespan_handler(app, "shutdown")
        
        app = FastAPI(title=title, description=description, version=version, lifespan=lifespan)
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        return app
    
    def configure_logging(service_name, log_level):
        import logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format=f"%(asctime)s - {service_name} - %(levelname)s - %(message)s"
        )
        return logging.getLogger(service_name)
from app.core.config import settings
from app.api import health, sessions, audio, websocket
from app.services.initialization import initialize_components, cleanup_resources

# Configure logging
logger = configure_logging(
    service_name="realtime-voice",
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
        # Set start time
        app.state.start_time = datetime.now()
        
        # Initialize components
        await initialize_components()
        
        logger.info(f"{settings.APP_NAME} is ready!")
    else:  # shutdown
        logger.info(f"Shutting down {settings.APP_NAME}...")
        # Cleanup resources
        await cleanup_resources()

# Create FastAPI application
app = create_app(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan_handler=lifespan_handler,
    cors_origins=settings.CORS_ORIGINS,
    enable_metrics=settings.ENABLE_METRICS
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(audio.router, prefix="/audio", tags=["Audio"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Add WebSocket endpoint
app.add_websocket_route("/ws/{session_id}", websocket.websocket_endpoint)

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint - serves the main interface
    
    Args:
        request: HTTP request
        
    Returns:
        HTMLResponse: Main interface
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": settings.APP_NAME}
    )

# Dashboard endpoint
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Dashboard endpoint - serves the dashboard interface
    
    Args:
        request: HTTP request
        
    Returns:
        HTMLResponse: Dashboard interface
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": f"{settings.APP_NAME} Dashboard"}
    )

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