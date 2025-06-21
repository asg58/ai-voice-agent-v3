"""
Application Settings for AI Voice Agent
"""
import os
import os.path
from typing import List, Dict, Optional
from pydantic import BaseModel

# Application settings
VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Session settings
AUTO_CLOSE_SESSION = os.getenv("AUTO_CLOSE_SESSION", "True").lower() in ("true", "1", "t")
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# Audio settings
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
CHANNELS = int(os.getenv("CHANNELS", "1"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "4096"))

# Audio preprocessing settings
NOISE_REDUCTION_ENABLED = os.getenv("NOISE_REDUCTION_ENABLED", "True").lower() in ("true", "1", "t")
NOISE_REDUCTION_STRENGTH = float(os.getenv("NOISE_REDUCTION_STRENGTH", "1.5"))
VOLUME_NORMALIZATION_ENABLED = os.getenv("VOLUME_NORMALIZATION_ENABLED", "True").lower() in ("true", "1", "t")
TARGET_RMS = float(os.getenv("TARGET_RMS", "3000.0"))
BANDPASS_FILTER_ENABLED = os.getenv("BANDPASS_FILTER_ENABLED", "True").lower() in ("true", "1", "t")

# STT settings
STT_MODEL = os.getenv("STT_MODEL", "base")
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "nl")
STT_STREAMING_ENABLED = os.getenv("STT_STREAMING_ENABLED", "True").lower() in ("true", "1", "t")
STT_MIN_SPEECH_DURATION = float(os.getenv("STT_MIN_SPEECH_DURATION", "0.5"))
STT_SILENCE_THRESHOLD = float(os.getenv("STT_SILENCE_THRESHOLD", "0.8"))
STT_MAX_AUDIO_LENGTH = float(os.getenv("STT_MAX_AUDIO_LENGTH", "30.0"))
STT_VAD_THRESHOLD = float(os.getenv("STT_VAD_THRESHOLD", "0.5"))

# Language detection settings
LANGUAGE_DETECTION_ENABLED = os.getenv("LANGUAGE_DETECTION_ENABLED", "True").lower() in ("true", "1", "t")
LANGUAGE_DETECTION_MIN_CONFIDENCE = float(os.getenv("LANGUAGE_DETECTION_MIN_CONFIDENCE", "0.6"))
SUPPORTED_LANGUAGES = os.getenv("SUPPORTED_LANGUAGES", "nl,en,de,fr,es").split(",")

# Accent adaptation settings
ACCENT_ADAPTATION_ENABLED = os.getenv("ACCENT_ADAPTATION_ENABLED", "True").lower() in ("true", "1", "t")
ACCENT_ADAPTATION_STRENGTH = float(os.getenv("ACCENT_ADAPTATION_STRENGTH", "0.7"))
ACCENT_ADAPTATION_MIN_CONFIDENCE = float(os.getenv("ACCENT_ADAPTATION_MIN_CONFIDENCE", "0.6"))

# Domain-specific STT settings
DOMAIN_SPECIFIC_STT_ENABLED = os.getenv("DOMAIN_SPECIFIC_STT_ENABLED", "True").lower() in ("true", "1", "t")
DOMAIN_SPECIFIC_STT_CONFIDENCE = float(os.getenv("DOMAIN_SPECIFIC_STT_CONFIDENCE", "0.6"))

# Voice verification settings
VOICE_VERIFICATION_ENABLED = os.getenv("VOICE_VERIFICATION_ENABLED", "True").lower() in ("true", "1", "t")
VOICE_VERIFICATION_THRESHOLD = float(os.getenv("VOICE_VERIFICATION_THRESHOLD", "0.7"))
VOICE_VERIFICATION_MIN_DURATION = float(os.getenv("VOICE_VERIFICATION_MIN_DURATION", "3.0"))
ANTI_SPOOFING_ENABLED = os.getenv("ANTI_SPOOFING_ENABLED", "True").lower() in ("true", "1", "t")

