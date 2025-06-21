"""
Voice service for GraphQL API
"""
import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.voice_session import VoiceSession, VoiceInteraction
from app.services.event_service import publish_event

logger = logging.getLogger(__name__)


def get_voice_sessions(user_id=None, status=None):
    """
    Get voice sessions, optionally filtered by user ID or status
    
    Args:
        user_id (int, optional): User ID. Defaults to None.
        status (str, optional): Status. Defaults to None.
    
    Returns:
        list: List of VoiceSession objects
    """
    db = next(get_db())
    query = db.query(VoiceSession)
    
    if user_id:
        query = query.filter(VoiceSession.user_id == user_id)
    
    if status:
        query = query.filter(VoiceSession.status == status)
    
    return query.all()


def get_voice_session(id=None, session_id=None):
    """
    Get a voice session by ID or session ID
    
    Args:
        id (int, optional): Voice session ID. Defaults to None.
        session_id (str, optional): Voice session UUID. Defaults to None.
    
    Returns:
        VoiceSession: Voice session object
    """
    if not id and not session_id:
        raise ValueError("Either id or session_id must be provided")
    
    db = next(get_db())
    query = db.query(VoiceSession)
    
    if id:
        return query.filter(VoiceSession.id == id).first()
    else:
        return query.filter(VoiceSession.session_id == session_id).first()


def create_voice_session(user_id, language, metadata=None):
    """
    Create a new voice session
    
    Args:
        user_id (int): User ID
        language (str): Language code
        metadata (dict, optional): Metadata. Defaults to None.
    
    Returns:
        VoiceSession: Created voice session
    """
    db = next(get_db())
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Create new voice session
    voice_session = VoiceSession(
        session_id=session_id,
        user_id=user_id,
        status="active",
        language=language,
        metadata=metadata
    )
    
    db.add(voice_session)
    db.commit()
    db.refresh(voice_session)
    
    # Publish event
    publish_event("voice_session_created", {
        "session_id": session_id,
        "user_id": user_id,
        "language": language
    })
    
    logger.info(f"Created voice session: {session_id}")
    return voice_session


def update_voice_session(session_id, status=None, language=None, metadata=None):
    """
    Update an existing voice session
    
    Args:
        session_id (int): Voice session ID
        status (str, optional): Status. Defaults to None.
        language (str, optional): Language code. Defaults to None.
        metadata (dict, optional): Metadata. Defaults to None.
    
    Returns:
        VoiceSession: Updated voice session
    """
    db = next(get_db())
    voice_session = db.query(VoiceSession).filter(VoiceSession.id == session_id).first()
    
    if not voice_session:
        raise ValueError(f"Voice session with ID {session_id} not found")
    
    # Update fields if provided
    if status is not None:
        voice_session.status = status
    
    if language is not None:
        voice_session.language = language
    
    if metadata is not None:
        # Merge with existing metadata if it exists
        if voice_session.metadata:
            voice_session.metadata.update(metadata)
        else:
            voice_session.metadata = metadata
    
    db.commit()
    db.refresh(voice_session)
    
    # Publish event
    publish_event("voice_session_updated", {
        "session_id": voice_session.session_id,
        "status": voice_session.status,
        "language": voice_session.language
    })
    
    logger.info(f"Updated voice session: {voice_session.session_id}")
    return voice_session


def end_voice_session(session_id):
    """
    End a voice session
    
    Args:
        session_id (int): Voice session ID
    
    Returns:
        VoiceSession: Updated voice session
    """
    db = next(get_db())
    voice_session = db.query(VoiceSession).filter(VoiceSession.id == session_id).first()
    
    if not voice_session:
        raise ValueError(f"Voice session with ID {session_id} not found")
    
    # Update session
    voice_session.status = "completed"
    voice_session.end_time = datetime.now()
    
    # Calculate duration
    if voice_session.start_time:
        delta = voice_session.end_time - voice_session.start_time
        voice_session.duration = int(delta.total_seconds())
    
    db.commit()
    db.refresh(voice_session)
    
    # Publish event
    publish_event("voice_session_ended", {
        "session_id": voice_session.session_id,
        "duration": voice_session.duration
    })
    
    logger.info(f"Ended voice session: {voice_session.session_id}")
    return voice_session


def get_voice_interactions(session_id):
    """
    Get voice interactions for a session
    
    Args:
        session_id (int): Voice session ID
    
    Returns:
        list: List of VoiceInteraction objects
    """
    db = next(get_db())
    return db.query(VoiceInteraction).filter(VoiceInteraction.session_id == session_id).all()


def create_voice_interaction(session_id, user_input=None, system_response=None, 
                            audio_file_path=None, confidence_score=None, 
                            intent=None, entities=None):
    """
    Create a new voice interaction
    
    Args:
        session_id (int): Voice session ID
        user_input (str, optional): User input. Defaults to None.
        system_response (str, optional): System response. Defaults to None.
        audio_file_path (str, optional): Audio file path. Defaults to None.
        confidence_score (int, optional): Confidence score. Defaults to None.
        intent (str, optional): Intent. Defaults to None.
        entities (dict, optional): Entities. Defaults to None.
    
    Returns:
        VoiceInteraction: Created voice interaction
    """
    db = next(get_db())
    
    # Check if session exists
    voice_session = db.query(VoiceSession).filter(VoiceSession.id == session_id).first()
    if not voice_session:
        raise ValueError(f"Voice session with ID {session_id} not found")
    
    # Create new voice interaction
    voice_interaction = VoiceInteraction(
        session_id=session_id,
        user_input=user_input,
        system_response=system_response,
        audio_file_path=audio_file_path,
        confidence_score=confidence_score,
        intent=intent,
        entities=entities
    )
    
    db.add(voice_interaction)
    db.commit()
    db.refresh(voice_interaction)
    
    # Publish event
    publish_event("voice_interaction_created", {
        "interaction_id": voice_interaction.id,
        "session_id": voice_session.session_id,
        "intent": intent
    })
    
    logger.info(f"Created voice interaction for session: {voice_session.session_id}")
    return voice_interaction