"""
Response Models for Core Engine Service

This module defines Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class ProcessingResponse(BaseModel):
    """Model for AI processing responses."""
    
    request_id: str = Field(..., description="Original request identifier")
    status: str = Field(..., description="Processing status")
    result: Dict[str, Any] = Field(..., description="Processing result")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationResponse(BaseModel):
    """Model for conversation responses."""
    
    session_id: str = Field(..., description="Conversation session identifier")
    response: str = Field(..., description="AI response message")
    status: str = Field(..., description="Response status")
    context: Optional[Dict[str, Any]] = Field(None, description="Updated conversation context")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class TextProcessingResponse(BaseModel):
    """Model for text processing responses."""
    
    processed_text: str = Field(..., description="Processed text result")
    original_text: str = Field(..., description="Original input text")
    processing_type: str = Field(..., description="Type of processing applied")
    confidence: Optional[float] = Field(None, description="Processing confidence score")
    language_detected: Optional[str] = Field(None, description="Detected language")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")


class VoiceProcessingResponse(BaseModel):
    """Model for voice processing responses."""
    
    transcription: str = Field(..., description="Voice transcription")
    confidence: float = Field(..., description="Transcription confidence")
    language_detected: Optional[str] = Field(None, description="Detected language")
    audio_duration: Optional[float] = Field(None, description="Audio duration in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")


class DocumentProcessingResponse(BaseModel):
    """Model for document processing responses."""
    
    extracted_text: str = Field(..., description="Extracted text from document")
    document_type: str = Field(..., description="Detected document type")
    page_count: Optional[int] = Field(None, description="Number of pages processed")
    processing_summary: Optional[Dict[str, Any]] = Field(None, description="Processing summary")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


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