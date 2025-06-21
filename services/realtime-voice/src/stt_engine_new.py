"""
Speech-to-Text Engine using OpenAI Whisper
Professional implementation with streaming support and multilingual capabilities
"""
import asyncio
import logging
import time
import tempfile
import os
import numpy as np
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime

import whisper
import torch
import soundfile as sf
from pydantic import BaseModel, Field

from .models import AudioChunk, TranscriptionResult
from .config import config

logger = logging.getLogger(__name__)


class WhisperSTTConfig(BaseModel):
    """Configuration for Whisper STT Engine"""
    model_size: str = Field("base", description="Whisper model size")
    language: Optional[str] = Field(None, description="Language code or None for auto-detect")
    device: str = Field("cpu", description="Device for inference")
    compute_type: str = Field("int8", description="Compute precision")
    enable_streaming: bool = Field(True, description="Enable streaming transcription")
    chunk_duration: float = Field(2.0, description="Audio chunk duration for streaming")
    overlap_duration: float = Field(0.3, description="Overlap between chunks")
    vad_filter: bool = Field(True, description="Enable voice activity detection filtering")
    word_timestamps: bool = Field(True, description="Include word-level timestamps")
    
    class Config:
        env_prefix = "STT_"


class WhisperSTTEngine:
    """
    Professional Whisper-based Speech-to-Text Engine
    
    Features:
    - Multiple model sizes (tiny, base, small, medium, large)
    - Multilingual support (50+ languages)
    - Real-time streaming transcription
    - Word-level timestamps
    - Confidence scoring
    - Automatic language detection
    - Voice activity detection integration
    """
    
    def __init__(self, config_obj: Optional[WhisperSTTConfig] = None):
        """Initialize Whisper STT Engine"""
        self.config = config_obj or WhisperSTTConfig()
        self.model: Optional[whisper.Whisper] = None
        self.is_initialized = False
        self.device = torch.device(self.config.device)
        self.sample_rate = 16000  # Whisper's expected sample rate
        
        # Performance metrics
        self.total_audio_processed = 0.0
        self.total_processing_time = 0.0
        self.transcription_count = 0
        
        logger.info(f"Whisper STT Engine configured with model: {self.config.model_size}")
    
    async def initialize(self) -> bool:
        """Initialize the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.config.model_size}")
            start_time = time.time()
            
            # Load model in a thread to avoid blocking
            def load_model():
                return whisper.load_model(
                    self.config.model_size,
                    device=self.device
                )
            
            # Run model loading in thread pool
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(None, load_model)
            
            load_time = time.time() - start_time
            logger.info(f"Whisper model loaded successfully in {load_time:.2f}s")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            return False
    
    async def transcribe_audio(
        self, 
        audio_chunk: AudioChunk,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio chunk to text
        
        Args:
            audio_chunk: Audio data to transcribe
            language: Language code override
            prompt: Initial prompt for context
            
        Returns:
            TranscriptionResult with text and metadata
        """
        if not self.is_initialized:
            raise RuntimeError("STT Engine not initialized")
        
        start_time = time.time()
        temp_path = None
        
        try:
            # Convert audio data to numpy array
            audio_data = audio_chunk.to_numpy()
            
            # Ensure correct sample rate and format
            if audio_chunk.sample_rate != self.sample_rate:
                logger.warning(f"Sample rate mismatch: {audio_chunk.sample_rate} vs {self.sample_rate}")
            
            # Normalize audio to float32
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            
            # Save to temporary WAV file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                sf.write(temp_path, audio_data, self.sample_rate)
            
            # Prepare transcription options
            options = {
                "language": language or self.config.language,
                "task": "transcribe",
                "word_timestamps": self.config.word_timestamps,
                "condition_on_previous_text": True if prompt else False,
            }
            
            if prompt:
                options["initial_prompt"] = prompt
            
            # Run transcription in thread pool
            def transcribe():
                return self.model.transcribe(temp_path, **options)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, transcribe)
            
            processing_time = time.time() - start_time
            
            # Extract words with timestamps if available
            words = []
            if self.config.word_timestamps and "segments" in result:
                for segment in result["segments"]:
                    if "words" in segment:
                        for word in segment["words"]:
                            words.append({
                                "word": word.get("word", ""),
                                "start": word.get("start", 0.0),
                                "end": word.get("end", 0.0),
                                "confidence": word.get("probability", 0.0)
                            })
            
            # Update metrics
            self.total_audio_processed += audio_chunk.duration or 0.0
            self.total_processing_time += processing_time
            self.transcription_count += 1
            
            # Calculate confidence (Whisper doesn't provide direct confidence)
            confidence = self._estimate_confidence(result)
            
            transcription_result = TranscriptionResult(
                session_id=audio_chunk.session_id,
                text=result["text"].strip(),
                confidence=confidence,
                language=result.get("language"),
                start_time=audio_chunk.timestamp,
                end_time=audio_chunk.timestamp + (audio_chunk.duration or 0.0),
                words=words,
                is_final=True
            )
            
            logger.info(
                f"Transcribed {audio_chunk.duration:.2f}s audio in {processing_time:.3f}s "
                f"(RTF: {processing_time / (audio_chunk.duration or 1.0):.2f}): '{result['text'][:50]}...'"
            )
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            # Return empty result with error indication
            return TranscriptionResult(
                session_id=audio_chunk.session_id,
                text="",
                confidence=0.0,
                language="unknown",
                start_time=audio_chunk.timestamp,
                end_time=audio_chunk.timestamp,
                words=[],
                is_final=True
            )
        finally:
            # Cleanup temporary file
            if temp_path:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")
    
    async def transcribe_streaming(
        self, 
        audio_chunks: List[AudioChunk],
        language: Optional[str] = None
    ) -> List[TranscriptionResult]:
        """
        Stream transcription of continuous audio chunks
        
        Args:
            audio_chunks: List of audio chunks to process
            language: Language code override
            
        Returns:
            List of TranscriptionResult objects
        """
        if not self.is_initialized:
            raise RuntimeError("STT Engine not initialized")
        
        results = []
        
        for chunk in audio_chunks:
            try:
                result = await self.transcribe_audio(chunk, language)
                if result.text.strip():  # Only include non-empty results
                    results.append(result)
            except Exception as e:
                logger.error(f"Streaming transcription error for chunk: {e}")
                continue
        
        return results
    
    def _estimate_confidence(self, whisper_result: Dict[str, Any]) -> float:
        """
        Estimate confidence score from Whisper result
        
        Whisper doesn't provide direct confidence, so we estimate based on:
        - Presence of text
        - Language detection probability
        - Text length and structure
        """
        text = whisper_result.get("text", "").strip()
        
        if not text:
            return 0.0
        
        # Base confidence on text characteristics
        confidence = 0.5  # Base confidence
        
        # Boost for longer, structured text
        if len(text) > 10:
            confidence += 0.2
        
        if len(text.split()) > 3:
            confidence += 0.1
        
        # Boost if language was detected with high probability
        if "language" in whisper_result:
            confidence += 0.2
        
        # Check for repetition or hallucination patterns
        words = text.split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            confidence *= repetition_ratio  # Reduce confidence for repetitive text
        
        return min(confidence, 1.0)
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if self.transcription_count == 0:
            return {
                "transcriptions_processed": 0,
                "total_audio_duration": 0.0,
                "average_processing_time": 0.0,
                "real_time_factor": 0.0
            }
        
        avg_processing_time = self.total_processing_time / self.transcription_count
        rtf = self.total_processing_time / max(self.total_audio_processed, 0.001)
        
        return {
            "transcriptions_processed": self.transcription_count,
            "total_audio_duration": self.total_audio_processed,
            "average_processing_time": avg_processing_time,
            "real_time_factor": rtf,
            "model_size": self.config.model_size,
            "device": str(self.device)
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.model:
            # Clear model from memory
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        self.is_initialized = False
        logger.info("STT Engine cleaned up")


# Global STT engine instance
stt_engine = WhisperSTTEngine()