# Conversation analysis settings
CONVERSATION_ANALYSIS_ENABLED = os.getenv("CONVERSATION_ANALYSIS_ENABLED", "True").lower() in ("true", "1", "t")
SENTIMENT_ANALYSIS_ENABLED = os.getenv("SENTIMENT_ANALYSIS_ENABLED", "True").lower() in ("true", "1", "t")
TOPIC_DETECTION_ENABLED = os.getenv("TOPIC_DETECTION_ENABLED", "True").lower() in ("true", "1", "t")
INTENT_RECOGNITION_ENABLED = os.getenv("INTENT_RECOGNITION_ENABLED", "True").lower() in ("true", "1", "t")
ENTITY_EXTRACTION_ENABLED = os.getenv("ENTITY_EXTRACTION_ENABLED", "True").lower() in ("true", "1", "t")

# Emotion recognition settings
EMOTION_RECOGNITION_ENABLED = os.getenv("EMOTION_RECOGNITION_ENABLED", "True").lower() in ("true", "1", "t")
AUDIO_EMOTION_ENABLED = os.getenv("AUDIO_EMOTION_ENABLED", "True").lower() in ("true", "1", "t")
TEXT_EMOTION_ENABLED = os.getenv("TEXT_EMOTION_ENABLED", "True").lower() in ("true", "1", "t")
MULTIMODAL_EMOTION_ENABLED = os.getenv("MULTIMODAL_EMOTION_ENABLED", "True").lower() in ("true", "1", "t")

# Translation settings
TRANSLATION_ENABLED = os.getenv("TRANSLATION_ENABLED", "True").lower() in ("true", "1", "t")
AUTO_TRANSLATION_ENABLED = os.getenv("AUTO_TRANSLATION_ENABLED", "False").lower() in ("true", "1", "t")
DEFAULT_TARGET_LANGUAGE = os.getenv("DEFAULT_TARGET_LANGUAGE", "nl")

# TTS settings
TTS_MODEL = os.getenv("TTS_MODEL", "tts_models/nl/css10/vits")
TTS_SPEAKER = os.getenv("TTS_SPEAKER", None)
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "nl")

# Multilingual TTS settings
TTS_LANGUAGE_MODELS = {
    "nl": os.getenv("TTS_MODEL_NL", "tts_models/nl/css10/vits"),
    "en": os.getenv("TTS_MODEL_EN", "tts_models/en/ljspeech/tacotron2-DDC"),
    "de": os.getenv("TTS_MODEL_DE", "tts_models/de/thorsten/tacotron2-DDC"),
    "fr": os.getenv("TTS_MODEL_FR", "tts_models/fr/mai/tacotron2-DDC"),
    "es": os.getenv("TTS_MODEL_ES", "tts_models/es/mai/tacotron2-DDC")
}

TTS_LANGUAGE_VOICES = {
    "nl": {
        "male": os.getenv("TTS_VOICE_NL_MALE", None),
        "female": os.getenv("TTS_VOICE_NL_FEMALE", None),
        "default": os.getenv("TTS_VOICE_NL_DEFAULT", None)
    },
    "en": {
        "male": os.getenv("TTS_VOICE_EN_MALE", None),
        "female": os.getenv("TTS_VOICE_EN_FEMALE", None),
        "default": os.getenv("TTS_VOICE_EN_DEFAULT", None)
    },
    "de": {
        "male": os.getenv("TTS_VOICE_DE_MALE", None),
        "female": os.getenv("TTS_VOICE_DE_FEMALE", None),
        "default": os.getenv("TTS_VOICE_DE_DEFAULT", None)
    },
    "fr": {
        "male": os.getenv("TTS_VOICE_FR_MALE", None),
        "female": os.getenv("TTS_VOICE_FR_FEMALE", None),
        "default": os.getenv("TTS_VOICE_FR_DEFAULT", None)
    },
    "es": {
        "male": os.getenv("TTS_VOICE_ES_MALE", None),
        "female": os.getenv("TTS_VOICE_ES_FEMALE", None),
        "default": os.getenv("TTS_VOICE_ES_DEFAULT", None)
    }
}

# LLM settings
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "256"))
LLM_SYSTEM_PROMPT = os.getenv(
    "LLM_SYSTEM_PROMPT",
    "Je bent een vriendelijke, natuurlijke Nederlandse AI-assistent. "
    "Geef korte, conversationele antwoorden alsof je een echte persoon bent. "
    "Gebruik natuurlijke spraakpatronen en emotie in je antwoorden."
)

# Storage settings
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TEMP_DIR = os.path.join(STORAGE_DIR, "temp")
MODELS_DIR = os.path.join(STORAGE_DIR, "models")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Database settings
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "voice_ai")
DB_USER = os.getenv("DB_USER", "voice_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "voice_pass")

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

# Memory settings
MEMORY_ENABLED = os.getenv("MEMORY_ENABLED", "True").lower() in ("true", "1", "t")
SHORT_TERM_MEMORY_TTL = int(os.getenv("SHORT_TERM_MEMORY_TTL", "1800"))  # 30 minutes
LONG_TERM_MEMORY_ENABLED = os.getenv("LONG_TERM_MEMORY_ENABLED", "True").lower() in ("true", "1", "t")
VECTOR_SEARCH_ENABLED = os.getenv("VECTOR_SEARCH_ENABLED", "True").lower() in ("true", "1", "t")
KNOWLEDGE_GRAPH_ENABLED = os.getenv("KNOWLEDGE_GRAPH_ENABLED", "False").lower() in ("true", "1", "t")

# Vector DB settings
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", "8080"))
WEAVIATE_SCHEME = os.getenv("WEAVIATE_SCHEME", "http")

# Knowledge Graph settings
NEO4J_HOST = os.getenv("NEO4J_HOST", "neo4j")
NEO4J_PORT = int(os.getenv("NEO4J_PORT", "7687"))
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# RabbitMQ settings
RABBITMQ_ENABLED = os.getenv("RABBITMQ_ENABLED", "True").lower() in ("true", "1", "t")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

# Kafka settings
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "True").lower() in ("true", "1", "t")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_TOPIC_PREFIX = os.getenv("KAFKA_TOPIC_PREFIX", "voice.")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "voice-service")

