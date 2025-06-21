"""
Voice Processor - Core Voice Processing Logic

This module handles all voice processing operations including:
- Speech-to-text using OpenAI Whisper
- Text-to-speech synthesis
- Audio preprocessing and enhancement
- Voice activity detection
- Real-time audio streaming
"""

import asyncio
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import io

try:
    import whisper
except ImportError:
    whisper = None

try:
    import torch
except ImportError:
    torch = None

try:
    import librosa
    import soundfile as sf
except ImportError:
    librosa = None
    sf = None

try:
    import webrtcvad
except ImportError:
    webrtcvad = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from .config import settings

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Voice Processor handles all voice-related operations.
    """
    
    def __init__(self):
        """Initialize the Voice Processor."""
        self.whisper_model = None
        self.openai_client = None
        self.vad = None
        self.initialized = False
        self.start_time = datetime.utcnow()
        
        # Processing statistics
        self.stats = {
            "total_requests": 0,
            "successful_transcriptions": 0,
            "failed_transcriptions": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the voice processor and its components."""
        try:
            logger.info("Initializing Voice Processor...")
            
            # Create storage directories
            os.makedirs(settings.AUDIO_STORAGE_PATH, exist_ok=True)
            os.makedirs(settings.TEMP_STORAGE_PATH, exist_ok=True)
            
            # Initialize Whisper model
            await self._initialize_whisper()
            
            # Initialize OpenAI client for TTS
            if settings.TTS_ENABLED and settings.OPENAI_API_KEY:
                await self._initialize_openai()
            
            # Initialize Voice Activity Detection
            if settings.VAD_ENABLED:
                await self._initialize_vad()
            
            self.initialized = True
            logger.info("Voice Processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Voice Processor: {e}")
            raise
    
    async def _initialize_whisper(self) -> None:
        """Initialize Whisper model."""
        if whisper is None:
            logger.warning("Whisper not available, speech-to-text will be limited")
            return
        
        try:
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(
                None, 
                lambda: whisper.load_model(
                    settings.WHISPER_MODEL,
                    device=settings.WHISPER_DEVICE
                )
            )
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def _initialize_openai(self) -> None:
        """Initialize OpenAI client for TTS."""
        if AsyncOpenAI is None:
            logger.warning("OpenAI client not available, TTS will be limited")
            return
        
        try:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Test connection
            await self.openai_client.models.list()
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def _initialize_vad(self) -> None:
        """Initialize Voice Activity Detection."""
        if webrtcvad is None:
            logger.warning("WebRTC VAD not available, voice activity detection will be limited")
            return
        
        try:
            # Initialize VAD with aggressiveness level 2 (0-3)
            self.vad = webrtcvad.Vad(2)
            logger.info("Voice Activity Detection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {e}")
            # VAD is optional, so don't raise here
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        language: Optional[str] = None,
        format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text using Whisper.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code for transcription
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Dict containing transcription results
        """
        if not self.initialized:
            raise RuntimeError("Voice Processor not initialized")
        
        if self.whisper_model is None:
            raise RuntimeError("Whisper model not available")
        
        start_time = time.time()
        
        try:
            self.stats["total_requests"] += 1
            
            # Save audio to temporary file
            temp_file = await self._save_temp_audio(audio_data, format)
            
            try:
                # Transcribe using Whisper
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.whisper_model.transcribe(
                        temp_file,
                        language=language or settings.WHISPER_LANGUAGE,
                        fp16=False if settings.WHISPER_DEVICE == "cpu" else True
                    )
                )
                
                processing_time = time.time() - start_time
                self.stats["successful_transcriptions"] += 1
                self.stats["total_processing_time"] += processing_time
                self.stats["average_processing_time"] = (
                    self.stats["total_processing_time"] / self.stats["successful_transcriptions"]
                )
                
                logger.info(f"Transcription completed in {processing_time:.2f}s")
                
                return {
                    "transcript": result["text"].strip(),
                    "language": result.get("language", "unknown"),
                    "processing_time": processing_time,
                    "confidence": 1.0,  # Whisper doesn't provide confidence scores
                    "segments": result.get("segments", []),
                    "status": "success"
                }
                
            finally:
                # Clean up temporary file
                if settings.CLEANUP_TEMP_FILES:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                        
        except Exception as e:
            self.stats["failed_transcriptions"] += 1
            logger.error(f"Transcription failed: {e}")
            
            return {
                "transcript": "",
                "language": "unknown",
                "processing_time": time.time() - start_time,
                "confidence": 0.0,
                "segments": [],
                "status": "failed",
                "error": str(e)
            }
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using OpenAI TTS.
        
        Args:
            text: Text to synthesize
            voice: Voice to use for synthesis
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Dict containing synthesis results
        """
        if not self.initialized:
            raise RuntimeError("Voice Processor not initialized")
        
        if not settings.TTS_ENABLED or self.openai_client is None:
            raise RuntimeError("TTS not available")
        
        start_time = time.time()
        
        try:
            response = await self.openai_client.audio.speech.create(
                model=settings.TTS_MODEL,
                voice=voice or settings.TTS_VOICE,
                input=text,
                speed=speed or settings.TTS_SPEED
            )
            
            # Get audio data
            audio_data = response.content
            
            processing_time = time.time() - start_time
            
            logger.info(f"Speech synthesis completed in {processing_time:.2f}s")
            
            return {
                "audio_data": audio_data,
                "text": text,
                "voice": voice or settings.TTS_VOICE,
                "processing_time": processing_time,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            
            return {
                "audio_data": None,
                "text": text,
                "voice": voice or settings.TTS_VOICE,
                "processing_time": time.time() - start_time,
                "status": "failed",
                "error": str(e)
            }
    
    async def detect_voice_activity(self, audio_data: bytes) -> bool:
        """
        Detect if audio contains voice activity.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            True if voice activity detected, False otherwise
        """
        if self.vad is None:
            # Fallback to simple energy-based detection
            return await self._simple_vad(audio_data)
        
        try:
            # WebRTC VAD expects 16kHz, 16-bit PCM
            # Convert audio if necessary
            if librosa is not None:
                audio_array, sr = librosa.load(io.BytesIO(audio_data), sr=16000)
                audio_pcm = (audio_array * 32767).astype('int16').tobytes()
            else:
                audio_pcm = audio_data
            
            # Check voice activity
            return self.vad.is_speech(audio_pcm, 16000)
            
        except Exception as e:
            logger.warning(f"VAD detection failed: {e}")
            return await self._simple_vad(audio_data)
    
    async def _simple_vad(self, audio_data: bytes) -> bool:
        """Simple energy-based voice activity detection."""
        try:
            if librosa is not None:
                audio_array, sr = librosa.load(io.BytesIO(audio_data))
                energy = float(sum(audio_array ** 2) / len(audio_array))
                return energy > settings.SILENCE_THRESHOLD
            else:
                # Very basic fallback
                return len(audio_data) > 1000  # Assume voice if enough data
                
        except Exception:
            return True  # Assume voice activity if detection fails
    
    async def preprocess_audio(
        self, 
        audio_data: bytes, 
        target_sr: int = None
    ) -> bytes:
        """
        Preprocess audio for better quality.
        
        Args:
            audio_data: Raw audio bytes
            target_sr: Target sample rate
            
        Returns:
            Preprocessed audio bytes
        """
        if librosa is None or sf is None:
            logger.warning("Audio preprocessing libraries not available")
            return audio_data
        
        try:
            # Load audio
            audio_array, sr = librosa.load(io.BytesIO(audio_data))
            
            # Resample if needed
            if target_sr and sr != target_sr:
                audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
            
            # Normalize audio
            audio_array = librosa.util.normalize(audio_array)
            
            # Apply noise reduction (basic)
            audio_array = librosa.effects.preemphasis(audio_array)
            
            # Convert back to bytes
            with io.BytesIO() as buffer:
                sf.write(buffer, audio_array, sr, format='WAV')
                return buffer.getvalue()
                
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}")
            return audio_data
    
    async def _save_temp_audio(self, audio_data: bytes, format: str) -> str:
        """Save audio data to temporary file."""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{format}",
            dir=settings.TEMP_STORAGE_PATH
        )
        
        with temp_file as f:
            f.write(audio_data)
        
        return temp_file.name
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the voice processor."""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "initialized": self.initialized,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "components": {
                "whisper": {
                    "available": self.whisper_model is not None,
                    "model": settings.WHISPER_MODEL,
                    "device": settings.WHISPER_DEVICE
                },
                "tts": {
                    "available": self.openai_client is not None,
                    "enabled": settings.TTS_ENABLED
                },
                "vad": {
                    "available": self.vad is not None,
                    "enabled": settings.VAD_ENABLED
                }
            },
            "statistics": self.stats,
            "health": "healthy" if self.initialized else "unhealthy"
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up Voice Processor...")
        
        # Clean up temporary files
        if settings.CLEANUP_TEMP_FILES:
            try:
                temp_path = Path(settings.TEMP_STORAGE_PATH)
                for file in temp_path.glob("*"):
                    if file.is_file():
                        file.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp files: {e}")
        
        # Reset state
        self.initialized = False
        self.whisper_model = None
        self.openai_client = None
        self.vad = None
        
        logger.info("Voice Processor cleanup completed")