"""
Audio processing endpoints for the Real-time Voice AI Service
"""
import logging
import time
import base64
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body, status, UploadFile, File
from pydantic import BaseModel

from ..core.config import settings
from ..core.session.manager import session_manager
from ..services.initialization import audio_pipeline

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Audio"])

class TTSRequest(BaseModel):
    """Text-to-speech request model"""
    text: str
    voice: Optional[str] = None
    language: Optional[str] = None

class TTSResponse(BaseModel):
    """Text-to-speech response model"""
    text: str
    audio_base64: str
    duration: float
    format: str = "wav"

@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech
    
    Args:
        request: Text-to-speech request
        
    Returns:
        TTSResponse: Audio response
    """
    try:
        # Create TTS request
        tts_request = {
            "text": request.text,
            "voice": request.voice or settings.TTS_VOICE,
            "language": request.language
        }
        
        # Synthesize speech
        tts_response = await audio_pipeline.synthesize_speech(tts_request)
        
        # Encode audio data
        audio_base64 = base64.b64encode(tts_response.audio_data).decode("utf-8")
        
        return TTSResponse(
            text=tts_response.text,
            audio_base64=audio_base64,
            duration=tts_response.duration
        )
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error synthesizing speech: {str(e)}"
        )

class STTResponse(BaseModel):
    """Speech-to-text response model"""
    text: str
    confidence: float
    language: Optional[str] = None
    duration: float

@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Convert speech to text
    
    Args:
        file: Audio file
        language: Optional language code
        
    Returns:
        STTResponse: Transcription response
    """
    try:
        # Read audio data
        audio_data = await file.read()
        
        # Create audio chunk
        chunk = {
            "audio_data": audio_data,
            "sample_rate": 16000,  # Default, can be overridden
            "channels": 1,
            "timestamp": time.time()
        }
        
        # Process audio
        result = await audio_pipeline.transcribe_audio(chunk, language)
        
        return STTResponse(
            text=result.text,
            confidence=result.confidence,
            language=result.language,
            duration=result.duration
        )
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing audio: {str(e)}"
        )

class VoiceListResponse(BaseModel):
    """Voice list response model"""
    voices: List[Dict[str, Any]]

@router.get("/voices", response_model=VoiceListResponse)
async def get_available_voices(language: Optional[str] = None):
    """
    Get available voices
    
    Args:
        language: Optional language filter
        
    Returns:
        VoiceListResponse: List of available voices
    """
    try:
        voices = await audio_pipeline.get_available_voices(language)
        
        return VoiceListResponse(voices=voices)
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available voices: {str(e)}"
        )