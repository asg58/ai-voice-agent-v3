"""
Request Models for Core Engine Service

This module defines Pydantic models for incoming API requests.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class ProcessingRequest(BaseModel):
    """Model for general AI processing requests."""
    
    request_id: str = Field(..., description="Unique request identifier")
    request_type: str = Field(..., description="Type of request (text, voice, document)")
    input_data: Dict[str, Any] = Field(..., description="Input data to process")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationRequest(BaseModel):
    """Model for conversation requests."""
    
    session_id: str = Field(..., description="Conversation session identifier")
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class TextProcessingRequest(BaseModel):
    """Model for text processing requests."""
    
    text: str = Field(..., description="Text to process")
    language: Optional[str] = Field("en", description="Text language")
    processing_type: str = Field("general", description="Type of text processing")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VoiceProcessingRequest(BaseModel):
    """Model for voice processing requests."""
    
    audio_data: bytes = Field(..., description="Audio data to process")
    audio_format: str = Field("wav", description="Audio format")
    sample_rate: int = Field(16000, description="Audio sample rate")
    language: Optional[str] = Field("en", description="Expected audio language")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentProcessingRequest(BaseModel):
    """Model for document processing requests."""
    
    document_data: bytes = Field(..., description="Document data to process")
    document_type: str = Field(..., description="Document type (pdf, docx, txt, etc.)")
    processing_options: Optional[Dict[str, Any]] = Field(None, description="Processing options")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
Request Models for Core Engine Service

This module defines Pydantic models for incoming API requests.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class ProcessingRequest(BaseModel):
    """Model for general AI processing requests."""
    
    request_id: str = Field(..., description="Unique request identifier")
    request_type: str = Field(..., description="Type of request (text, voice, document)")
    input_data: Dict[str, Any] = Field(..., description="Input data to process")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationRequest(BaseModel):
    """Model for conversation requests."""
    
    session_id: str = Field(..., description="Conversation session identifier")
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class TextProcessingRequest(BaseModel):
    """Model for text processing requests."""
    
    text: str = Field(..., description="Text to process")
    language: Optional[str] = Field("en", description="Text language")
    processing_type: str = Field("general", description="Type of text processing")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VoiceProcessingRequest(BaseModel):
    """Model for voice processing requests."""
    
    audio_data: bytes = Field(..., description="Audio data to process")
    audio_format: str = Field("wav", description="Audio format")
    sample_rate: int = Field(16000, description="Audio sample rate")
    language: Optional[str] = Field("en", description="Expected audio language")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentProcessingRequest(BaseModel):
    """Model for document processing requests."""
    
    document_data: bytes = Field(..., description="Document data to process")
    document_type: str = Field(..., description="Document type (pdf, docx, txt, etc.)")
    processing_options: Optional[Dict[str, Any]] = Field(None, description="Processing options")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")