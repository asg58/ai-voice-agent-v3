"""
Document Module Service - Main Application Entry Point

This module provides document processing capabilities including:
- PDF parsing and extraction
- Text analysis and summarization
- Document classification
- Content indexing for vector search
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes import document_router
from .core.document_processor import DocumentProcessor
from .core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Document Module Service...")
    
    # Initialize document processor
    document_processor = DocumentProcessor()
    await document_processor.initialize()
    app.state.document_processor = document_processor
    
    yield
    
    # Cleanup
    logger.info("Shutting down Document Module Service...")
    await document_processor.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Document Module Service",
    description="Document processing engine for AI voice agent platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_router, prefix="/api/v1/documents", tags=["Document Processing"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document-module"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Document Module Service",
        "version": "1.0.0",
        "description": "Document processing engine for AI voice agent platform"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )"""
Document Module Service - Main Application Entry Point

This module provides document processing capabilities including:
- PDF parsing and extraction
- Text analysis and summarization
- Document classification
- Content indexing for vector search
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes import document_router
from .core.document_processor import DocumentProcessor
from .core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Document Module Service...")
    
    # Initialize document processor
    document_processor = DocumentProcessor()
    await document_processor.initialize()
    app.state.document_processor = document_processor
    
    yield
    
    # Cleanup
    logger.info("Shutting down Document Module Service...")
    await document_processor.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Document Module Service",
    description="Document processing engine for AI voice agent platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_router, prefix="/api/v1/documents", tags=["Document Processing"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document-module"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Document Module Service",
        "version": "1.0.0",
        "description": "Document processing engine for AI voice agent platform"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )