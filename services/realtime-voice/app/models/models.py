"""
Data models for Real-time Voice AI Service
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import numpy as np


class SessionInfo(BaseModel):
    """Information about a conversation session"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    language: Optional[str] = Field(None, description="Session language")
    accent: Optional[str] = Field(None, description="Session accent")
    domain: Optional[str] = Field(None, description="Session domain")
    verified: Optional[bool] = Field(None, description="Whether user is voice-verified")
    emotion: Optional[str] = Field(None, description="Current user emotion")
    emotion_score: Optional[float] = Field(None, description="Emotion confidence score")
    target_language: Optional[str] = Field(None, description="Target language for translation")
    auto_translate: Optional[bool] = Field(None, description="Whether auto-translation is enabled")


class ConversationSession:
    """Conversation session with user state"""
    def __init__(self, session_id: str, user_id: str, created_at: datetime = None):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at or datetime.now()
        self.last_activity = self.created_at
        self.verified = False
        self.verification_attempts = 0
        self.language = "nl"  # Default language
        self.target_language = "nl"  # Default target language
        self.auto_translate = False  # Auto translation disabled by default
        self.messages = []
        self.current_emotion = "neutral"
        self.emotion_score = 1.0
        self.emotion_history = []
        self.translation_history = []
        self.metadata = {}


class MemoryCapabilities(BaseModel):
    """Memory system capabilities"""
    short_term: bool = Field(True, description="Short-term memory support")
    long_term: bool = Field(True, description="Long-term memory support")
    knowledge_graph: bool = Field(True, description="Knowledge graph support")
    vector_search: bool = Field(True, description="Vector search support")


class AudioChunk(BaseModel):
    """Audio data chunk for real-time processing"""
    session_id: str = Field(..., description="Conversation session ID")
    audio_data: bytes = Field(..., description="Raw audio data")
    sample_rate: int = Field(16000, description="Audio sample rate")
    channels: int = Field(1, description="Number of audio channels")
    timestamp: float = Field(..., description="Timestamp when audio was captured")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def from_numpy(cls, session_id: str, audio_array: np.ndarray, 
                   sample_rate: int = 16000, channels: int = 1, timestamp: float = None):
        """Create AudioChunk from numpy array"""
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        return cls(
            session_id=session_id,
            audio_data=audio_array.tobytes(),
            sample_rate=sample_rate,
            channels=channels,
            timestamp=timestamp,
            duration=len(audio_array) / sample_rate
        )
    
    def to_numpy(self) -> np.ndarray:
        """Convert audio data to numpy array"""
        return np.frombuffer(self.audio_data, dtype=np.int16)


class TranscriptionResult(BaseModel):
    """Speech-to-text transcription result"""
    session_id: str = Field(..., description="Conversation session ID")
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Confidence score 0-1")
    language: Optional[str] = Field(None, description="Detected language")
    start_time: float = Field(..., description="Start timestamp")
    end_time: float = Field(..., description="End timestamp")
    words: Optional[List[Dict[str, Any]]] = Field(None, description="Word-level timestamps")
    is_final: bool = Field(True, description="Whether this is the final result")
    
    @property
    def duration(self) -> float:
        """Get transcription duration"""
        return self.end_time - self.start_time


class TTSRequest(BaseModel):
    """Text-to-speech generation request"""
    session_id: str = Field(..., description="Conversation session ID")
    text: str = Field(..., description="Text to synthesize")
    voice_id: Optional[str] = Field(None, description="Voice ID to use")
    language: str = Field("nl", description="Language code")
    gender: Optional[str] = Field("female", description="Voice gender (male/female)")
    speed: float = Field(1.0, description="Speaking speed multiplier")
    emotion: Optional[str] = Field("neutral", description="Emotional tone")
    pitch: Optional[float] = Field(None, description="Pitch adjustment")
    streaming: bool = Field(True, description="Enable streaming synthesis")


