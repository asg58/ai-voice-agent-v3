"""
Conversation Manager for Real-time AI
Handles LLM integration, context management, and conversation flow
"""
import logging
import json
from typing import Optional, Dict, List, AsyncGenerator, Any
from datetime import datetime, timedelta

import ollama
import openai
from pydantic import BaseModel, Field

from .models import ConversationMessage, TranscriptionResult, TTSRequest
from src.core.memory.manager import memory_manager
from src.models import ConversationSession

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuration for LLM integration"""
    # OpenAI Configuration
    openai_api_key: str = Field("", description="OpenAI API key")
    openai_model: str = Field("gpt-3.5-turbo", description="OpenAI model name")
    openai_max_tokens: int = Field(256, description="Max tokens in response")
    openai_temperature: float = Field(0.7, description="Response creativity")
    
    # Ollama Configuration (fallback)
    base_url: str = Field("http://localhost:11434", description="Ollama base URL")
    model: str = Field("llama3", description="LLM model name")
    max_tokens: int = Field(256, description="Max tokens in response")
    temperature: float = Field(0.7, description="Response creativity")
    stream: bool = Field(True, description="Enable streaming responses")
    
    system_prompt: str = Field(
        "Je bent een vriendelijke, natuurlijke Nederlandse AI-assistent. "
        "Geef korte, conversationele antwoorden alsof je een echte persoon bent. "
        "Gebruik natuurlijke spraakpatronen en emotie in je antwoorden.",
        description="System prompt for the AI"
    )
    timeout: float = Field(30.0, description="Request timeout in seconds")
    
    class Config:
        env_prefix = "LLM_"


class ConversationContext:
    """Manages conversation context and history"""
    
    def __init__(self, session_id: str, user_id: str = None, max_history: int = 10):
        self.session_id = session_id
        self.user_id = user_id or f"user_{session_id[:8]}"
        self.messages: List[ConversationMessage] = []
        self.max_history = max_history
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata = {}
        self.language = "nl"
    
    async def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        # Keep only recent messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        logger.debug(f"Added {role} message to conversation {self.session_id}: {content[:100]}...")
        
        # Store message in memory system if enabled
        try:
            if memory_manager.initialized:
                # Store in short-term memory (Redis)
                session_data = {
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "last_activity": self.last_activity.isoformat(),
                    "language": self.language,
                    "last_message": {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await memory_manager.store_session(self.session_id, session_data)
                
                # Store in long-term memory (Database)
                if role in ["user", "assistant"]:  # Don't store system messages
                    await memory_manager.store_message(self.session_id, message)
        except Exception as e:
            logger.error(f"Error storing message in memory: {e}")
    
    def get_context_for_llm(self, system_prompt: str, memory_context: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """Get conversation history formatted for LLM"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add memory context if provided
        if memory_context:
            messages.extend(memory_context)
        
        # Add conversation history
        for msg in self.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if conversation has expired"""
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout
    
    def to_session_object(self) -> ConversationSession:
        """Convert to ConversationSession object for storage"""
        return ConversationSession(
            session_id=self.session_id,
            user_id=self.user_id,
            created_at=self.created_at,
            last_activity=self.last_activity,
            metadata=self.metadata
        )


class ConversationManager:
    """
    Professional Conversation Manager
    
    Features:
    - LLM integration with Ollama    - Conversation context management
    - Streaming response generation
    - Interruption handling
    - Emotional context awareness
    - Multi-turn conversation support
    """
    def __init__(self, config: Optional[LLMConfig] = None):
        # Load configuration from enhanced config
        from src.config.settings import ServiceConfig
        settings = ServiceConfig()
        
        # Create LLM config with OpenAI settings from environment
        if config is None:
            config = LLMConfig(
                openai_api_key=settings.openai_api_key,
                openai_model=settings.openai_model,
                openai_max_tokens=settings.openai_max_tokens,
                openai_temperature=settings.openai_temperature,
                base_url=settings.ollama_base_url,
                model=settings.ollama_model
            )        
        self.config = config
        self.conversations: Dict[str, ConversationContext] = {}
        self.client = None
        self.openai_client = None
        self.is_initialized = False
        
        # Prefer OpenAI if API key is available
        self.use_openai = bool(self.config.openai_api_key and self.config.openai_api_key.strip())
        
        logger.info(f"ConversationManager initialized with {'OpenAI' if self.use_openai else 'Ollama'} model: {self.config.openai_model if self.use_openai else self.config.model}")
    
    async def initialize(self):
        """Initialize the conversation manager"""
        try:
            if self.use_openai:
                # Initialize OpenAI client
                self.openai_client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
                # Test connection
                await self._test_openai_connection()
                logger.info("OpenAI client initialized successfully")
            else:
                # Initialize Ollama client
                self.client = ollama.AsyncClient(host=self.config.base_url)            
                # Test connection and ensure model is available
                await self._ensure_model_available()
                logger.info("Ollama client initialized successfully")
            
            # Initialize memory manager if not already initialized
            if not memory_manager.initialized:
                await memory_manager.initialize()
                logger.info("Memory manager initialized")
            
            self.is_initialized = True
            logger.info("ConversationManager initialized successfully")            
        except Exception as e:
            logger.error(f"Failed to initialize ConversationManager: {e}")
            self.is_initialized = False
            raise

    async def _test_openai_connection(self):
        """Test OpenAI connection with a simple call"""
        try:
            await self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            logger.info(f"OpenAI model {self.config.openai_model} is working correctly")
        except Exception as e:
            logger.warning(f"OpenAI connection test failed: {e}")
            logger.info("Falling back to simple mode without testing")
            # Don't raise the exception - just warn and continue

    async def _ensure_model_available(self):
        """Ensure the specified model is available"""
        try:
            # Check if model exists
            models = await self.client.list()
            # Handle both old and new Ollama API response formats
            if 'models' in models:
                model_names = [model.get('name', model.get('model', '')) for model in models['models']]
            else:
                model_names = [model.get('name', model.get('model', '')) for model in models]
            
            if self.config.model not in model_names:
                logger.warning(f"Model {self.config.model} not found. Available models: {model_names}")
                
                # Try to pull the model
                logger.info(f"Attempting to pull model: {self.config.model}")
                await self.client.pull(self.config.model)
                logger.info(f"Successfully pulled model: {self.config.model}")
            
            # Test model with a simple prompt
            await self.client.generate(
                model=self.config.model,
                prompt="Test",
                options={"num_predict": 1}
            )
            logger.info(f"Model {self.config.model} is working correctly")
            
        except Exception as e:
            logger.error(f"Error ensuring model availability: {e}")
            raise
    
    async def create_conversation(self, session_id: str, user_id: str = None) -> ConversationContext:
        """Create a new conversation context"""
        if session_id in self.conversations:
            logger.warning(f"Conversation {session_id} already exists")
            return self.conversations[session_id]
        
        # Check if we have session data in memory
        session_data = None
        if memory_manager.initialized:
            session_data = await memory_manager.get_session(session_id)
        
        # Create context with user_id from memory if available
        if session_data and "user_id" in session_data:
            user_id = session_data.get("user_id")
            
        context = ConversationContext(session_id, user_id)
        self.conversations[session_id] = context
        
        # Store conversation in memory
        if memory_manager.initialized:
            await memory_manager.store_conversation(context.to_session_object())
        
        logger.info(f"Created new conversation: {session_id} for user: {context.user_id}")
        return context
    
    def get_conversation(self, session_id: str) -> Optional[ConversationContext]:
        """Get existing conversation context"""
        return self.conversations.get(session_id)
    
    async def end_conversation(self, session_id: str):
        """End and cleanup conversation"""
        if session_id in self.conversations:
            # Get conversation before deleting
            context = self.conversations[session_id]
            
            # Store final state in long-term memory
            if memory_manager.initialized:
                try:
                    # Store conversation in database
                    await memory_manager.store_conversation(context.to_session_object())
                    
                    # Delete from short-term memory
                    await memory_manager.delete_session(session_id)
                except Exception as e:
                    logger.error(f"Error storing conversation in memory: {e}")
            
            # Remove from active conversations
            del self.conversations[session_id]
            logger.info(f"Ended conversation: {session_id}")
    
    async def process_transcription(self, session_id: str, transcription: TranscriptionResult) -> Optional[TTSRequest]:
        """
        Process a transcription and generate AI response
        
        Args:
            session_id: Conversation session ID
            transcription: Transcription result from STT
            
        Returns:
            TTSRequest for generating audio response
        """
        if not self.is_initialized:
            logger.error("ConversationManager not initialized")
            return None
        
        try:
            # Get or create conversation context
            context = self.conversations.get(session_id)
            if not context:
                context = await self.create_conversation(session_id)
            
            # Set language if provided
            if transcription.language:
                context.language = transcription.language
            
            # Add user message to context
            await context.add_message(
                "user", 
                transcription.text,
                metadata={
                    "confidence": transcription.confidence,
                    "language": transcription.language,
                    "duration": transcription.duration
                }
            )
            
            # Get relevant memory context if available
            memory_context = []
            if memory_manager.initialized:
                try:
                    # Search memory for relevant information
                    memory_result = await memory_manager.search_memory(transcription.text, session_id)
                    
                    # Add relevant messages as context
                    if memory_result.messages:
                        memory_context.append({
                            "role": "system",
                            "content": "Relevante informatie uit eerdere gesprekken:"
                        })
                        
                        for msg in memory_result.messages[:3]:  # Limit to 3 most relevant messages
                            memory_context.append({
                                "role": "system",
                                "content": f"Eerder {msg.role}: {msg.content}"
                            })
                    
                    # Add relevant entities if found
                    if memory_result.entities:
                        entities_text = "Relevante entiteiten: " + ", ".join([f"{e.name} ({e.entity_type})" for e in memory_result.entities[:5]])
                        memory_context.append({
                            "role": "system",
                            "content": entities_text
                        })
                except Exception as e:
                    logger.error(f"Error retrieving memory context: {e}")
            
            # Generate AI response with memory context
            response_text = await self._generate_response(context, memory_context)
            
            if response_text:
                # Add AI response to context
                await context.add_message("assistant", response_text)
                
                # Create TTS request
                tts_request = TTSRequest(
                    session_id=session_id,
                    text=response_text,
                    language=context.language,
                    speed=self.config.temperature  # Use temperature as speed factor
                )
                
                return tts_request
            
        except Exception as e:
            logger.error(f"Error processing transcription for session {session_id}: {e}")
            # Add error context
            if session_id in self.conversations:
                await self.conversations[session_id].add_message(
                    "system", 
                    f"Error occurred: {str(e)}",
                    metadata={"error": True}
                )
        
        return None
    
    async def _generate_response(self, context: ConversationContext, memory_context: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        """Generate AI response using LLM"""
        try:
            # Prepare messages for LLM with memory context
            messages = context.get_context_for_llm(self.config.system_prompt, memory_context)
            
            # Generate response based on provider
            if self.use_openai:
                # OpenAI response
                response = await self.openai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=messages,
                    max_tokens=self.config.openai_max_tokens,
                    temperature=self.config.openai_temperature
                )
                response_text = response.choices[0].message.content.strip()
            else:
                # Generate response using Ollama
                if self.config.stream:
                    # Streaming response
                    response_chunks = []
                    async for chunk in await self.client.chat(
                        model=self.config.model,
                        messages=messages,
                        stream=True,
                        options={
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens
                        }
                    ):
                        if chunk.get('message', {}).get('content'):
                            response_chunks.append(chunk['message']['content'])
                    
                    response_text = ''.join(response_chunks).strip()
                else:
                    # Non-streaming response
                    response = await self.client.chat(
                        model=self.config.model,
                        messages=messages,
                        options={
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens
                        }
                    )
                    response_text = response['message']['content'].strip()
            
            logger.info(f"Generated response for session {context.session_id}: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None
    
    async def generate_streaming_response(self, session_id: str, user_text: str) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response
        
        Args:
            session_id: Conversation session ID
            user_text: User input text
            
        Yields:
            Response chunks as they are generated
        """
        if not self.is_initialized:
            logger.error("ConversationManager not initialized")
            return
        
        try:
            # Get or create conversation context
            context = self.conversations.get(session_id)
            if not context:
                context = await self.create_conversation(session_id)
            
            # Add user message
            await context.add_message("user", user_text)
            
            # Get relevant memory context if available
            memory_context = []
            if memory_manager.initialized:
                try:
                    # Search memory for relevant information
                    memory_result = await memory_manager.search_memory(user_text, session_id)
                    
                    # Add relevant messages as context
                    if memory_result.messages:
                        memory_context.append({
                            "role": "system",
                            "content": "Relevante informatie uit eerdere gesprekken:"
                        })
                        
                        for msg in memory_result.messages[:3]:  # Limit to 3 most relevant messages
                            memory_context.append({
                                "role": "system",
                                "content": f"Eerder {msg.role}: {msg.content}"
                            })
                    
                    # Add relevant entities if found
                    if memory_result.entities:
                        entities_text = "Relevante entiteiten: " + ", ".join([f"{e.name} ({e.entity_type})" for e in memory_result.entities[:5]])
                        memory_context.append({
                            "role": "system",
                            "content": entities_text
                        })
                except Exception as e:
                    logger.error(f"Error retrieving memory context: {e}")
            
            # Prepare messages for LLM with memory context
            messages = context.get_context_for_llm(self.config.system_prompt, memory_context)
            
            # Generate streaming response based on provider
            response_chunks = []
            
            if self.use_openai:
                # OpenAI streaming
                stream = await self.openai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=messages,
                    max_tokens=self.config.openai_max_tokens,
                    temperature=self.config.openai_temperature,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        response_chunks.append(content)
                        yield content
            else:
                # Ollama streaming
                async for chunk in await self.client.chat(
                    model=self.config.model,
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                ):
                    if chunk.get('message', {}).get('content'):
                        content = chunk['message']['content']
                        response_chunks.append(content)
                        yield content
            
            # Add complete response to context
            full_response = ''.join(response_chunks).strip()
            await context.add_message("assistant", full_response)
            
        except Exception as e:
            logger.error(f"Error in streaming response for session {session_id}: {e}")
            yield f"Sorry, ik ondervind een technisch probleem: {str(e)}"
    
    async def cleanup_expired_conversations(self, timeout_minutes: int = 30):
        """Clean up expired conversations"""
        expired_sessions = []
        
        for session_id, context in self.conversations.items():
            if context.is_expired(timeout_minutes):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_conversation(session_id)
        
        # Also clean up old sessions in database if memory manager is initialized
        if memory_manager.initialized:
            try:
                # Clean up sessions older than 30 days
                cleaned_count = await memory_manager.cleanup_old_sessions(max_age_days=30)
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} old sessions from database")
            except Exception as e:
                logger.error(f"Error cleaning up old sessions: {e}")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired conversations")
    
    async def close(self):
        """Cleanup resources"""
        if self.client:
            # Ollama client doesn't need explicit closing
            pass
        
        self.conversations.clear()
        self.is_initialized = False
        logger.info("ConversationManager closed")


# Global instance
conversation_manager = ConversationManager()
