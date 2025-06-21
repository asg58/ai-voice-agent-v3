"""
Conversation Models for AI Voice Agent
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from src.models import TranscriptionResult
from src.core.audio.models import TTSRequest

class ConversationMessage(BaseModel):
    """Message in a conversation"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")