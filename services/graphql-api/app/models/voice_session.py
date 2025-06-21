"""
Voice Session model for GraphQL API Service
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class VoiceSession(Base):
    """
    Voice Session model
    """
    __tablename__ = "voice_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # active, completed, failed
    language = Column(String)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    session_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="voice_sessions")
    interactions = relationship("VoiceInteraction", back_populates="session")


class VoiceInteraction(Base):
    """
    Voice Interaction model
    """
    __tablename__ = "voice_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("voice_sessions.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_input = Column(Text, nullable=True)
    system_response = Column(Text, nullable=True)
    audio_file_path = Column(String, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    intent = Column(String, nullable=True)
    entities = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("VoiceSession", back_populates="interactions")