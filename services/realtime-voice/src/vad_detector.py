"""
Voice Activity Detection for Real-time Conversation
Detects when user starts/stops speaking for natural conversation flow
"""
import asyncio
import logging
from typing import Optional, Callable
import numpy as np
import torch
from collections import deque
import time

from .config import config
from .models import VoiceActivityDetection, AudioChunk

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """Real-time Voice Activity Detection using Silero VAD"""
    
    def __init__(self):
        self.model = None
        self.sample_rate = config.audio.sample_rate
        self.threshold = config.vad.threshold
        self.min_speech_duration = config.vad.min_speech_duration
        self.max_speech_duration = config.vad.max_speech_duration
        
        # State tracking
        self.is_speech_active = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 2))  # 2 second buffer
          # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_speech_detected: Optional[Callable] = None
        
        logger.info("Voice Activity Detector initialized")

    async def initialize(self):
        """Initialize the VAD model with improved error handling"""
        try:
            # Import dependencies
            import torch
            torch.set_num_threads(1)  # Optimize for single threaded usage
            
            # Try to load the model from different sources
            model_sources = [
                'snakers4/silero-vad',
                'snakers4/silero-vad:silero_vad'
            ]
            
            model_loaded = False
            for source in model_sources:
                try:
                    logger.info(f"Attempting to load VAD model from: {source}")
                    self.model, utils = torch.hub.load(
                        repo_or_dir=source,
                        model='silero_vad',
                        force_reload=False,
                        trust_repo=True,
                        onnx=False
                    )
                    model_loaded = True
                    break
                except Exception as source_error:
                    logger.warning(f"Failed to load from {source}: {source_error}")
                    continue
            
            if not model_loaded:
                raise Exception("Could not load VAD model from any source")
            
            # Extract utility functions
            self.get_speech_timestamps = utils[0]
            self.save_audio = utils[1]
            self.read_audio = utils[2]
            self.VADIterator = utils[3]
            self.collect_chunks = utils[4]
            
            # Initialize VAD iterator for streaming
            self.vad_iterator = self.VADIterator(
                model=self.model,
                threshold=self.threshold,
                sampling_rate=self.sample_rate,
                min_silence_duration_ms=300,
                speech_pad_ms=100
            )
            
            logger.info("Silero VAD model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VAD model: {e}")
            # Fallback to simple energy-based VAD
            self.model = None
            self.vad_iterator = None
            logger.warning("Using fallback energy-based VAD")
        
        self.is_initialized = True
    
    async def process_audio(self, audio_chunk: AudioChunk) -> Optional[VoiceActivityDetection]:
        """Process audio chunk and detect voice activity"""
        
        audio_data = audio_chunk.to_numpy()
        current_time = audio_chunk.timestamp
        
        # Add to buffer
        self.audio_buffer.extend(audio_data)
        
        # Detect speech
        if self.model is not None:
            return await self._detect_with_silero(audio_data, current_time, audio_chunk.session_id)
        else:
            return await self._detect_with_energy(audio_data, current_time, audio_chunk.session_id)
    
    async def _detect_with_silero(self, audio_data: np.ndarray, timestamp: float, session_id: str) -> Optional[VoiceActivityDetection]:
        """Detect speech using Silero VAD model"""
        
        try:
            # Ensure audio is float32 and normalized
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_float)
            
            # Get VAD prediction
            speech_dict = self.vad_iterator(audio_tensor, return_seconds=True)
            
            is_speech = speech_dict is not None
            confidence = 1.0 if is_speech else 0.0
            
            # Handle speech state changes
            await self._handle_speech_detection(is_speech, timestamp, session_id)
            
            # Calculate audio level
            audio_level = float(np.sqrt(np.mean(audio_data.astype(np.float64) ** 2)))
            
            return VoiceActivityDetection(
                session_id=session_id,
                is_speech=is_speech,
                confidence=confidence,
                start_time=timestamp,
                audio_level=audio_level
            )
            
        except Exception as e:
            logger.error(f"Error in Silero VAD detection: {e}")
            # Fallback to energy detection
            return await self._detect_with_energy(audio_data, timestamp, session_id)
    
    async def _detect_with_energy(self, audio_data: np.ndarray, timestamp: float, session_id: str) -> VoiceActivityDetection:
        """Fallback energy-based voice activity detection"""
        
        # Calculate RMS energy
        rms_energy = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        
        # Normalize to 0-1 range (approximate)
        audio_level = min(rms_energy / 5000.0, 1.0)
        
        # Simple threshold-based detection
        energy_threshold = 0.01  # Adjust based on testing
        is_speech = audio_level > energy_threshold
        confidence = min(audio_level / energy_threshold, 1.0) if is_speech else 0.0
        
        # Handle speech state changes
        await self._handle_speech_detection(is_speech, timestamp, session_id)
        
        return VoiceActivityDetection(
            session_id=session_id,
            is_speech=is_speech,
            confidence=confidence,
            start_time=timestamp,
            audio_level=audio_level
        )
    
    async def _handle_speech_detection(self, is_speech: bool, timestamp: float, session_id: str):
        """Handle speech state changes and trigger callbacks"""
        
        # Speech started
        if is_speech and not self.is_speech_active:
            self.is_speech_active = True
            self.speech_start_time = timestamp
            self.last_speech_time = timestamp
            
            logger.debug(f"Speech started for session {session_id}")
            
            if self.on_speech_start:
                await self.on_speech_start(session_id, timestamp)
        
        # Speech continuing
        elif is_speech and self.is_speech_active:
            self.last_speech_time = timestamp
            
            if self.on_speech_detected:
                await self.on_speech_detected(session_id, timestamp)
            
            # Check for max speech duration
            if (timestamp - self.speech_start_time) > self.max_speech_duration:
                logger.warning(f"Speech duration exceeded maximum for session {session_id}")
                await self._end_speech(session_id, timestamp)
        
        # Speech ended
        elif not is_speech and self.is_speech_active:
            # Check minimum speech duration
            speech_duration = timestamp - self.speech_start_time
            if speech_duration >= self.min_speech_duration:
                await self._end_speech(session_id, timestamp)
            else:
                logger.debug(f"Speech too short ({speech_duration:.2f}s), ignoring")
    
    async def _end_speech(self, session_id: str, timestamp: float):
        """End current speech and trigger callback"""
        
        if not self.is_speech_active:
            return
        
        speech_duration = timestamp - self.speech_start_time
        logger.debug(f"Speech ended for session {session_id}, duration: {speech_duration:.2f}s")
        
        self.is_speech_active = False
        
        if self.on_speech_end:
            await self.on_speech_end(session_id, self.speech_start_time, timestamp)
        
        self.speech_start_time = None
    
    def set_callbacks(self, 
                     on_speech_start: Optional[Callable] = None,
                     on_speech_end: Optional[Callable] = None,
                     on_speech_detected: Optional[Callable] = None):
        """Set callback functions for speech events"""
        
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
        self.on_speech_detected = on_speech_detected
        
        logger.info("VAD callbacks configured")
    
    def get_speech_segments(self, audio_data: np.ndarray) -> list:
        """Get speech segments from audio data (batch processing)"""
        
        if self.model is None:
            logger.warning("VAD model not available for batch processing")
            return []
        
        try:
            # Ensure audio is float32 and normalized
            audio_float = audio_data.astype(np.float32) / 32768.0
            audio_tensor = torch.from_numpy(audio_float)
            
            # Get speech timestamps
            speech_timestamps = self.get_speech_timestamps(
                audio_tensor, 
                self.model,
                sampling_rate=self.sample_rate,
                threshold=self.threshold,
                min_speech_duration_ms=int(self.min_speech_duration * 1000),
                return_seconds=True
            )
            
            return speech_timestamps
            
        except Exception as e:
            logger.error(f"Error getting speech segments: {e}")
            return []
    
    def reset_state(self):
        """Reset VAD state"""
        self.is_speech_active = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.audio_buffer.clear()
        
        if hasattr(self, 'vad_iterator') and self.vad_iterator:
            self.vad_iterator.reset_states()
        
        logger.debug("VAD state reset")
    
    def get_state(self) -> dict:
        """Get current VAD state"""
        return {
            "is_speech_active": self.is_speech_active,
            "speech_start_time": self.speech_start_time,
            "last_speech_time": self.last_speech_time,
            "buffer_size": len(self.audio_buffer),
            "threshold": self.threshold
        }
    
    def update_threshold(self, new_threshold: float):
        """Update VAD threshold dynamically"""
        self.threshold = max(0.0, min(1.0, new_threshold))
        
        if hasattr(self, 'vad_iterator') and self.vad_iterator:
            self.vad_iterator.threshold = self.threshold
        
        logger.info(f"VAD threshold updated to {self.threshold}")


