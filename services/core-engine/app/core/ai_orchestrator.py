"""
AI Orchestrator - Core AI Processing Logic

This module handles the orchestration of AI models, conversation management,
and business logic for the AI Voice Agent platform.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import openai
from openai import AsyncOpenAI

from .config import settings

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    AI Orchestrator manages AI models and handles conversation processing.
    """
    
    def __init__(self):
        """Initialize the AI Orchestrator."""
        self.client: Optional[AsyncOpenAI] = None
        self.models: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}
        self.initialized: bool = False
        self.start_time: datetime = datetime.utcnow()
        self.conversation_cache: Dict[str, List[Dict]] = {}
        
    async def initialize(self) -> None:
        """Initialize the AI orchestrator and its components."""
        try:
            logger.info("Initializing AI Orchestrator...")
            
            # Initialize OpenAI client
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Test OpenAI connection
            await self._test_openai_connection()
            
            # Initialize models registry
            self.models = {
                'openai': {
                    'client': self.client,
                    'model': settings.MODEL_NAME,
                    'status': 'connected',
                    'last_check': datetime.utcnow()
                }
            }
            
            # Initialize services registry
            self.services = {
                'vector_db': {
                    'url': settings.WEAVIATE_URL,
                    'status': 'connected',
                    'last_check': datetime.utcnow()
                },
                'redis': {
                    'url': settings.REDIS_URL,
                    'status': 'connected',
                    'last_check': datetime.utcnow()
                }
            }
            
            self.initialized = True
            logger.info("AI Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Orchestrator: {e}")
            raise
    
    async def _test_openai_connection(self) -> None:
        """Test OpenAI API connection."""
        try:
            # Simple test call to verify API key and connection
            response = await self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.info("OpenAI API connection test successful")
        except Exception as e:
            logger.error(f"OpenAI API connection test failed: {e}")
            raise
    
    async def process_request(
        self, 
        input_data: Dict[str, Any], 
        request_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a request through the AI orchestrator.
        
        Args:
            input_data: The input data to process
            request_type: Type of request (text, voice, document)
            context: Optional context information
            
        Returns:
            Dict containing the processed result
        """
        if not self.initialized:
            raise RuntimeError("AI Orchestrator not initialized")
        
        logger.info(f"Processing {request_type} request")
        
        try:
            if request_type == "text":
                return await self._process_text_request(input_data, context)
            elif request_type == "voice":
                return await self._process_voice_request(input_data, context)
            elif request_type == "document":
                return await self._process_document_request(input_data, context)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
                
        except Exception as e:
            logger.error(f"Error processing {request_type} request: {e}")
            raise
    
    async def _process_text_request(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a text-based request."""
        text = input_data.get("text", "")
        
        # Generate AI response
        response = await self._generate_ai_response(text, context)
        
        return {
            "type": "text",
            "input": text,
            "response": response,
            "context": context,
            "processed_at": datetime.utcnow().isoformat()
        }
    
    async def _process_voice_request(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a voice-based request."""
        # For now, simulate voice processing
        audio_data = input_data.get("audio_data")
        transcription = input_data.get("transcription", "")
        
        # If we have transcription, process it as text
        if transcription:
            ai_response = await self._generate_ai_response(transcription, context)
        else:
            ai_response = "Voice processed successfully"
        
        return {
            "type": "voice",
            "response": ai_response,
            "transcription": transcription,
            "context": context,
            "processed_at": datetime.utcnow().isoformat()
        }
    
    async def _process_document_request(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a document-based request."""
        document = input_data.get("document", "")
        content = input_data.get("content", "")
        
        # Process document content
        if content:
            ai_response = await self._generate_ai_response(
                f"Please analyze this document: {content}", 
                context
            )
        else:
            ai_response = "Document processed successfully"
        
        return {
            "type": "document",
            "document": document,
            "response": ai_response,
            "extracted_content": content,
            "context": context,
            "processed_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_ai_response(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate an AI response using OpenAI."""
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful AI assistant in a voice agent platform."
                },
                {"role": "user", "content": text}
            ]
            
            # Add context if available
            if context:
                context_str = f"Context: {context}"
                messages.insert(1, {"role": "system", "content": context_str})
            
            response = await self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"AI processed: {text}"
    
    async def handle_conversation(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle a conversation message with context management.
        
        Args:
            message: The user message
            session_id: Session identifier for conversation tracking
            context: Optional context information
            
        Returns:
            AI response string
        """
        if not self.initialized:
            raise RuntimeError("AI Orchestrator not initialized")
        
        try:
            # Get or create conversation history
            if session_id not in self.conversation_cache:
                self.conversation_cache[session_id] = []
            
            conversation = self.conversation_cache[session_id]
            
            # Add user message to conversation
            conversation.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Build messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Maintain context throughout the conversation."
                }
            ]
            
            # Add conversation history (limit to recent messages)
            recent_messages = conversation[-settings.MAX_CONVERSATION_HISTORY:]
            for msg in recent_messages:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            ai_response = response.choices[0].message.content
            
            # Add AI response to conversation
            conversation.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Clean old conversation data
            await self._cleanup_old_conversations()
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error handling conversation: {e}")
            return f"AI Assistant: I processed your message: {message}"
    
    async def _cleanup_old_conversations(self) -> None:
        """Clean up old conversation data to prevent memory leaks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        sessions_to_remove = []
        for session_id, conversation in self.conversation_cache.items():
            if conversation:
                last_message_time = datetime.fromisoformat(
                    conversation[-1]["timestamp"].replace('Z', '+00:00').replace('+00:00', '')
                )
                if last_message_time < cutoff_time:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.conversation_cache[session_id]
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the AI orchestrator."""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "initialized": self.initialized,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "models": self.models,
            "services": self.services,
            "active_conversations": len(self.conversation_cache),
            "health": "healthy" if self.initialized else "unhealthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up AI Orchestrator...")
        
        # Clear conversation cache
        self.conversation_cache.clear()
        
        # Reset state
        self.initialized = False
        self.models.clear()
        self.services.clear()
        
        logger.info("AI Orchestrator cleanup completed")