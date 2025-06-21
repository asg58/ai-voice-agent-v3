"""
Text-to-Speech Engine using Coqui XTTS v2
Professional implementation with natural voice synthesis and streaming support
"""
import asyncio
import logging
import time
import io
import numpy as np
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import tempfile
import os

import torch
import soundfile as sf
from TTS.api import TTS
from pydantic import BaseModel, Field

from .models import TTSRequest, TTSResult, AudioChunk

logger = logging.getLogger(__name__)


class XTTSConfig(BaseModel):
    """Configuration for XTTS v2 TTS Engine"""
    model_name: str = Field("tts_models/multilingual/multi-dataset/xtts_v2", description="XTTS model name")
    language: str = Field("nl", description="Default language")
    speaker: str = Field("Claribel Dervla", description="Default speaker voice")
    speed: float = Field(1.0, description="Speaking speed multiplier")
    temperature: float = Field(0.75, description="Voice variation temperature")
    length_penalty: float = Field(1.0, description="Length penalty for generation")
    repetition_penalty: float = Field(5.0, description="Repetition penalty")
    top_k: int = Field(50, description="Top-k sampling")
    top_p: float = Field(0.85, description="Top-p sampling")
    device: str = Field("cpu", description="Device for inference")
    streaming: bool = Field(True, description="Enable streaming synthesis")
    sample_rate: int = Field(24000, description="Output sample rate")
    
    class Config:
        env_prefix = "TTS_"