# Create directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Service configuration class
class ServiceConfig(BaseModel):
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "256"))
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Ollama settings
    ollama_base_url: str = OLLAMA_HOST
    ollama_model: str = LLM_MODEL
    
    # Audio settings
    audio_sample_rate: int = SAMPLE_RATE
    audio_channels: int = CHANNELS
    audio_chunk_size: int = CHUNK_SIZE
    
    # Audio preprocessing settings
    noise_reduction_enabled: bool = NOISE_REDUCTION_ENABLED
    noise_reduction_strength: float = NOISE_REDUCTION_STRENGTH
    volume_normalization_enabled: bool = VOLUME_NORMALIZATION_ENABLED
    target_rms: float = TARGET_RMS
    bandpass_filter_enabled: bool = BANDPASS_FILTER_ENABLED
    
    # STT settings
    stt_model: str = STT_MODEL
    stt_language: str = STT_LANGUAGE
    stt_streaming_enabled: bool = STT_STREAMING_ENABLED
    stt_min_speech_duration: float = STT_MIN_SPEECH_DURATION
    stt_silence_threshold: float = STT_SILENCE_THRESHOLD
    stt_max_audio_length: float = STT_MAX_AUDIO_LENGTH
    
    # VAD settings
    vad_threshold: float = STT_VAD_THRESHOLD
    vad_min_speech_duration: float = STT_MIN_SPEECH_DURATION
    vad_max_speech_duration: float = 10.0
    
    # Language detection settings
    language_detection_enabled: bool = LANGUAGE_DETECTION_ENABLED
    language_detection_min_confidence: float = LANGUAGE_DETECTION_MIN_CONFIDENCE
    supported_languages: List[str] = SUPPORTED_LANGUAGES
    
    # Accent adaptation settings
    accent_adaptation_enabled: bool = ACCENT_ADAPTATION_ENABLED
    accent_adaptation_strength: float = ACCENT_ADAPTATION_STRENGTH
    accent_adaptation_min_confidence: float = ACCENT_ADAPTATION_MIN_CONFIDENCE
    
    # Domain-specific STT settings
    domain_specific_stt_enabled: bool = DOMAIN_SPECIFIC_STT_ENABLED
    domain_specific_stt_confidence: float = DOMAIN_SPECIFIC_STT_CONFIDENCE
    
    # Voice verification settings
    voice_verification_enabled: bool = VOICE_VERIFICATION_ENABLED
    voice_verification_threshold: float = VOICE_VERIFICATION_THRESHOLD
    voice_verification_min_duration: float = VOICE_VERIFICATION_MIN_DURATION
    anti_spoofing_enabled: bool = ANTI_SPOOFING_ENABLED
    
    # Conversation analysis settings
    conversation_analysis_enabled: bool = CONVERSATION_ANALYSIS_ENABLED
    sentiment_analysis_enabled: bool = SENTIMENT_ANALYSIS_ENABLED
    topic_detection_enabled: bool = TOPIC_DETECTION_ENABLED
    intent_recognition_enabled: bool = INTENT_RECOGNITION_ENABLED
    entity_extraction_enabled: bool = ENTITY_EXTRACTION_ENABLED
    
    # Emotion recognition settings
    emotion_recognition_enabled: bool = EMOTION_RECOGNITION_ENABLED
    audio_emotion_enabled: bool = AUDIO_EMOTION_ENABLED
    text_emotion_enabled: bool = TEXT_EMOTION_ENABLED
    multimodal_emotion_enabled: bool = MULTIMODAL_EMOTION_ENABLED
    
    # Translation settings
    translation_enabled: bool = TRANSLATION_ENABLED
    auto_translation_enabled: bool = AUTO_TRANSLATION_ENABLED
    default_target_language: str = DEFAULT_TARGET_LANGUAGE
      # TTS settings
    tts_model: str = TTS_MODEL
    tts_speaker: Optional[str] = TTS_SPEAKER
    tts_language: str = TTS_LANGUAGE
    tts_language_models: Dict[str, str] = TTS_LANGUAGE_MODELS
      # Memory settings
    MEMORY_ENABLED: bool = MEMORY_ENABLED
    SHORT_TERM_MEMORY_TTL: int = SHORT_TERM_MEMORY_TTL
    LONG_TERM_MEMORY_ENABLED: bool = LONG_TERM_MEMORY_ENABLED
    VECTOR_SEARCH_ENABLED: bool = VECTOR_SEARCH_ENABLED
    KNOWLEDGE_GRAPH_ENABLED: bool = KNOWLEDGE_GRAPH_ENABLED
    
    # RabbitMQ settings
    rabbitmq_enabled: bool = RABBITMQ_ENABLED
    rabbitmq_host: str = RABBITMQ_HOST
    rabbitmq_port: int = RABBITMQ_PORT
    rabbitmq_user: str = RABBITMQ_USER
    rabbitmq_password: str = RABBITMQ_PASSWORD
    rabbitmq_vhost: str = RABBITMQ_VHOST
    
    # Kafka settings
    kafka_enabled: bool = KAFKA_ENABLED
    kafka_bootstrap_servers: List[str] = KAFKA_BOOTSTRAP_SERVERS
    kafka_topic_prefix: str = KAFKA_TOPIC_PREFIX
    kafka_consumer_group: str = KAFKA_CONSUMER_GROUP
    
    # Database settings
    DB_HOST: str = DB_HOST
    DB_PORT: int = DB_PORT
    DB_NAME: str = DB_NAME
    DB_USER: str = DB_USER
    DB_PASSWORD: str = DB_PASSWORD
    
    # Redis settings
    REDIS_HOST: str = REDIS_HOST
    REDIS_PORT: int = REDIS_PORT
    REDIS_DB: int = REDIS_DB
    REDIS_PASSWORD: str = REDIS_PASSWORD
      # Weaviate settings
    WEAVIATE_HOST: str = WEAVIATE_HOST
    WEAVIATE_PORT: int = WEAVIATE_PORT
    WEAVIATE_SCHEME: str = WEAVIATE_SCHEME
    
    # Neo4J settings  
    NEO4J_HOST: str = NEO4J_HOST
    NEO4J_PORT: int = NEO4J_PORT
    NEO4J_USER: str = NEO4J_USER
    NEO4J_PASSWORD: str = NEO4J_PASSWORD
    
    # Debug and general settings
    DEBUG: bool = DEBUG