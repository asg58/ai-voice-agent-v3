"""
Voice Processing API Routes

API endpoints for voice processing operations.
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    language: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    transcript: str
    language: str
    confidence: float
    processing_time: float
    status: str = "success"


class SynthesisRequest(BaseModel):
    """Request model for speech synthesis."""
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None)
) -> TranscriptionResponse:
    """
    Transcribe audio file to text.
    
    Args:
        request: FastAPI request object
        audio: Audio file to transcribe
        language: Language code for transcription
        
    Returns:
        TranscriptionResponse: Transcription result
    """
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        if not voice_processor:
            raise HTTPException(status_code=500, detail="Voice processor not available")
        
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file type")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Validate file size
        if len(audio_data) > voice_processor.settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Audio file too large")
        
        # Get file format
        file_format = audio.filename.split('.')[-1].lower() if audio.filename else "wav"
        
        # Transcribe audio
        result = await voice_processor.transcribe_audio(
            audio_data=audio_data,
            language=language,
            format=file_format
        )
        
        if result["status"] == "failed":
            raise HTTPException(status_code=500, detail=result.get("error", "Transcription failed"))
        
        logger.info(f"Transcribed audio file: {audio.filename}")
        
        return TranscriptionResponse(
            transcript=result["transcript"],
            language=result["language"],
            confidence=result["confidence"],
            processing_time=result["processing_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech(
    request: Request,
    synthesis_request: SynthesisRequest
) -> Response:
    """
    Synthesize speech from text.
    
    Args:
        request: FastAPI request object
        synthesis_request: Synthesis request data
        
    Returns:
        Response: Audio file response
    """
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        if not voice_processor:
            raise HTTPException(status_code=500, detail="Voice processor not available")
        
        # Synthesize speech
        result = await voice_processor.synthesize_speech(
            text=synthesis_request.text,
            voice=synthesis_request.voice,
            speed=synthesis_request.speed
        )
        
        if result["status"] == "failed":
            raise HTTPException(status_code=500, detail=result.get("error", "Synthesis failed"))
        
        logger.info(f"Synthesized speech for text: {synthesis_request.text[:50]}...")
        
        # Return audio response
        return Response(
            content=result["audio_data"],
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.post("/detect-voice-activity")
async def detect_voice_activity(
    request: Request,
    audio: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Detect voice activity in audio file.
    
    Args:
        request: FastAPI request object
        audio: Audio file to analyze
        
    Returns:
        Dict containing voice activity detection result
    """
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        if not voice_processor:
            raise HTTPException(status_code=500, detail="Voice processor not available")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Detect voice activity
        has_voice = await voice_processor.detect_voice_activity(audio_data)
        
        return {
            "filename": audio.filename,
            "has_voice_activity": has_voice,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error detecting voice activity: {e}")
        raise HTTPException(status_code=500, detail=f"Voice activity detection failed: {str(e)}")


@router.post("/preprocess")
async def preprocess_audio(
    request: Request,
    audio: UploadFile = File(...),
    target_sample_rate: Optional[int] = Form(None)
) -> Response:
    """
    Preprocess audio for better quality.
    
    Args:
        request: FastAPI request object
        audio: Audio file to preprocess
        target_sample_rate: Target sample rate
        
    Returns:
        Response: Preprocessed audio file
    """
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        if not voice_processor:
            raise HTTPException(status_code=500, detail="Voice processor not available")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Preprocess audio
        processed_audio = await voice_processor.preprocess_audio(
            audio_data=audio_data,
            target_sr=target_sample_rate
        )
        
        logger.info(f"Preprocessed audio file: {audio.filename}")
        
        # Return preprocessed audio
        return Response(
            content=processed_audio,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=preprocessed_{audio.filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error preprocessing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Audio preprocessing failed: {str(e)}")


@router.get("/capabilities")
async def get_capabilities(request: Request) -> Dict[str, Any]:
    """
    Get voice processing capabilities.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict containing capabilities information
    """
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        if not voice_processor:
            raise HTTPException(status_code=500, detail="Voice processor not available")
        
        status = await voice_processor.get_status()
        
        return {
            "capabilities": {
                "speech_to_text": {
                    "available": status["components"]["whisper"]["available"],
                    "model": status["components"]["whisper"]["model"],
                    "device": status["components"]["whisper"]["device"]
                },
                "text_to_speech": {
                    "available": status["components"]["tts"]["available"],
                    "enabled": status["components"]["tts"]["enabled"]
                },
                "voice_activity_detection": {
                    "available": status["components"]["vad"]["available"],
                    "enabled": status["components"]["vad"]["enabled"]
                },
                "audio_preprocessing": True,
                "real_time_processing": True,
                "websocket_streaming": True
            },
            "supported_formats": ["wav", "mp3", "m4a", "ogg", "flac"],
            "supported_languages": [
                "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
                "ar", "hi", "nl", "pl", "tr", "sv", "da", "no", "fi"
            ],
            "limits": {
                "max_file_size_mb": 25,
                "max_audio_length_seconds": 30,
                "processing_timeout_seconds": 30
            },
            "statistics": status["statistics"]
        }
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.get("/statistics")
async def get_statistics(request: Request) -> Dict[str, Any]:
    """
    Get voice processing statistics.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict containing processing statistics
    """
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        if not voice_processor:
            raise HTTPException(status_code=500, detail="Voice processor not available")
        
        status = await voice_processor.get_status()
        
        return {
            "statistics": status["statistics"],
            "uptime_seconds": status["uptime_seconds"],
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")