class InterruptionDetector:
    """Detects when user interrupts AI speech"""
    
    def __init__(self, vad: VoiceActivityDetector):
        self.vad = vad
        self.ai_speaking = False
        self.ai_speech_start_time = None
        self.interruption_callbacks = []
        
        # Set VAD callbacks for interruption detection
        self.vad.set_callbacks(
            on_speech_start=self._on_user_speech_start,
            on_speech_end=self._on_user_speech_end
        )
        
        logger.info("Interruption Detector initialized")
    
    async def _on_user_speech_start(self, session_id: str, timestamp: float):
        """Handle user speech start - potential interruption"""
        
        if self.ai_speaking:
            # User interrupted AI
            interruption_data = {
                "session_id": session_id,
                "timestamp": timestamp,
                "ai_speech_start": self.ai_speech_start_time,
                "interruption_delay": timestamp - self.ai_speech_start_time if self.ai_speech_start_time else 0
            }
            
            logger.info(f"User interruption detected for session {session_id}")
            
            # Trigger interruption callbacks
            for callback in self.interruption_callbacks:
                await callback(interruption_data)
    
    async def _on_user_speech_end(self, session_id: str, start_time: float, end_time: float):
        """Handle user speech end"""
        # Could be used for conversation flow management
        pass
    
    def start_ai_speech(self, session_id: str):
        """Mark that AI started speaking"""
        self.ai_speaking = True
        self.ai_speech_start_time = time.time()
        logger.debug(f"AI speech started for session {session_id}")
    
    def stop_ai_speech(self, session_id: str):
        """Mark that AI stopped speaking"""
        self.ai_speaking = False
        self.ai_speech_start_time = None
        logger.debug(f"AI speech stopped for session {session_id}")
    
    def add_interruption_callback(self, callback: Callable):
        """Add callback for interruption events"""
        self.interruption_callbacks.append(callback)
        logger.info("Interruption callback added")


# Global VAD instance
vad_detector = VoiceActivityDetector()
