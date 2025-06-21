"""
Core Engine API Routes

This module defines all API routes for AI processing and orchestration.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import logging

from ..core.ai_orchestrator import AIOrchestrator
from ..models.requests import ProcessingRequest, ConversationRequest
from ..models.responses import ProcessingResponse, ConversationResponse

logger = logging.getLogger(__name__)

ai_router = APIRouter()


async def get_ai_orchestrator(request: Request) -> AIOrchestrator:
    """Dependency to get AI orchestrator instance."""
    # This will be injected from the app state
    return request.app.state.ai_orchestrator


@ai_router.post("/process", response_model=ProcessingResponse)
async def process_ai_request(
    request: ProcessingRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)
) -> ProcessingResponse:
    """
    Process an AI request through the orchestration engine.

    Args:
        request: The processing request containing input data
        orchestrator: AI orchestrator instance
        
    Returns:
        ProcessingResponse: The processed result
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing request: {request.request_id}")
        
        # Process the request through the orchestrator
        result = await orchestrator.process_request(
            request_type=request.request_type,
            input_data=request.input_data,
            context=request.context
        )
        
        return ProcessingResponse(
            request_id=request.request_id,
            status="completed",
            result=result,
            metadata={"processing_engine": "core-engine"}
        )
        
    except Exception as e:
        logger.error(f"Error processing request {request.request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@ai_router.post("/conversation", response_model=ConversationResponse)
async def handle_conversation(
    request: ConversationRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)
) -> ConversationResponse:
    """
    Handle a conversation turn with the AI system.

    Args:
        request: The conversation request
        orchestrator: AI orchestrator instance
        
    Returns:
        ConversationResponse: The AI response
        
    Raises:
        HTTPException: If conversation handling fails
    """
    try:
        logger.info(f"Handling conversation: {request.conversation_id}")
          # Process the conversation through the orchestrator
        response = await orchestrator.handle_conversation(
            message=request.message,
            session_id=request.conversation_id,
            context=request.context
        )
        
        return ConversationResponse(
            session_id=request.conversation_id,
            response=response,
            status="completed",
            context=request.context,
            metadata={"processing_engine": "core-engine"}
        )
        
    except Exception as e:
        logger.error(f"Error in conversation {request.conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@ai_router.get("/status")
async def get_ai_status(
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)
) -> Dict[str, Any]:
    """
    Get the current status of the AI orchestrator.

    Returns:
        Dict containing status information
    """
    try:
        status = await orchestrator.get_status()
        return {
            "status": "healthy",
            "orchestrator_info": status,
            "service": "core-engine",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error getting AI status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