class TTSResult(BaseModel):
    """Text-to-speech synthesis result"""
    session_id: str = Field(..., description="Conversation session ID")
    audio_data: bytes = Field(..., description="Generated audio data")
    sample_rate: int = Field(22050, description="Audio sample rate")
    duration: float = Field(..., description="Audio duration in seconds")
    text: str = Field(..., description="Original text")
    voice_id: str = Field(..., description="Voice used for synthesis")
    generation_time: float = Field(..., description="Time taken to generate")
    
    def to_numpy(self) -> np.ndarray:
        """Convert audio data to numpy array"""
        return np.frombuffer(self.audio_data, dtype=np.int16)


class ConversationMessage(BaseModel):
    """Single message in a conversation"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    audio_duration: Optional[float] = Field(None, description="Audio duration if spoken")
    confidence: Optional[float] = Field(None, description="Transcription confidence")


class ConversationSession(BaseModel):
    """Complete conversation session"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    messages: List[ConversationMessage] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    status: str = Field("active", description="Session status: active, paused, ended")
    language: str = Field("nl", description="Conversation language")
    voice_profile: Optional[Dict[str, Any]] = Field(None, description="User voice profile")
    context: Optional[Dict[str, Any]] = Field(None, description="Session context")
    
    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the conversation"""
        message = ConversationMessage(role=role, content=content, **kwargs)
        self.messages.append(message)
        self.last_activity = datetime.now()
        return message
    
    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        """Get recent messages for context"""
        return self.messages[-count:] if count > 0 else self.messages
    
    def get_context_string(self, max_messages: int = 10) -> str:
        """Get conversation context as formatted string"""
        recent_messages = self.get_recent_messages(max_messages)
        context_parts = []
        
        for msg in recent_messages:
            context_parts.append(f"{msg.role}: {msg.content}")
        
        return "\n".join(context_parts)


class VoiceActivityDetection(BaseModel):
    """Voice activity detection result"""
    session_id: str = Field(..., description="Session ID")
    is_speech: bool = Field(..., description="Whether speech was detected")
    confidence: float = Field(..., description="Detection confidence")
    start_time: float = Field(..., description="Speech start timestamp")
    end_time: Optional[float] = Field(None, description="Speech end timestamp")
    audio_level: float = Field(..., description="Audio level/volume")


class ConversationState(BaseModel):
    """Current state of conversation processing"""
    session_id: str = Field(..., description="Session ID")
    is_user_speaking: bool = Field(False, description="User is currently speaking")
    is_ai_speaking: bool = Field(False, description="AI is currently speaking")
    is_processing: bool = Field(False, description="Processing user input")
    last_user_speech: Optional[float] = Field(None, description="Last user speech timestamp")
    last_ai_speech: Optional[float] = Field(None, description="Last AI speech timestamp")
    interruption_count: int = Field(0, description="Number of interruptions")
    
    def reset_speaking_states(self):
        """Reset all speaking states"""
        self.is_user_speaking = False
        self.is_ai_speaking = False
        self.is_processing = False


class InterruptionEvent(BaseModel):
    """User interruption event"""
    session_id: str = Field(..., description="Session ID")
    timestamp: float = Field(..., description="Interruption timestamp")
    user_speech_start: float = Field(..., description="When user started speaking")
    ai_speech_interrupted: bool = Field(..., description="Whether AI was speaking")
    ai_response_partial: Optional[str] = Field(None, description="Partial AI response")
    confidence: float = Field(..., description="Interruption detection confidence")


class WebRTCSessionInfo(BaseModel):
    """WebRTC session information"""
    session_id: str = Field(..., description="Session ID")
    peer_connection_id: str = Field(..., description="WebRTC peer connection ID")
    connection_state: str = Field(..., description="Connection state")
    ice_connection_state: str = Field(..., description="ICE connection state")
    local_description: Optional[str] = Field(None, description="Local SDP")
    remote_description: Optional[str] = Field(None, description="Remote SDP")
    created_at: datetime = Field(default_factory=datetime.now)
    stats: Optional[Dict[str, Any]] = Field(None, description="Connection statistics")


class ProcessingMetrics(BaseModel):
    """Processing performance metrics"""
    session_id: str = Field(..., description="Session ID")
    component: str = Field(..., description="Component name (STT, LLM, TTS)")
    start_time: float = Field(..., description="Processing start timestamp")
    end_time: float = Field(..., description="Processing end timestamp")
    latency_ms: float = Field(..., description="Processing latency in milliseconds")
    input_size: Optional[int] = Field(None, description="Input size in bytes")
    output_size: Optional[int] = Field(None, description="Output size in bytes")
    success: bool = Field(True, description="Whether processing succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @property
    def duration_ms(self) -> float:
        """Get processing duration in milliseconds"""
        return (self.end_time - self.start_time) * 1000


class HealthCheckResult(BaseModel):
    """Health check result for monitoring"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status: healthy, unhealthy, degraded")
    timestamp: datetime = Field(default_factory=datetime.now)
    latency_ms: Optional[float] = Field(None, description="Response latency")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    errors: Optional[List[str]] = Field(None, description="Error messages")


