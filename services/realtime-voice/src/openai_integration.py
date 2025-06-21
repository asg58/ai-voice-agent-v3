"""
OpenAI Integration Service for Phase 2
Real-time AI conversation with speech processing
"""
import os
import asyncio
import logging
import base64
import io
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime

import openai
from openai import AsyncOpenAI
import aiofiles

# Configure logging
logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI API integration for real-time conversation"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.conversation_model = "gpt-4o-mini"
        self.speech_model = "whisper-1"
        self.tts_model = "tts-1"
        self.tts_voice = "nova"  # Friendly female voice
        
        # Conversation settings
        self.max_tokens = 150
        self.temperature = 0.7
        self.system_prompt = """Je bent een vriendelijke, behulpzame AI-assistent die natuurlijk Nederlands spreekt. 
Je geeft korte, informatieve antwoorden en houdt gesprekken vlot en engaging. 
Je bent gespecialiseerd in het helpen van gebruikers met vragen en taken in het Nederlands."""
    
    async def transcribe_audio(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """
        Transcribe audio to text using OpenAI Whisper
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Create temporary file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{format}"
            
            # Call OpenAI Whisper API
            transcript = await self.client.audio.transcriptions.create(
                model=self.speech_model,
                file=audio_file,
                language="nl"  # Dutch language
            )
            
            transcribed_text = transcript.text.strip()
            logger.info(f"🎤 Transcribed audio: '{transcribed_text[:50]}...'")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"❌ Error transcribing audio: {e}")
            return None
    
    async def generate_conversation_response(self, 
                                           user_message: str, 
                                           conversation_history: List[Dict[str, str]] = None,
                                           stream: bool = False) -> str:
        """
        Generate AI conversation response using GPT
        
        Args:
            user_message: User's input message
            conversation_history: Previous conversation context
            stream: Whether to stream the response
            
        Returns:
            AI response text
        """
        try:
            # Prepare conversation context
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history (keep last 10 exchanges)
            if conversation_history:
                recent_history = conversation_history[-20:]  # Last 10 exchanges (user + assistant)
                messages.extend(recent_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            if stream:
                return await self._generate_streaming_response(messages)
            else:
                response = await self.client.chat.completions.create(
                    model=self.conversation_model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1
                )
                
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"🤖 AI Response: '{ai_response[:50]}...'")
                
                return ai_response
                
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return "Sorry, ik kon geen antwoord genereren. Probeer het opnieuw."
    
    async def _generate_streaming_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Generate streaming AI response"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.conversation_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"❌ Error in streaming response: {e}")
            yield "Sorry, er is een fout opgetreden bij het genereren van het antwoord."
    
    async def synthesize_speech(self, text: str, voice: str = None) -> Optional[bytes]:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        try:
            # Use specified voice or default
            selected_voice = voice or self.tts_voice
            
            # Generate speech
            response = await self.client.audio.speech.create(
                model=self.tts_model,
                voice=selected_voice,
                input=text,
                response_format="mp3",
                speed=1.0
            )
            
            # Get audio bytes
            audio_bytes = b""
            async for chunk in response.iter_bytes():
                audio_bytes += chunk
            
            logger.info(f"🔊 Synthesized speech for text: '{text[:50]}...' ({len(audio_bytes)} bytes)")
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ Error synthesizing speech: {e}")
            return None
    
    async def process_conversation_cycle(self, 
                                       audio_data: bytes = None,
                                       text_input: str = None,
                                       conversation_history: List[Dict[str, str]] = None,
                                       return_audio: bool = True) -> Dict[str, any]:
        """
        Complete conversation cycle: speech-to-text, AI response, text-to-speech
        
        Args:
            audio_data: Input audio bytes (if speech input)
            text_input: Input text (if text input)
            conversation_history: Previous conversation context
            return_audio: Whether to generate audio response
            
        Returns:
            Dictionary with transcription, AI response, and audio
        """
        result = {
            "transcribed_text": None,
            "ai_response_text": None,
            "ai_response_audio": None,
            "processing_time_ms": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = datetime.now()
        
        try:
            # Step 1: Speech-to-Text (if audio input)
            if audio_data:
                logger.info("🎤 Processing audio input...")
                transcribed_text = await self.transcribe_audio(audio_data)
                result["transcribed_text"] = transcribed_text
                
                if not transcribed_text:
                    result["ai_response_text"] = "Sorry, ik kon je audio niet verstaan. Kun je het opnieuw proberen?"
                    return result
                    
                user_input = transcribed_text
            elif text_input:
                user_input = text_input
                result["transcribed_text"] = text_input
            else:
                raise ValueError("Either audio_data or text_input must be provided")
            
            # Step 2: Generate AI Response
            logger.info("🤖 Generating AI response...")
            ai_response = await self.generate_conversation_response(
                user_message=user_input,
                conversation_history=conversation_history
            )
            result["ai_response_text"] = ai_response
            
            # Step 3: Text-to-Speech (if requested)
            if return_audio and ai_response:
                logger.info("🔊 Synthesizing speech response...")
                audio_response = await self.synthesize_speech(ai_response)
                result["ai_response_audio"] = audio_response
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = round(processing_time, 2)
            
            logger.info(f"✅ Conversation cycle completed in {processing_time:.0f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in conversation cycle: {e}")
            result["ai_response_text"] = "Sorry, er is een fout opgetreden. Probeer het opnieuw."
            result["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            return result


class ConversationManager:
    """Manages conversation state and context"""
    
    def __init__(self, max_history_length: int = 20):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.max_history_length = max_history_length
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversations[session_id].append(message)
        
        # Keep only recent messages to prevent context overflow
        if len(self.conversations[session_id]) > self.max_history_length:
            # Remove oldest messages but keep system message if present
            self.conversations[session_id] = self.conversations[session_id][-self.max_history_length:]
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for session"""
        return self.conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, any]:
        """Get conversation statistics"""
        history = self.conversations.get(session_id, [])
        
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        return {
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "conversation_started": history[0]["timestamp"] if history else None,
            "last_message": history[-1]["timestamp"] if history else None
        }


# Audio utility functions
def encode_audio_to_base64(audio_bytes: bytes) -> str:
    """Encode audio bytes to base64 string"""
    return base64.b64encode(audio_bytes).decode('utf-8')

def decode_audio_from_base64(audio_base64: str) -> bytes:
    """Decode base64 string to audio bytes"""
    return base64.b64decode(audio_base64)

def validate_audio_format(audio_data: bytes) -> bool:
    """Basic validation of audio data"""
    # Check if it looks like valid audio data
    return len(audio_data) > 44  # Minimum for WAV header

# Global instances
openai_service = None
conversation_manager = ConversationManager()

def initialize_openai_service(api_key: str) -> OpenAIService:
    """Initialize OpenAI service with API key"""
    global openai_service
    openai_service = OpenAIService(api_key)
    logger.info("✅ OpenAI service initialized")
    return openai_service
