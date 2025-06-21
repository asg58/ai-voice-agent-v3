"""
Streaming Speech-to-Text Processor

Real-time audio processing with streaming transcription capabilities.
Integrates with VAD for speech detection and Whisper for transcription.
"""
import asyncio
import logging
import time
import numpy as np
from typing import Optional, Dict, Any, List, Callable, Tuple, AsyncGenerator
from collections import deque
import threading
import queue
import os
import tempfile

from src.config import settings
from src.models import AudioChunk, TranscriptionResult, VoiceActivityDetection
from src.core.audio.vad import VoiceActivityDetector
from src.core.audio.language_detection import language_detector
from src.core.audio.preprocessing import audio_preprocessor
from src.core.audio.accent_adaptation import accent_adaptation_manager
from src.core.audio.domain_specific_stt import domain_specific_stt
from src.core.audio.voice_verification import voice_verification
from src.core.audio.emotion_recognition import emotion_recognition

logger = logging.getLogger(__name__)


class StreamingSTTProcessor:
    """
    Streaming Speech-to-Text Processor
    
    Features:
    - Real-time audio processing with WebSocket streaming
    - Voice activity detection for speech segmentation
    - Continuous and incremental transcription
    - Configurable speech detection parameters
    - Automatic language detection
    - Noise filtering and audio preprocessing
    """
    
    def __init__(self, vad: Optional[VoiceActivityDetector] = None):
        """
        Initialize streaming STT processor
        
        Args:
            vad: Voice activity detector instance (optional)
        """
        self.vad = vad
        self.is_initialized = False
        self.processing_queue = asyncio.Queue()
        self.processing_task = None
        self.active_sessions = {}
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.sample_rate = self.config.audio_sample_rate
        self.language = self.config.stt_language
        self.max_audio_length_sec = self.config.stt_max_audio_length
        self.min_speech_duration_sec = self.config.stt_min_speech_duration
        self.silence_threshold_sec = self.config.stt_silence_threshold
        
        # Performance metrics
        self.total_audio_processed = 0.0
        self.total_processing_time = 0.0
        self.transcription_count = 0
        
        logger.info("Streaming STT processor initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize streaming STT processor
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize VAD if not provided
            if self.vad is None:
                from src.core.audio.vad import VoiceActivityDetector
                self.vad = VoiceActivityDetector()
                await self.vad.initialize()
            
            # Initialize STT engine
            from src.core.audio.stt import stt_engine
            await stt_engine.initialize()
            
            # Initialize language detector
            await language_detector.initialize()
            
            # Initialize audio preprocessor
            await audio_preprocessor.initialize()
            
            # Initialize accent adaptation manager
            await accent_adaptation_manager.initialize()
            
            # Initialize domain-specific STT manager
            await domain_specific_stt.initialize()
            
            # Initialize voice verification manager
            await voice_verification.initialize()
            
            # Initialize emotion recognition manager
            await emotion_recognition.initialize()
            
            # Start processing task
            self.processing_task = asyncio.create_task(self._process_queue())
            
            self.is_initialized = True
            logger.info("Streaming STT processor initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize streaming STT processor: {e}")
            return False
    
    async def process_audio(self, audio_chunk: AudioChunk) -> Optional[TranscriptionResult]:
        """
        Process audio chunk and detect speech for transcription
        
        Args:
            audio_chunk: Audio chunk to process
            
        Returns:
            TranscriptionResult if speech detected and transcribed, None otherwise
        """
        if not self.is_initialized:
            logger.error("Streaming STT processor not initialized")
            return None
        
        try:
            session_id = audio_chunk.session_id
            
            # Create session state if it doesn't exist
            if session_id not in self.active_sessions:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.active_sessions[session_id]
            
            # Apply audio preprocessing
            processed_chunk = await audio_preprocessor.process_audio(audio_chunk)
            
            # Process audio with VAD
            vad_result = await self.vad.process_audio(processed_chunk)
            
            # Update session state with VAD result
            if vad_result:
                session_state["last_vad_result"] = vad_result
                session_state["last_activity"] = time.time()
                
                # Add audio to buffer if speech detected
                if vad_result.is_speech:
                    session_state["audio_buffer"].extend(audio_chunk.to_numpy())
                    session_state["speech_active"] = True
                    session_state["last_speech_time"] = time.time()
                    
                    # Update speech start time if not set
                    if session_state["speech_start_time"] is None:
                        session_state["speech_start_time"] = time.time()
                        logger.debug(f"Speech started for session {session_id}")
                
                # Check if speech ended (silence after speech)
                elif session_state["speech_active"]:
                    silence_duration = time.time() - session_state["last_speech_time"]
                    
                    if silence_duration > self.silence_threshold_sec:
                        # Speech ended, process the buffered audio
                        speech_duration = time.time() - session_state["speech_start_time"]
                        
                        if speech_duration >= self.min_speech_duration_sec:
                            logger.debug(f"Speech ended for session {session_id}, duration: {speech_duration:.2f}s")
                            
                            # Create audio chunk from buffer
                            audio_data = np.array(session_state["audio_buffer"], dtype=np.int16)
                            
                            # Limit audio length if too long
                            max_samples = int(self.max_audio_length_sec * self.sample_rate)
                            if len(audio_data) > max_samples:
                                logger.warning(f"Audio too long ({len(audio_data)/self.sample_rate:.2f}s), truncating to {self.max_audio_length_sec}s")
                                audio_data = audio_data[-max_samples:]
                            
                            # Create audio chunk for transcription
                            speech_chunk = AudioChunk(
                                session_id=session_id,
                                data=audio_data.tobytes(),
                                sample_rate=self.sample_rate,
                                channels=1,
                                timestamp=session_state["speech_start_time"],
                                duration=len(audio_data) / self.sample_rate
                            )
                            
                            # Add to processing queue
                            await self.processing_queue.put((session_id, speech_chunk))
                            
                            # Create preliminary result
                            return TranscriptionResult(
                                session_id=session_id,
                                text="",
                                confidence=0.0,
                                language=self.language,
                                start_time=session_state["speech_start_time"],
                                end_time=time.time(),
                                is_final=False
                            )
                        
                        # Reset speech state
                        self._reset_speech_state(session_id)
            
            return None
        
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
    
    async def _process_queue(self):
        """Process audio chunks in the queue"""
        logger.info("Starting audio processing queue")
        
        while True:
            try:
                # Get item from queue
                session_id, audio_chunk = await self.processing_queue.get()
                
                # Process audio chunk
                result = await self._transcribe_audio(audio_chunk)
                
                # Update session state with result
                if result and session_id in self.active_sessions:
                    session_state = self.active_sessions[session_id]
                    session_state["last_transcription"] = result
                    session_state["last_activity"] = time.time()
                    
                    # Call callback if registered
                    if session_state["transcription_callback"]:
                        try:
                            await session_state["transcription_callback"](result)
                        except Exception as e:
                            logger.error(f"Error in transcription callback: {e}")
                
                # Mark task as done
                self.processing_queue.task_done()
            
            except asyncio.CancelledError:
                logger.info("Audio processing queue cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error processing audio queue: {e}")
                continue
    
    async def _transcribe_audio(self, audio_chunk: AudioChunk) -> Optional[TranscriptionResult]:
        """
        Transcribe audio chunk
        
        Args:
            audio_chunk: Audio chunk to transcribe
            
        Returns:
            TranscriptionResult if successful, None otherwise
        """
        try:
            start_time = time.time()
            
            # Get STT engine
            from src.core.audio.stt import stt_engine
            
            # Get previous transcription for context
            session_id = audio_chunk.session_id
            previous_text = None
            
            if session_id in self.active_sessions:
                session_state = self.active_sessions[session_id]
                if session_state["last_transcription"]:
                    previous_text = session_state["last_transcription"].text
            
            # Get language for this session
            session_language = language_detector.get_session_language(session_id)
            
            # Transcribe audio
            result = await stt_engine.transcribe_audio(
                audio_chunk=audio_chunk,
                language=session_language,
                prompt=previous_text
            )
            
            # If we have a result, detect language from the transcription
            if result and result.text:
                # Detect language from transcribed text
                detected_lang, confidence = await language_detector.detect_language(
                    result.text, 
                    session_id=session_id
                )
                
                # Update result with detected language
                result.language = detected_lang
                
                # If detected language is different from session language with high confidence,
                # we might want to re-transcribe with the detected language
                if detected_lang != session_language and confidence > 0.8 and len(result.text) > 10:
                    logger.info(f"Re-transcribing with detected language: {detected_lang}")
                    
                    # Re-transcribe with detected language
                    new_result = await stt_engine.transcribe_audio(
                        audio_chunk=audio_chunk,
                        language=detected_lang,
                        prompt=previous_text
                    )
                    
                    if new_result and new_result.text:
                        new_result.language = detected_lang
                        result = new_result
            
            # Apply accent adaptation if we have a result
            if result and result.text:
                # Detect accent from transcription
                accent, confidence = await accent_adaptation_manager.detect_accent(result)
                
                # Apply accent adaptation
                result = await accent_adaptation_manager.process_transcription(result)
                
                # Apply domain-specific adaptations
                result = await domain_specific_stt.process_transcription(result)
                
                # Apply emotion recognition
                emotion_result = await emotion_recognition.recognize_emotion(audio_chunk, result)
                
                # Store emotion in result metadata
                if not result.metadata:
                    result.metadata = {}
                result.metadata["emotion"] = emotion_result
                
                # Update session emotion if available
                if session_id in self.active_sessions and emotion_result:
                    from src.core.session.manager import session_manager
                    session = session_manager.get_session(session_id)
                    if session:
                        session.current_emotion = emotion_result.get("emotion", "neutral")
                        session.emotion_score = emotion_result.get("score", 1.0)
                        if "all_scores" in emotion_result:
                            session.emotion_history.append({
                                "emotion": session.current_emotion,
                                "score": session.emotion_score,
                                "timestamp": time.time()
                            })
            
            # Update metrics
            processing_time = time.time() - start_time
            self.total_audio_processed += audio_chunk.duration or 0.0
            self.total_processing_time += processing_time
            self.transcription_count += 1
            
            logger.info(
                f"Transcribed {audio_chunk.duration:.2f}s audio in {processing_time:.3f}s "
                f"(RTF: {processing_time / (audio_chunk.duration or 1.0):.2f}): '{result.text[:50]}...' "
                f"[Language: {result.language}]"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    def register_transcription_callback(self, session_id: str, callback: Callable[[TranscriptionResult], None]):
        """
        Register callback for transcription results
        
        Args:
            session_id: Session ID
            callback: Callback function to call with transcription results
        """
        if session_id not in self.active_sessions:
            self._create_session_state(session_id)
        
        self.active_sessions[session_id]["transcription_callback"] = callback
        logger.debug(f"Registered transcription callback for session {session_id}")
    
    def _create_session_state(self, session_id: str):
        """
        Create session state
        
        Args:
            session_id: Session ID
        """
        self.active_sessions[session_id] = {
            "audio_buffer": deque(maxlen=int(self.max_audio_length_sec * self.sample_rate)),
            "speech_active": False,
            "speech_start_time": None,
            "last_speech_time": None,
            "last_vad_result": None,
            "last_transcription": None,
            "last_activity": time.time(),
            "transcription_callback": None
        }
    
    def _reset_speech_state(self, session_id: str):
        """
        Reset speech state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.active_sessions:
            session_state = self.active_sessions[session_id]
            session_state["speech_active"] = False
            session_state["speech_start_time"] = None
            session_state["last_speech_time"] = None
            session_state["audio_buffer"].clear()
    
    async def cleanup_session(self, session_id: str):
        """
        Clean up session resources
        
        Args:
            session_id: Session ID
        """
        if session_id in self.active_sessions:
            # Reset speech state
            self._reset_speech_state(session_id)
            
            # Remove session state
            del self.active_sessions[session_id]
            
            # Reset language detector session
            language_detector.reset_session(session_id)
            
            # Reset audio preprocessor session
            audio_preprocessor.reset_session(session_id)
            
            # Reset accent adaptation session
            accent_adaptation_manager.reset_session(session_id)
            
            # Reset domain-specific STT session
            domain_specific_stt.reset_session(session_id)
            
            # Reset voice verification session
            voice_verification.reset_session(session_id)
            
            # Reset emotion recognition session
            emotion_recognition.reset_session(session_id)
            
            logger.debug(f"Cleaned up session {session_id}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Returns:
            dict: Performance statistics
        """
        if self.transcription_count == 0:
            return {
                "transcriptions_processed": 0,
                "total_audio_duration": 0.0,
                "average_processing_time": 0.0,
                "real_time_factor": 0.0,
                "active_sessions": len(self.active_sessions)
            }
        
        avg_processing_time = self.total_processing_time / self.transcription_count
        rtf = self.total_processing_time / max(self.total_audio_processed, 0.001)
        
        return {
            "transcriptions_processed": self.transcription_count,
            "total_audio_duration": self.total_audio_processed,
            "average_processing_time": avg_processing_time,
            "real_time_factor": rtf,
            "active_sessions": len(self.active_sessions)
        }
    
    async def close(self):
        """Close streaming STT processor"""
        logger.info("Closing streaming STT processor")
        
        # Cancel processing task
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Clear session states
        self.active_sessions.clear()
        
        # Close VAD
        if self.vad:
            self.vad.reset_state()
        
        # Close language detector
        language_detector.close()
        
        # Close audio preprocessor
        audio_preprocessor.close()
        
        # Close accent adaptation manager
        accent_adaptation_manager.close()
        
        # Close domain-specific STT manager
        domain_specific_stt.close()
        
        # Close voice verification manager
        voice_verification.close()
        
        # Close emotion recognition manager
        emotion_recognition.close()
        
        self.is_initialized = False
        logger.info("Streaming STT processor closed")


# Global streaming STT processor instance
streaming_stt_processor = StreamingSTTProcessor()