"""
AI Processing API Routes

API endpoints for general AI processing tasks.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessingRequest(BaseModel):
    """Request model for AI processing."""
    input_data: Dict[str, Any]
    request_type: str  # text, voice, document
    context: Optional[Dict[str, Any]] = None


class ProcessingResponse(BaseModel):
    """Response model for AI processing."""
    result: Dict[str, Any]
    status: str = "success"
    processing_time: Optional[float] = None


@router.post("/process", response_model=ProcessingResponse)
async def process_ai_request(
    request: ProcessingRequest,
    app_request: Request
) -> ProcessingResponse:
    """
    Process an AI request through the orchestrator.
    
    Args:
        request: Processing request data
        app_request: FastAPI request object
        
    Returns:
        ProcessingResponse: Processing result and metadata
    """
    import time
    start_time = time.time()
    
    try:
        # Get AI orchestrator from app state
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        # Process the request
        result = await orchestrator.process_request(
            input_data=request.input_data,
            request_type=request.request_type,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Processed {request.request_type} request in {processing_time:.2f}s")
        
        return ProcessingResponse(
            result=result,
            processing_time=processing_time
        )
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/text/process")
async def process_text(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    app_request: Request = None
) -> Dict[str, Any]:
    """
    Process text through AI models.
    
    Args:
        text: Text to process
        context: Optional context information
        app_request: FastAPI request object
        
    Returns:
        Dict containing processing result
    """
    try:
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        result = await orchestrator.process_request(
            input_data={"text": text},
            request_type="text",
            context=context
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")


@router.get("/models")
async def get_available_models(app_request: Request) -> Dict[str, Any]:
    """
    Get information about available AI models.
    
    Args:
        app_request: FastAPI request object
        
    Returns:
        Dict containing model information
    """
    try:
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        status = await orchestrator.get_status()
        
        return {
            "models": status.get("models", {}),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {str(e)}")


@router.get("/status")
async def get_ai_status(app_request: Request) -> Dict[str, Any]:
    """
    Get AI processing status and statistics.
    
    Args:
        app_request: FastAPI request object
        
    Returns:
        Dict containing AI status information
    """
    try:
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        status = await orchestrator.get_status()
        
        return {
            "ai_status": status,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving AI status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI status: {str(e)}")