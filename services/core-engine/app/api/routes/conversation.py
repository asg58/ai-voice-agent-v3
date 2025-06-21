"""
Conversation API Routes

API endpoints for conversation management and processing.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


class ConversationRequest(BaseModel):
    """Request model for conversation processing."""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response model for conversation processing."""
    response: str
    session_id: str
    status: str = "success"
    context: Optional[Dict[str, Any]] = None


@router.post("/start", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationRequest,
    app_request: Request
) -> ConversationResponse:
    """
    Start a new conversation or continue an existing one.
    
    Args:
        request: Conversation request data
        app_request: FastAPI request object
        
    Returns:
        ConversationResponse: AI response and session information
    """
    try:
        # Get AI orchestrator from app state
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process conversation
        ai_response = await orchestrator.handle_conversation(
            message=request.message,
            session_id=session_id,
            context=request.context
        )
        
        logger.info(f"Processed conversation for session {session_id}")
        
        return ConversationResponse(
            response=ai_response,
            session_id=session_id,
            context=request.context
        )
        
    except Exception as e:
        logger.error(f"Error processing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation processing failed: {str(e)}")


@router.get("/session/{session_id}")
async def get_conversation_history(
    session_id: str,
    app_request: Request
) -> Dict[str, Any]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        app_request: FastAPI request object
        
    Returns:
        Dict containing conversation history
    """
    try:
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        # Get conversation from cache
        conversation = orchestrator.conversation_cache.get(session_id, [])
        
        return {
            "session_id": session_id,
            "conversation": conversation,
            "message_count": len(conversation),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_conversation(
    session_id: str,
    app_request: Request
) -> Dict[str, Any]:
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session identifier
        app_request: FastAPI request object
        
    Returns:
        Dict containing operation status
    """
    try:
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        # Clear conversation from cache
        if session_id in orchestrator.conversation_cache:
            del orchestrator.conversation_cache[session_id]
            logger.info(f"Cleared conversation for session {session_id}")
        
        return {
            "session_id": session_id,
            "status": "cleared",
            "message": "Conversation history cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")


@router.get("/sessions")
async def list_active_sessions(app_request: Request) -> Dict[str, Any]:
    """
    List all active conversation sessions.
    
    Args:
        app_request: FastAPI request object
        
    Returns:
        Dict containing active sessions information
    """
    try:
        orchestrator = getattr(app_request.app.state, 'ai_orchestrator', None)
        if not orchestrator:
            raise HTTPException(status_code=500, detail="AI orchestrator not available")
        
        sessions = []
        for session_id, conversation in orchestrator.conversation_cache.items():
            if conversation:
                sessions.append({
                    "session_id": session_id,
                    "message_count": len(conversation),
                    "last_activity": conversation[-1].get("timestamp") if conversation else None
                })
        
        return {
            "active_sessions": len(sessions),
            "sessions": sessions,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")