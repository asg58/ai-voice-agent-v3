"""
Production entry point for the Real-time Voice AI service
Optimized for production environments with enhanced security and performance
"""
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import the consolidated main application
from main import app as main_app

# Configure production logging
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("realtime_voice_production")

# Create production app wrapper
app = FastAPI(
    title="Real-time Voice AI - Production",
    description="Production-ready Real-time Voice AI Service (Consolidated Version)",
    version="1.0.0-consolidated",
    docs_url=None if os.environ.get("DISABLE_DOCS", "false").lower() == "true" else "/docs",
    redoc_url=None if os.environ.get("DISABLE_DOCS", "false").lower() == "true" else "/redoc",
)

# Add production middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )

# Mount the main application
app.mount("/", main_app)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Real-time Voice AI in production mode")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Real-time Voice AI production server")