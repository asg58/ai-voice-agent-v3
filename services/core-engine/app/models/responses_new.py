"""
Response Models for Core Engine Service

This module defines Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class ProcessingResponse(BaseModel):
    """Model for AI processing responses."""
    
    request_id: str = Field(..., description="Request identifier")
    response_id: str = Field(..., description="Unique response identifier")
    status: str = Field(..., description="Processing status")
    result: Dict[str, Any] = Field(..., description="Processing result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationResponse(BaseModel):
    """Model for conversation responses."""
    
    conversation_id: str = Field(..., description="Conversation identifier")
    response_id: str = Field(..., description="Response identifier")
    message: str = Field(..., description="AI response message")
    context: Optional[Dict[str, Any]] = Field(None, description="Updated conversation context")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class VoiceProcessingResponse(BaseModel):
    """Model for voice processing responses."""
    
    audio_data: Optional[bytes] = Field(None, description="Processed audio data")
    transcription: Optional[str] = Field(None, description="Audio transcription")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Audio analysis results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")


class HealthResponse(BaseModel):
    """Model for health check responses."""
    
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    services: Optional[Dict[str, str]] = Field(None, description="Component health status")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
