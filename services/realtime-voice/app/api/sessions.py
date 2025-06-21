"""
Session management endpoints for the Real-time Voice AI Service
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body, status
from pydantic import BaseModel

from ..core.config import settings
from ..core.session.manager import session_manager
from ..services.initialization import active_sessions, close_session

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Sessions"])

class SessionResponse(BaseModel):
    """Session response model"""
    session_id: str
    user_id: Optional[str] = None
    language: str
    accent: Optional[str] = None
    domain: Optional[str] = None
    created_at: float
    last_activity: float
    is_active: bool

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
async def create_session(user_id: Optional[str] = None):
    """
    Create a new conversation session
    
    Args:
        user_id: Optional user ID to associate with the session
        
    Returns:
        SessionResponse: The created session
    """
    try:
        session = session_manager.create_session(user_id)
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            language=session.language,
            accent=session.accent,
            domain=session.domain,
            created_at=session.created_at,
            last_activity=session.last_activity,
            is_active=session.session_id in active_sessions
        )
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get session information
    
    Args:
        session_id: Session ID
        
    Returns:
        SessionResponse: Session information
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        language=session.language,
        accent=session.accent,
        domain=session.domain,
        created_at=session.created_at,
        last_activity=session.last_activity,
        is_active=session.session_id in active_sessions
    )

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """
    Delete a session
    
    Args:
        session_id: Session ID
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Close active session
    await close_session(session_id)
    
    # Remove from session manager
    session_manager.delete_session(session_id)

@router.get("", response_model=List[SessionResponse])
async def get_sessions():
    """
    Get all sessions
    
    Returns:
        List[SessionResponse]: List of all sessions
    """
    sessions = session_manager.get_all_sessions()
    
    return [
        SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            language=session.language,
            accent=session.accent,
            domain=session.domain,
            created_at=session.created_at,
            last_activity=session.last_activity,
            is_active=session.session_id in active_sessions
        )
        for session in sessions
    ]

class LanguageUpdate(BaseModel):
    """Language update model"""
    language: str

@router.put("/{session_id}/language", response_model=SessionResponse)
async def set_session_language(session_id: str, data: LanguageUpdate):
    """
    Set session language
    
    Args:
        session_id: Session ID
        data: Language update data
        
    Returns:
        SessionResponse: Updated session
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Update language
    session.language = data.language
    session_manager.update_session(session)
    
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        language=session.language,
        accent=session.accent,
        domain=session.domain,
        created_at=session.created_at,
        last_activity=session.last_activity,
        is_active=session.session_id in active_sessions
    )