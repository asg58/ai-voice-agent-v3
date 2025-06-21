"""
Main application module for Dashboard Service
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from loguru import logger

from app.core.config import settings
from app.routers import auth, dashboard, health

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Dashboard Service for monitoring and managing the AI Voice Agent platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

# Mount static files
if os.path.exists(settings.STATIC_DIR):
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    """
    logger.info(f"Shutting down {settings.APP_NAME}")


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint.
    
    Args:
        request: Request object
        
    Returns:
        HTMLResponse: HTML response
    """
    # If we have a frontend build, serve the index.html
    if os.path.exists(os.path.join(settings.STATIC_DIR, "index.html")):
        return templates.TemplateResponse("index.html", {"request": request})
    
    # Otherwise, return a simple HTML page
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Dashboard Service</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f5f5f5;
                }
                .container {
                    text-align: center;
                    padding: 2rem;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #333;
                }
                p {
                    color: #666;
                }
                .links {
                    margin-top: 1rem;
                }
                a {
                    color: #0066cc;
                    text-decoration: none;
                    margin: 0 0.5rem;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Dashboard Service</h1>
                <p>Welcome to the Dashboard Service for the AI Voice Agent platform.</p>
                <div class="links">
                    <a href="/docs">API Documentation</a>
                    <a href="/api/v1/health">Health Check</a>
                </div>
            </div>
        </body>
    </html>
    """