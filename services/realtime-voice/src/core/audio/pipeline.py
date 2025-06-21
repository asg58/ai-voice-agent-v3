"""
Audio Processing Pipeline for AI Voice Agent
Handles audio processing, STT, TTS, and conversation management
"""
import asyncio
import logging
import time
from typing import Dict, Optional, AsyncGenerator

from src.models import AudioChunk, TranscriptionResult
from src.core.audio.models import TTSRequest, TTSResponse
from src.core.conversation.manager import ConversationManager
from src.core.translation.translator import translator
from src.config import settings

logger = logging.getLogger(__name__)

class AudioProcessingPipeline:
    """Audio processing pipeline for AI Voice Agent"""
    
    def __init__(self):
        """Initialize audio processing pipeline"""
        self.initialized = False
        self.conversation_manager = None
        self.active_sessions = {}
    
    async def initialize(self):
        """Initialize audio processing pipeline"""
        logger.info("Initializing audio processing pipeline")
        
        try:
            # Initialize conversation manager
            self.conversation_manager = ConversationManager()
            await self.conversation_manager.initialize()
            
            # Initialize streaming STT processor
            from src.core.audio.streaming_stt import streaming_stt_processor
            await streaming_stt_processor.initialize()
            
            # Initialize VAD
            from src.core.audio.vad import VoiceActivityDetector
            self.vad = VoiceActivityDetector()
            await self.vad.initialize()
            
            # Initialize audio preprocessor
            from src.core.audio.preprocessing import audio_preprocessor
            await audio_preprocessor.initialize()
            
            # Initialize TTS engine
            from src.core.audio.tts import tts_engine
            await tts_engine.initialize()
            
            # Initialize translator
            await translator.initialize()
            
            self.initialized = True
            logger.info("Audio processing pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio processing pipeline: {str(e)}")
            raise
    
    async def process_audio(self, chunk: AudioChunk) -> Optional[TranscriptionResult]:
        """Process audio chunk and return transcription result"""
        if not self.initialized:
            logger.error("Audio processing pipeline not initialized")
            return None
        
        try:
            # Create session if it doesn't exist
            session_id = chunk.session_id
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "last_activity": time.time(),
                    "audio_buffer": [],
                    "is_speaking": False
                }
            
            # Update session activity
            self.active_sessions[session_id]["last_activity"] = time.time()
            
            # Process audio with streaming STT processor
            from src.core.audio.streaming_stt import streaming_stt_processor
            result = await streaming_stt_processor.process_audio(chunk)
            
            # If no result yet, check if translation is needed
            if result and result.text:
                # Get session from session manager
                from src.core.session.manager import session_manager
                session = session_manager.get_session(session_id)
                
                # Check if auto-translation is enabled and target language is different
                if session and session.auto_translate and session.language != session.target_language:
                    # Translate transcription
                    translated_result = await translator.translate_transcription(
                        result, session.target_language
                    )
                    
                    # Return translated result
                    return translated_result
            
            # Return None if no result or empty text
            if not result or not result.text:
                return None
            
            # If we have a result, check if translation is needed
            # Get session from session manager
            from src.core.session.manager import session_manager
            session = session_manager.get_session(session_id)
            
            # Check if auto-translation is enabled and target language is different
            if session and session.auto_translate and session.language != session.target_language:
                # Translate transcription
                translated_result = await translator.translate_transcription(
                    result, session.target_language
                )
                
                # Return translated result
                return translated_result
            
            # Return original result
            return result
        
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return None
    
    async def process_text(self, session_id: str, text: str) -> AsyncGenerator[str, None]:
        """Process text input and generate response"""
        if not self.initialized:
            logger.error("Audio processing pipeline not initialized")
            yield "Error: Audio processing pipeline not initialized"
            return
        
        try:
            # Create session if it doesn't exist
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "last_activity": time.time(),
                    "audio_buffer": [],
                    "is_speaking": False
                }
            
            # Update session activity
            self.active_sessions[session_id]["last_activity"] = time.time()
            
            # Generate response with conversation manager
            async for response_chunk in self.conversation_manager.generate_streaming_response(
                session_id, text
            ):
                yield response_chunk
        
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def generate_response(self, session_id: str, transcription: TranscriptionResult) -> TTSRequest:
        """Generate response to transcription"""
        if not self.initialized:
            logger.error("Audio processing pipeline not initialized")
            return TTSRequest(
                session_id=session_id,
                text="Error: Audio processing pipeline not initialized",
                voice="default",
                language="nl"
            )
        
        try:
            # Update session activity
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["last_activity"] = time.time()
            
            # Generate response with conversation manager
            tts_request = await self.conversation_manager.process_transcription(
                session_id, transcription
            )
            
            if tts_request is None:
                # Create default response
                tts_request = TTSRequest(
                    session_id=session_id,
                    text="Ik begrijp het niet helemaal. Kun je dat anders formuleren?",
                    voice="default",
                    language="nl"
                )
            
            # Check if translation is needed for response
            from src.core.session.manager import session_manager
            session = session_manager.get_session(session_id)
            
            if session and session.auto_translate and session.language != session.target_language:
                # Translate TTS request
                translated_request = await translator.translate_tts_request(
                    tts_request, session.target_language
                )
                
                # Use translated request
                tts_request = translated_request
            
            return tts_request
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return TTSRequest(
                session_id=session_id,
                text=f"Er is een fout opgetreden: {str(e)}",
                voice="default",
                language="nl"
            )
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize speech from text
        
        Args:
            request: TTS request with text and parameters
            
        Returns:
            TTSResponse with generated audio
        """
        if not self.initialized:
            logger.error("Audio processing pipeline not initialized")
            return TTSResponse(
                session_id=request.session_id,
                audio_data=b"",
                sample_rate=16000,
                duration=0.0
            )
        
        try:
            # Get language for session if not specified
            if not request.language:
                from src.core.audio.language_detection import language_detector
                request.language = language_detector.get_session_language(request.session_id)
            
            # Create TTS request for the engine
            from src.models import TTSRequest as ModelTTSRequest
            tts_request = ModelTTSRequest(
                session_id=request.session_id,
                text=request.text,
                voice_id=request.voice,
                language=request.language,
                speed=getattr(request, 'speed', 1.0),
                emotion=getattr(request, 'emotion', 'neutral'),
                pitch=getattr(request, 'pitch', None),
                streaming=True
            )
            
            # Clean up translator
            translator.reset_session(request.session_id)
            
            # Get TTS engine
            from src.core.audio.tts import tts_engine
            
            # Synthesize speech
            result = await tts_engine.synthesize_speech(tts_request)
            
            # Convert to TTSResponse
            response = TTSResponse(
                session_id=request.session_id,
                audio_data=result.audio_data,
                sample_rate=result.sample_rate,
                duration=result.duration,
                text=result.text,
                voice=result.voice_id
            )
            
            # Clean up translator
            translator.reset_session(request.session_id)
            
            return response
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            return TTSResponse(
                session_id=request.session_id,
                audio_data=b"",
                sample_rate=16000,
                duration=0.0
            )
    
    async def reset_conversation(self, session_id: str):
        """Reset conversation context"""
        if not self.initialized:
            logger.error("Audio processing pipeline not initialized")
            return
        
        try:
            # Reset conversation with conversation manager
            if self.conversation_manager:
                self.conversation_manager.end_conversation(session_id)
                self.conversation_manager.create_conversation(session_id)
            
            # Clean up translator
            translator.reset_session(session_id)
            
            # Reset session state
            if session_id in self.active_sessions:
                self.active_sessions[session_id] = {
                    "last_activity": time.time(),
                    "audio_buffer": [],
                    "is_speaking": False
                }
            
            logger.info(f"Reset conversation for session {session_id}")
        
        except Exception as e:
            logger.error(f"Error resetting conversation: {str(e)}")
    
    async def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        if not self.initialized:
            return
        
        try:
            # Clean up conversation with conversation manager
            if self.conversation_manager:
                self.conversation_manager.end_conversation(session_id)
            
            # Clean up streaming STT processor
            from src.core.audio.streaming_stt import streaming_stt_processor
            await streaming_stt_processor.cleanup_session(session_id)
            
            # Clean up audio preprocessor
            from src.core.audio.preprocessing import audio_preprocessor
            audio_preprocessor.reset_session(session_id)
            
            # Clean up translator
            translator.reset_session(session_id)
            
            # Clean up VAD
            if hasattr(self, 'vad'):
                self.vad.reset_state()
            
            # Remove session state
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"Cleaned up session {session_id}")
        
        except Exception as e:
            logger.error(f"Error cleaning up session: {str(e)}")
    
    async def shutdown(self):
        """Shut down audio processing pipeline"""
        logger.info("Shutting down audio processing pipeline")
        
        try:
            # Close conversation manager
            if self.conversation_manager:
                await self.conversation_manager.close()
            
            # Close streaming STT processor
            from src.core.audio.streaming_stt import streaming_stt_processor
            await streaming_stt_processor.close()
            
            # Close audio preprocessor
            from src.core.audio.preprocessing import audio_preprocessor
            audio_preprocessor.close()
            
            # Close TTS engine
            from src.core.audio.tts import tts_engine
            tts_engine.close()
            
            # Close translator
            translator.close()
            
            # Clear session state
            self.active_sessions = {}
            
            self.initialized = False
            logger.info("Audio processing pipeline shut down successfully")
        
        except Exception as e:
            logger.error(f"Error shutting down audio processing pipeline: {str(e)}")
            raise