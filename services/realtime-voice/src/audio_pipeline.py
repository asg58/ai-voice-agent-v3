"""
Audio Processing Pipeline for Real-time Conversational AI
Orchestrates STT, LLM, and TTS components for seamless conversation flow
"""
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator, Callable, List
from datetime import datetime

from .models import AudioChunk, TranscriptionResult, TTSResult
from .stt_engine import stt_engine
from .tts_engine import tts_engine
from .conversation_manager import conversation_manager
from .vad_detector import vad_detector

logger = logging.getLogger(__name__)


class AudioPipelineEvent:
    """Event data for audio pipeline callbacks"""
    
    def __init__(self, event_type: str, session_id: str, data: Any = None, metadata: Dict = None):
        self.event_type = event_type
        self.session_id = session_id
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class AudioProcessingPipeline:
    """
    Professional Audio Processing Pipeline
    
    Orchestrates the complete conversation flow:
    1. Audio Input → VAD → STT → LLM → TTS → Audio Output
    2. Real-time streaming with minimal latency
    3. Event-driven architecture for real-time updates
    4. Interruption handling and conversation management
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.event_callbacks: Dict[str, List[Callable]] = {}
        self.is_initialized = False
        
        # Pipeline statistics
        self.stats = {
            "sessions_created": 0,
            "audio_chunks_processed": 0,
            "transcriptions_completed": 0,
            "responses_generated": 0,
            "total_processing_time": 0.0
        }
        
        logger.info("AudioProcessingPipeline initialized")
    
    async def initialize(self):
        """Initialize all pipeline components"""
        try:
            logger.info("Initializing audio processing pipeline...")
            
            # Initialize components in order
            await vad_detector.initialize()
            logger.info("✅ VAD detector initialized")
            
            await stt_engine.initialize()
            logger.info("✅ STT engine initialized")
            
            await conversation_manager.initialize()
            logger.info("✅ Conversation manager initialized")
            
            await tts_engine.initialize()
            logger.info("✅ TTS engine initialized")
            
            self.is_initialized = True
            logger.info("🚀 Audio processing pipeline fully initialized!")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio pipeline: {e}")
            self.is_initialized = False
            raise
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register callback for pipeline events"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
        logger.debug(f"Registered callback for event: {event_type}")
    
    async def _emit_event(self, event: AudioPipelineEvent):
        """Emit pipeline event to registered callbacks"""
        callbacks = self.event_callbacks.get(event.event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback for {event.event_type}: {e}")
    
    async def create_session(self, session_id: str, config: Optional[Dict] = None) -> bool:
        """Create a new conversation session"""
        if not self.is_initialized:
            logger.error("Pipeline not initialized")
            return False
        
        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already exists")
            return True
        
        try:
            # Create session data
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now(),
                "config": config or {},
                "status": "active",
                "audio_buffer": [],
                "processing_queue": asyncio.Queue(),
                "is_speaking": False,
                "last_activity": datetime.now()
            }
            
            self.active_sessions[session_id] = session_data
            
            # Create conversation context
            conversation_manager.create_conversation(session_id)
            
            # Start processing task for this session
            asyncio.create_task(self._process_session_queue(session_id))
            
            self.stats["sessions_created"] += 1
            
            await self._emit_event(AudioPipelineEvent(
                "session_created", session_id, data=session_data
            ))
            
            logger.info(f"Created audio processing session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            return False
    
    async def process_audio_chunk(self, session_id: str, audio_chunk: AudioChunk) -> bool:
        """
        Process incoming audio chunk through the complete pipeline
        
        Args:
            session_id: Session identifier
            audio_chunk: Raw audio data to process
            
        Returns:
            Success status
        """
        if not self.is_initialized:
            logger.error("Pipeline not initialized")
            return False
        
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return False
        
        try:
            session_data = self.active_sessions[session_id]
            session_data["last_activity"] = datetime.now()
            
            # Add to processing queue
            await session_data["processing_queue"].put({
                "type": "audio_chunk",
                "data": audio_chunk,
                "timestamp": datetime.now()
            })
            
            self.stats["audio_chunks_processed"] += 1
            
            await self._emit_event(AudioPipelineEvent(
                "audio_chunk_received", session_id, data=audio_chunk
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing audio chunk for session {session_id}: {e}")
            return False
    
    async def _process_session_queue(self, session_id: str):
        """Process the session's audio processing queue"""
        logger.info(f"Started processing queue for session {session_id}")
        
        try:
            session_data = self.active_sessions[session_id]
            queue = session_data["processing_queue"]
            
            while session_id in self.active_sessions:
                try:
                    # Get next item from queue with timeout
                    item = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    if item["type"] == "audio_chunk":
                        await self._process_audio_pipeline(session_id, item["data"])
                    
                    # Mark task as done
                    queue.task_done()
                    
                except asyncio.TimeoutError:
                    # Check if session is still active
                    continue
                except Exception as e:
                    logger.error(f"Error in processing queue for session {session_id}: {e}")
                    await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Session queue processor error for {session_id}: {e}")
        
        finally:
            logger.info(f"Processing queue ended for session {session_id}")
    
    async def _process_audio_pipeline(self, session_id: str, audio_chunk: AudioChunk):
        """Process audio through the complete STT→LLM→TTS pipeline"""
        start_time = datetime.now()
        
        try:
            # Step 1: Voice Activity Detection
            audio_array = audio_chunk.to_numpy()
            has_speech = await vad_detector.detect_speech(audio_array, audio_chunk.sample_rate)
            
            if not has_speech:
                logger.debug(f"No speech detected in audio chunk for session {session_id}")
                return
            
            await self._emit_event(AudioPipelineEvent(
                "speech_detected", session_id, data={"confidence": 0.8}
            ))
            
            # Step 2: Speech-to-Text
            logger.debug(f"Processing STT for session {session_id}")
            transcription = await stt_engine.transcribe_chunk(audio_chunk)
            
            if not transcription or not transcription.text.strip():
                logger.debug(f"No transcription result for session {session_id}")
                return
            
            await self._emit_event(AudioPipelineEvent(
                "transcription_completed", session_id, data=transcription
            ))
            
            self.stats["transcriptions_completed"] += 1
            
            # Step 3: LLM Processing
            logger.debug(f"Processing LLM for session {session_id}: {transcription.text}")
            tts_request = await conversation_manager.process_transcription(session_id, transcription)
            
            if not tts_request:
                logger.debug(f"No LLM response for session {session_id}")
                return
            
            await self._emit_event(AudioPipelineEvent(
                "response_generated", session_id, data=tts_request
            ))
            
            self.stats["responses_generated"] += 1
            
            # Step 4: Text-to-Speech
            logger.debug(f"Processing TTS for session {session_id}: {tts_request.text}")
            tts_result = await tts_engine.synthesize(tts_request)
            
            if tts_result:
                await self._emit_event(AudioPipelineEvent(
                    "audio_generated", session_id, data=tts_result
                ))
                
                logger.info(f"Complete pipeline processing for session {session_id}: "
                          f"'{transcription.text}' → '{tts_request.text}'")
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_processing_time"] += processing_time
            
            await self._emit_event(AudioPipelineEvent(
                "pipeline_completed", session_id, 
                data={
                    "transcription": transcription,
                    "response": tts_request,
                    "audio": tts_result,
                    "processing_time": processing_time
                }
            ))
            
        except Exception as e:
            logger.error(f"Error in audio pipeline for session {session_id}: {e}")
            await self._emit_event(AudioPipelineEvent(
                "pipeline_error", session_id, data={"error": str(e)}
            ))
    
    async def process_text_input(self, session_id: str, text: str) -> Optional[TTSResult]:
        """
        Process text input directly (bypass STT)
        
        Args:
            session_id: Session identifier
            text: User text input
            
        Returns:
            TTS result with generated audio
        """
        if not self.is_initialized:
            logger.error("Pipeline not initialized")
            return None
        
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return None
        
        try:
            # Create fake transcription result
            transcription = TranscriptionResult(
                session_id=session_id,
                text=text,
                confidence=1.0,
                start_time=datetime.now().timestamp(),
                end_time=datetime.now().timestamp(),
                is_final=True
            )
            
            # Process through LLM
            tts_request = await conversation_manager.process_transcription(session_id, transcription)
            
            if not tts_request:
                return None
            
            # Generate audio response
            tts_result = await tts_engine.synthesize(tts_request)
            
            logger.info(f"Processed text input for session {session_id}: '{text}' → '{tts_request.text}'")
            return tts_result
            
        except Exception as e:
            logger.error(f"Error processing text input for session {session_id}: {e}")
            return None
    
    async def generate_streaming_response(self, session_id: str, text: str) -> AsyncGenerator[str, None]:
        """Generate streaming text response"""
        if not self.is_initialized:
            logger.error("Pipeline not initialized")
            return
        
        try:
            async for chunk in conversation_manager.generate_streaming_response(session_id, text):
                yield chunk
        except Exception as e:
            logger.error(f"Error in streaming response for session {session_id}: {e}")
            yield f"Error: {str(e)}"
    
    async def end_session(self, session_id: str) -> bool:
        """End and cleanup session"""
        try:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                session_data["status"] = "ended"
                
                # Wait for queue to finish
                await session_data["processing_queue"].join()
                
                del self.active_sessions[session_id]
                
                await self._emit_event(AudioPipelineEvent(
                    "session_ended", session_id
                ))
                
                logger.info(f"Ended audio processing session: {session_id}")
            
            # Cleanup conversation
            conversation_manager.end_conversation(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id].copy()
            # Remove queue object for JSON serialization
            session_data.pop("processing_queue", None)
            return session_data
        return None
    
    def get_pipeline_stats(self) -> Dict:
        """Get pipeline statistics"""
        stats = self.stats.copy()
        stats.update({
            "active_sessions": len(self.active_sessions),
            "average_processing_time": (
                self.stats["total_processing_time"] / max(self.stats["responses_generated"], 1)
            ),
            "is_initialized": self.is_initialized
        })
        return stats
    
    async def cleanup_expired_sessions(self, timeout_minutes: int = 30):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            if (current_time - session_data["last_activity"]).total_seconds() > (timeout_minutes * 60):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        # Also cleanup conversation manager
        conversation_manager.cleanup_expired_conversations(timeout_minutes)
    
    async def close(self):
        """Cleanup all resources"""
        logger.info("Closing audio processing pipeline...")
        
        # End all active sessions
        active_session_ids = list(self.active_sessions.keys())
        for session_id in active_session_ids:
            await self.end_session(session_id)
        
        # Close components
        await conversation_manager.close()
        await tts_engine.close()
        await stt_engine.close()
        await vad_detector.close()
        
        self.is_initialized = False
        logger.info("Audio processing pipeline closed")


# Global pipeline instance
audio_pipeline = AudioProcessingPipeline()
