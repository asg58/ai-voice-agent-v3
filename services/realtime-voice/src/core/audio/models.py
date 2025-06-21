"""
Audio Models for AI Voice Agent
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TTSRequest(BaseModel):
    """Text-to-Speech request"""
    session_id: str = Field(..., description="Conversation session ID")
    text: str = Field(..., description="Text to synthesize")
    voice: str = Field("default", description="Voice to use")
    language: str = Field("nl", description="Language code")
    speed: float = Field(1.0, description="Speech speed multiplier")
    pitch: Optional[float] = Field(None, description="Speech pitch adjustment")
    emotion: Optional[str] = Field(None, description="Emotion to convey")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class TTSResponse(BaseModel):
    """Text-to-Speech response"""
    session_id: str = Field(..., description="Conversation session ID")
    audio_data: bytes = Field(..., description="Synthesized audio data")
    sample_rate: int = Field(16000, description="Audio sample rate")
    duration: float = Field(..., description="Audio duration in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")