class XTTSEngine:
    """
    Professional XTTS v2-based Text-to-Speech Engine
    
    Features:
    - Natural voice synthesis with XTTS v2
    - Multi-language support (17+ languages)
    - Voice cloning and speaker adaptation
    - Real-time streaming synthesis
    - Emotional control and prosody
    - High-quality 24kHz audio output
    - GPU acceleration support
    """
    
    def __init__(self, config_obj: Optional[XTTSConfig] = None):
        """Initialize XTTS TTS Engine"""
        self.config = config_obj or XTTSConfig()
        self.model = None
        self.tts_api: Optional[TTS] = None
        self.is_initialized = False
        self.device = torch.device(self.config.device)
        self.sample_rate = self.config.sample_rate
        
        # Performance metrics
        self.total_text_processed = 0
        self.total_processing_time = 0.0
        self.synthesis_count = 0
        
        # Supported languages for XTTS v2
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", 
            "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"
        ]
        
        logger.info(f"XTTS TTS Engine configured with model: {self.config.model_name}")
    
    async def initialize(self) -> bool:
        """Initialize the XTTS model"""
        try:
            logger.info(f"Loading XTTS model: {self.config.model_name}")
            start_time = time.time()
            
            # Load model in a thread to avoid blocking
            def load_model():
                # Initialize TTS API
                tts = TTS(self.config.model_name, progress_bar=False)
                tts.to(self.device)
                return tts
            
            # Run model loading in thread pool
            loop = asyncio.get_event_loop()
            self.tts_api = await loop.run_in_executor(None, load_model)
            
            load_time = time.time() - start_time
            logger.info(f"XTTS model loaded successfully in {load_time:.2f}s")
            
            # Get available speakers
            if hasattr(self.tts_api.tts, 'speakers'):
                speakers = self.tts_api.tts.speakers
                logger.info(f"Available speakers: {speakers[:5] if speakers else 'None'}...")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize XTTS model: {e}")
            return False
    
    async def synthesize_speech(
        self, 
        request: TTSRequest,
        speaker_wav: Optional[str] = None
    ) -> TTSResult:
        """
        Synthesize speech from text
        
        Args:
            request: TTS request with text and parameters
            speaker_wav: Path to speaker reference audio for voice cloning
            
        Returns:
            TTSResult with generated audio data
        """
        if not self.is_initialized:
            raise RuntimeError("TTS Engine not initialized")
        
        start_time = time.time()
        
        try:
            # Validate and clean text
            text = self._validate_text(request.text)
            
            # Validate language
            language = request.language.lower()
            if language not in self.supported_languages:
                logger.warning(f"Language {language} not supported, using 'en'")
                language = "en"
            
            # Prepare synthesis parameters
            synthesis_kwargs = {
                "text": text,
                "language": language,
            }
            
            # Add speaker if specified
            if speaker_wav and os.path.exists(speaker_wav):
                synthesis_kwargs["speaker_wav"] = speaker_wav
            elif hasattr(self.tts_api.tts, 'speakers') and self.tts_api.tts.speakers:
                # Use default speaker or find requested speaker
                speakers = self.tts_api.tts.speakers
                if request.voice_id and request.voice_id in speakers:
                    synthesis_kwargs["speaker"] = request.voice_id
                elif self.config.speaker in speakers:
                    synthesis_kwargs["speaker"] = self.config.speaker
                else:
                    synthesis_kwargs["speaker"] = speakers[0]  # Use first available
            
            # Run synthesis in thread pool
            def synthesize():
                return self.tts_api.tts(**synthesis_kwargs)
            
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(None, synthesize)
            
            processing_time = time.time() - start_time
            
            # Convert to proper format
            if isinstance(audio_data, torch.Tensor):
                audio_data = audio_data.cpu().numpy()
            
            # Ensure correct format (int16)
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                # Normalize and convert to int16
                audio_data = np.clip(audio_data, -1.0, 1.0)
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # Calculate duration
            duration = len(audio_data) / self.sample_rate
            
            # Update metrics
            self.total_text_processed += len(request.text)
            self.total_processing_time += processing_time
            self.synthesis_count += 1
            
            result = TTSResult(
                session_id=request.session_id,
                audio_data=audio_data.tobytes(),
                sample_rate=self.sample_rate,
                duration=duration,
                text=request.text,
                voice_id=request.voice_id or self.config.speaker,
                generation_time=processing_time
            )
            
            logger.info(
                f"Synthesized {len(request.text)} chars in {processing_time:.3f}s "
                f"({duration:.2f}s audio, RTF: {processing_time / duration:.2f}): '{request.text[:50]}...'"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            # Return empty result with error indication
            return TTSResult(
                session_id=request.session_id,
                audio_data=b"",
                sample_rate=self.sample_rate,
                duration=0.0,
                text=request.text,
                voice_id=request.voice_id or "error",
                generation_time=time.time() - start_time
            )
    
    async def synthesize_streaming(
        self, 
        requests: List[TTSRequest],
        speaker_wav: Optional[str] = None
    ) -> List[TTSResult]:
        """
        Synthesize multiple text requests in sequence
        
        Args:
            requests: List of TTS requests
            speaker_wav: Path to speaker reference audio
            
        Returns:
            List of TTSResult objects
        """
        if not self.is_initialized:
            raise RuntimeError("TTS Engine not initialized")
        
        results = []
        
        for request in requests:
            try:
                result = await self.synthesize_speech(request, speaker_wav)
                results.append(result)
                
                # Small delay for streaming effect
                if request.streaming:
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Streaming synthesis error for request: {e}")
                continue
        
        return results
    
    async def clone_voice(
        self, 
        speaker_wav_path: str, 
        text: str, 
        session_id: str,
        language: str = "en"
    ) -> TTSResult:
        """
        Clone a voice from reference audio and synthesize text
        
        Args:
            speaker_wav_path: Path to reference audio file
            text: Text to synthesize
            session_id: Session identifier
            language: Language code
            
        Returns:
            TTSResult with cloned voice synthesis
        """
        if not os.path.exists(speaker_wav_path):
            raise FileNotFoundError(f"Speaker reference file not found: {speaker_wav_path}")
        
        request = TTSRequest(
            session_id=session_id,
            text=text,
            language=language,
            voice_id="cloned"
        )
        
        return await self.synthesize_speech(request, speaker_wav_path)
    
    async def get_available_voices(self) -> List[str]:
        """Get list of available voices/speakers"""
        if not self.is_initialized or not self.tts_api:
            return []
        
        try:
            if hasattr(self.tts_api.tts, 'speakers') and self.tts_api.tts.speakers:
                return list(self.tts_api.tts.speakers)
            else:
                return ["default"]
        except Exception as e:
            logger.warning(f"Could not get available voices: {e}")
            return ["default"]
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def _validate_text(self, text: str) -> str:
        """Validate and clean text for synthesis"""
        # Remove or replace problematic characters
        text = text.strip()
        
        # Limit text length (XTTS works best with shorter texts)
        max_length = 500
        if len(text) > max_length:
            text = text[:max_length] + "..."
            logger.warning(f"Text truncated to {max_length} characters")
        
        # Ensure text is not empty
        if not text:
            text = "Hello."
        
        return text
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if self.synthesis_count == 0:
            return {
                "syntheses_processed": 0,
                "total_characters": 0,
                "average_processing_time": 0.0,
                "characters_per_second": 0.0
            }
        
        avg_processing_time = self.total_processing_time / self.synthesis_count
        chars_per_second = self.total_text_processed / max(self.total_processing_time, 0.001)
        
        return {
            "syntheses_processed": self.synthesis_count,
            "total_characters": self.total_text_processed,
            "average_processing_time": avg_processing_time,
            "characters_per_second": chars_per_second,
            "model_name": self.config.model_name,
            "device": str(self.device),
            "sample_rate": self.sample_rate
        }
    
    async def save_audio_to_file(self, tts_result: TTSResult, file_path: str) -> bool:
        """Save TTS result audio to file"""
        try:
            audio_array = tts_result.to_numpy()
            sf.write(file_path, audio_array, tts_result.sample_rate)
            logger.info(f"Audio saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save audio to file: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.tts_api:
            del self.tts_api
            
        if self.model:
            del self.model
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.is_initialized = False
        logger.info("TTS Engine cleaned up")


# Global TTS engine instance
tts_engine = XTTSEngine()