class VoiceVerificationResult(BaseModel):
    """Voice verification result"""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    is_verified: bool = Field(..., description="Whether voice is verified")
    confidence: float = Field(..., description="Verification confidence")
    timestamp: float = Field(..., description="Verification timestamp")
    audio_duration: Optional[float] = Field(None, description="Audio duration used for verification")
    anti_spoofing_result: Optional[bool] = Field(None, description="Anti-spoofing check result")


class VoiceProfile(BaseModel):
    """Voice profile for user"""
    user_id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User name")
    created_at: float = Field(..., description="Profile creation timestamp")
    updated_at: float = Field(..., description="Profile update timestamp")
    verification_count: int = Field(0, description="Number of verification attempts")
    verification_success: int = Field(0, description="Number of successful verifications")
    last_verification: Optional[float] = Field(None, description="Last verification timestamp")
    has_voice_features: bool = Field(False, description="Whether profile has voice features")


class MessageAnalysis(BaseModel):
    """Conversation message analysis"""
    session_id: str = Field(..., description="Session ID")
    message_id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user, assistant)")
    content: str = Field(..., description="Message content")
    timestamp: float = Field(..., description="Message timestamp")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Message analysis")


class ConversationAnalysisResult(BaseModel):
    """Conversation analysis result"""
    session_id: str = Field(..., description="Session ID")
    sentiment: str = Field(..., description="Overall sentiment")
    sentiment_score: float = Field(..., description="Sentiment score")
    topics: List[str] = Field(..., description="Detected topics")
    key_points: List[str] = Field(..., description="Key discussion points")
    user_satisfaction: Optional[float] = Field(None, description="Estimated user satisfaction")
    timestamp: float = Field(..., description="Analysis timestamp")


class EmotionDetectionResult(BaseModel):
    """Emotion detection result"""
    session_id: str = Field(..., description="Session ID")
    emotion: str = Field(..., description="Detected emotion")
    confidence: float = Field(..., description="Detection confidence")
    timestamp: float = Field(..., description="Detection timestamp")
    audio_duration: Optional[float] = Field(None, description="Audio duration analyzed")
    secondary_emotions: Optional[Dict[str, float]] = Field(None, description="Secondary emotions with scores")


class TranslationRequest(BaseModel):
    """Translation request"""
    text: str = Field(..., description="Text to translate")
    source_language: Optional[str] = Field(None, description="Source language code")
    target_language: str = Field(..., description="Target language code")
    preserve_formatting: bool = Field(True, description="Preserve formatting")
    context: Optional[str] = Field(None, description="Translation context")


class TranslationResult(BaseModel):
    """Translation result"""
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")
    confidence: float = Field(..., description="Translation confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    detected_language: Optional[str] = Field(None, description="Detected language if auto-detected")


class AccentDetectionResult(BaseModel):
    """Accent detection result"""
    session_id: str = Field(..., description="Session ID")
    language: str = Field(..., description="Language code")
    accent: str = Field(..., description="Detected accent")
    confidence: float = Field(..., description="Detection confidence")
    timestamp: float = Field(..., description="Detection timestamp")
    audio_duration: Optional[float] = Field(None, description="Audio duration analyzed")
    alternative_accents: Optional[Dict[str, float]] = Field(None, description="Alternative accents with scores")