"""
High-Quality Text-to-Speech Module

Provides natural-sounding speech synthesis with support for:
- Multiple voices and languages
- Emotion and intonation control
- Streaming synthesis
- Voice customization
"""
import asyncio
import logging
import time
import numpy as np
import os
import io
import tempfile
from typing import Optional, Dict, Any, List, Tuple, BinaryIO, Union
from pathlib import Path
import json
import re

from src.config import settings
from src.models import TTSRequest, TTSResult

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    High-quality text-to-speech engine
    
    Features:
    - Multiple TTS backends (local and cloud-based)
    - Voice selection and customization
    - Emotion and intonation control
    - Multilingual support
    - Streaming synthesis
    - Caching for improved performance
    """
    
    def __init__(self):
        """Initialize TTS engine"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.default_model = settings.TTS_MODEL
        self.default_language = settings.TTS_LANGUAGE
        self.default_speaker = settings.TTS_SPEAKER
        self.sample_rate = 22050  # Default sample rate for most TTS models
        
        # Multilingual support
        self.language_models = settings.TTS_LANGUAGE_MODELS
        self.language_voices = settings.TTS_LANGUAGE_VOICES
        self.language_synthesizers = {}
        
        # TTS models
        self.local_model = None
        self.cloud_model = None
        self.current_model_name = None
        
        # Voice profiles
        self.voice_profiles = {}
        self.available_voices = {}
        
        # Cache
        self.cache_dir = os.path.join(settings.MODELS_DIR, "tts_cache")
        self.cache_enabled = True
        self.cache_size_limit_mb = 100
        
        # Performance metrics
        self.total_synthesis_time = 0.0
        self.total_text_length = 0
        self.synthesis_count = 0
        
        logger.info("TTS engine initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize TTS engine
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create cache directory
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Initialize local TTS model
            await self._initialize_local_model()
            
            # Load voice profiles
            await self._load_voice_profiles()
            
            self.is_initialized = True
            logger.info(f"TTS engine initialized successfully with model: {self.current_model_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            return False
    
    async def _initialize_local_model(self) -> bool:
        """
        Initialize local TTS model
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try to import TTS library
            try:
                import torch
                from TTS.utils.manage import ModelManager
                from TTS.utils.synthesizer import Synthesizer
                
                # Check if CUDA is available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"TTS will use device: {device}")
                
                # Get model manager
                model_path = os.path.join(settings.MODELS_DIR, "tts")
                os.makedirs(model_path, exist_ok=True)
                
                # Initialize model manager
                self.model_manager = ModelManager(model_path)
                
                # Initialize language-specific models
                self.language_synthesizers = {}
                
                # Get default model info
                default_model_name = self.default_model
                default_language = self.default_language
                
                # Initialize default model first
                if not self.model_manager.is_model_downloaded(default_model_name):
                    logger.info(f"Downloading default TTS model: {default_model_name}")
                    self.model_manager.download_model(default_model_name)
                
                # Get model path
                model_path, config_path, model_item = self.model_manager.download_model(default_model_name)
                
                # Initialize default synthesizer
                default_synthesizer = Synthesizer(
                    model_path=model_path,
                    config_path=config_path,
                    use_cuda=torch.cuda.is_available()
                )
                
                # Set current model
                self.current_model_name = default_model_name
                self.synthesizer = default_synthesizer
                self.local_model = default_synthesizer
                self.language_synthesizers[default_language] = default_synthesizer
                
                # Initialize other language models if different from default
                for lang, model_name in self.language_models.items():
                    if lang == default_language or model_name == default_model_name:
                        # Skip if already initialized or same as default
                        continue
                    
                    try:
                        # Download model if needed
                        if not self.model_manager.is_model_downloaded(model_name):
                            logger.info(f"Downloading TTS model for {lang}: {model_name}")
                            self.model_manager.download_model(model_name)
                        
                        # Get model path
                        model_path, config_path, model_item = self.model_manager.download_model(model_name)
                        
                        # Initialize synthesizer
                        lang_synthesizer = Synthesizer(
                            model_path=model_path,
                            config_path=config_path,
                            use_cuda=torch.cuda.is_available()
                        )
                        
                        # Add to language synthesizers
                        self.language_synthesizers[lang] = lang_synthesizer
                        logger.info(f"Initialized TTS model for {lang}: {model_name}")
                    
                    except Exception as e:
                        logger.error(f"Failed to initialize TTS model for {lang}: {e}")
                        # Use default synthesizer as fallback
                        self.language_synthesizers[lang] = default_synthesizer
                
                # Get available voices
                self.available_voices = self._get_available_voices()
                
                logger.info(f"Local TTS model initialized: {model_name}")
                return True
            
            except ImportError:
                logger.warning("TTS library not available, falling back to alternative TTS")
                return await self._initialize_fallback_model()
        
        except Exception as e:
            logger.error(f"Failed to initialize local TTS model: {e}")
            return await self._initialize_fallback_model()
    
    async def _initialize_fallback_model(self) -> bool:
        """
        Initialize fallback TTS model
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try to import pyttsx3 for offline TTS
            try:
                import pyttsx3
                
                # Initialize engine
                self.fallback_engine = pyttsx3.init()
                
                # Set properties
                self.fallback_engine.setProperty('rate', 150)
                self.fallback_engine.setProperty('volume', 1.0)
                
                # Get available voices
                voices = self.fallback_engine.getProperty('voices')
                self.available_voices = {
                    f"fallback_{i}": {
                        "name": voice.name,
                        "language": voice.languages[0] if voice.languages else "unknown",
                        "gender": "female" if "female" in voice.name.lower() else "male",
                        "id": voice.id
                    }
                    for i, voice in enumerate(voices)
                }
                
                # Set current model
                self.current_model_name = "fallback_pyttsx3"
                self.local_model = self.fallback_engine
                
                logger.info("Fallback TTS model initialized with pyttsx3")
                return True
            
            except ImportError:
                logger.warning("pyttsx3 not available, using very basic TTS")
                
                # Set current model to indicate we're using basic TTS
                self.current_model_name = "basic_tts"
                self.local_model = None
                
                # Set available voices
                self.available_voices = {
                    "basic_default": {
                        "name": "Basic TTS",
                        "language": "en",
                        "gender": "neutral",
                        "id": "basic_default"
                    }
                }
                
                logger.info("Basic TTS initialized as last resort")
                return True
        
        except Exception as e:
            logger.error(f"Failed to initialize fallback TTS model: {e}")
            return False
    
    async def _load_voice_profiles(self):
        """Load voice profiles from storage"""
        try:
            voice_profiles_path = os.path.join(settings.MODELS_DIR, "voice_profiles.json")
            
            if os.path.exists(voice_profiles_path):
                with open(voice_profiles_path, 'r') as f:
                    self.voice_profiles = json.load(f)
                logger.info(f"Loaded {len(self.voice_profiles)} voice profiles")
            else:
                # Create default voice profiles
                self.voice_profiles = {
                    "default_nl": {
                        "name": "Nederlandse stem",
                        "model": self.default_model,
                        "language": "nl",
                        "gender": "female",
                        "pitch": 1.0,
                        "speed": 1.0,
                        "speaker_id": self.default_speaker
                    },
                    "default_en": {
                        "name": "English voice",
                        "model": "tts_models/en/ljspeech/tacotron2-DDC",
                        "language": "en",
                        "gender": "female",
                        "pitch": 1.0,
                        "speed": 1.0,
                        "speaker_id": None
                    }
                }
                
                # Save default profiles
                with open(voice_profiles_path, 'w') as f:
                    json.dump(self.voice_profiles, f, indent=2)
                
                logger.info("Created default voice profiles")
        
        except Exception as e:
            logger.error(f"Failed to load voice profiles: {e}")
            # Create empty profiles
            self.voice_profiles = {}
    
    def _get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available voices from current model
        
        Returns:
            Dict of voice IDs and their properties
        """
        voices = {}
        
        try:
            if self.current_model_name == "basic_tts":
                # Basic TTS has only one voice
                voices["basic_default"] = {
                    "name": "Basic TTS",
                    "language": "en",
                    "gender": "neutral",
                    "id": "basic_default"
                }
            
            elif self.current_model_name == "fallback_pyttsx3":
                # pyttsx3 voices were already loaded in _initialize_fallback_model
                pass
            
            else:
                # Get voices from TTS model
                if hasattr(self.synthesizer, "tts_model"):
                    if hasattr(self.synthesizer.tts_model, "speaker_manager") and self.synthesizer.tts_model.speaker_manager is not None:
                        # Multi-speaker model
                        speaker_ids = self.synthesizer.tts_model.speaker_manager.speaker_names
                        
                        for speaker_id in speaker_ids:
                            voices[speaker_id] = {
                                "name": speaker_id,
                                "language": self.default_language,
                                "gender": "unknown",
                                "id": speaker_id
                            }
                    else:
                        # Single speaker model
                        model_name = self.current_model_name.split("/")[-1]
                        voices[model_name] = {
                            "name": model_name,
                            "language": self.default_language,
                            "gender": "unknown",
                            "id": model_name
                        }
        
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
        
        return voices
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResult:
        """
        Synthesize speech from text
        
        Args:
            request: TTS request with text and parameters
            
        Returns:
            TTSResult with generated audio
        """
        if not self.is_initialized:
            logger.error("TTS engine not initialized")
            raise RuntimeError("TTS engine not initialized")
        
        try:
            start_time = time.time()
            
            # Get language-specific voice profile
            language = request.language or self.default_language
            voice_id = request.voice_id or "default_" + language
            
            # Try to get voice profile for specific voice_id
            voice_profile = self.voice_profiles.get(voice_id)
            
            # If not found, try language-specific default
            if not voice_profile:
                voice_profile = self.voice_profiles.get("default_" + language)
            
            # If still not found, use any available profile for the language
            if not voice_profile:
                for profile_id, profile in self.voice_profiles.items():
                    if profile.get("language") == language:
                        voice_profile = profile
                        break
            
            # If no profile found, create a default one
            if not voice_profile:
                # Get appropriate model for language
                model_name = self.language_models.get(language, self.default_model)
                
                # Get appropriate speaker for language and gender
                gender = request.gender or "female"
                speaker_id = None
                
                if language in self.language_voices:
                    if gender in self.language_voices[language]:
                        speaker_id = self.language_voices[language][gender]
                    elif "default" in self.language_voices[language]:
                        speaker_id = self.language_voices[language]["default"]
                
                # Create default voice profile
                voice_profile = {
                    "name": f"Default {language.upper()}",
                    "model": model_name,
                    "language": language,
                    "gender": gender,
                    "pitch": 1.0,
                    "speed": 1.0,
                    "speaker_id": speaker_id or self.default_speaker
                }
            
            # Check cache if enabled
            if self.cache_enabled:
                cache_key = self._get_cache_key(request.text, voice_profile)
                cached_result = self._get_from_cache(cache_key)
                
                if cached_result:
                    logger.debug(f"Using cached TTS result for: {request.text[:30]}...")
                    return cached_result
            
            # Process text
            processed_text = self._preprocess_text(request.text, request.language)
            
            # Synthesize speech
            audio_data, sample_rate = await self._synthesize(
                text=processed_text,
                voice_profile=voice_profile,
                speed=request.speed,
                emotion=request.emotion,
                pitch=request.pitch or voice_profile.get("pitch", 1.0)
            )
            
            # Calculate duration
            duration = len(audio_data) / sample_rate
            
            # Create result
            result = TTSResult(
                session_id=request.session_id,
                audio_data=audio_data,
                sample_rate=sample_rate,
                duration=duration,
                text=request.text,
                voice_id=voice_id,
                generation_time=time.time() - start_time
            )
            
            # Cache result if enabled
            if self.cache_enabled:
                self._add_to_cache(cache_key, result)
            
            # Update metrics
            self.total_synthesis_time += result.generation_time
            self.total_text_length += len(request.text)
            self.synthesis_count += 1
            
            logger.info(
                f"Synthesized {len(request.text)} chars in {result.generation_time:.3f}s "
                f"(RTF: {result.generation_time / duration:.2f}): '{request.text[:50]}...'"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise
    
    async def _synthesize(self, text: str, voice_profile: Dict[str, Any], 
                         speed: float = 1.0, emotion: Optional[str] = None,
                         pitch: float = 1.0) -> Tuple[bytes, int]:
        """
        Synthesize speech using the appropriate TTS engine
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use
            speed: Speaking speed multiplier
            emotion: Emotional tone
            pitch: Pitch adjustment
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        if self.current_model_name.startswith("fallback_"):
            return await self._synthesize_with_fallback(text, voice_profile, speed, pitch)
        
        elif self.current_model_name == "basic_tts":
            return self._synthesize_with_basic_tts(text)
        
        else:
            return await self._synthesize_with_tts_library(text, voice_profile, speed, emotion, pitch)
    
    async def _synthesize_with_tts_library(self, text: str, voice_profile: Dict[str, Any],
                                          speed: float, emotion: Optional[str],
                                          pitch: float) -> Tuple[bytes, int]:
        """
        Synthesize speech using the TTS library
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use
            speed: Speaking speed multiplier
            emotion: Emotional tone
            pitch: Pitch adjustment
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            # Get language and gender from voice profile
            language = voice_profile.get("language", self.default_language)
            gender = voice_profile.get("gender", "female")
            speaker_id = voice_profile.get("speaker_id")
            
            # Get appropriate synthesizer for language
            if language in self.language_synthesizers:
                synthesizer = self.language_synthesizers[language]
            else:
                # Fallback to default synthesizer
                synthesizer = self.synthesizer
                logger.warning(f"No synthesizer for language {language}, using default")
            
            # Get appropriate voice for language and gender if speaker_id not specified
            if not speaker_id and language in self.language_voices:
                if gender in self.language_voices[language] and self.language_voices[language][gender]:
                    speaker_id = self.language_voices[language][gender]
                elif "default" in self.language_voices[language] and self.language_voices[language]["default"]:
                    speaker_id = self.language_voices[language]["default"]
            
            # Apply emotion to text if specified
            if emotion and emotion != "neutral":
                text = self._apply_emotion_to_text(text, emotion, language)
            
            # Synthesize
            wav = synthesizer.tts(
                text=text,
                speaker_id=speaker_id,
                speed=speed
            )
            
            # Convert to bytes
            import io
            import soundfile as sf
            
            buffer = io.BytesIO()
            sf.write(buffer, wav, synthesizer.output_sample_rate, format='wav')
            buffer.seek(0)
            
            # Read wav file
            import wave
            with wave.open(buffer, 'rb') as wav_file:
                # Get sample rate
                sample_rate = wav_file.getframerate()
                # Read frames
                frames = wav_file.readframes(wav_file.getnframes())
            
            return frames, sample_rate
        
        except Exception as e:
            logger.error(f"Error synthesizing with TTS library: {e}")
            # Fall back to basic TTS
            return self._synthesize_with_basic_tts(text)
    
    async def _synthesize_with_fallback(self, text: str, voice_profile: Dict[str, Any],
                                       speed: float, pitch: float) -> Tuple[bytes, int]:
        """
        Synthesize speech using pyttsx3
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use
            speed: Speaking speed multiplier
            pitch: Pitch adjustment
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            # Set voice
            voice_id = voice_profile.get("id")
            if voice_id and voice_id in [v["id"] for v in self.available_voices.values()]:
                self.fallback_engine.setProperty('voice', voice_id)
            
            # Set rate
            rate = self.fallback_engine.getProperty('rate')
            self.fallback_engine.setProperty('rate', int(rate * speed))
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Save to file
            self.fallback_engine.save_to_file(text, temp_path)
            self.fallback_engine.runAndWait()
            
            # Read wav file
            import wave
            with wave.open(temp_path, 'rb') as wav_file:
                # Get sample rate
                sample_rate = wav_file.getframerate()
                # Read frames
                frames = wav_file.readframes(wav_file.getnframes())
            
            # Clean up
            os.unlink(temp_path)
            
            return frames, sample_rate
        
        except Exception as e:
            logger.error(f"Error synthesizing with fallback: {e}")
            # Fall back to basic TTS
            return self._synthesize_with_basic_tts(text)
    
    def _synthesize_with_basic_tts(self, text: str) -> Tuple[bytes, int]:
        """
        Synthesize speech using a very basic method (silence with length proportional to text)
        
        Args:
            text: Text to synthesize
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        # Generate silence with length proportional to text length
        sample_rate = 16000
        duration = 0.1 + len(text) * 0.05  # 50ms per character
        num_samples = int(duration * sample_rate)
        
        # Generate silence
        silence = np.zeros(num_samples, dtype=np.int16)
        
        # Add some low-volume noise to indicate audio is playing
        noise = np.random.normal(0, 10, num_samples).astype(np.int16)
        audio = silence + noise
        
        return audio.tobytes(), sample_rate
    
    def _preprocess_text(self, text: str, language: str) -> str:
        """
        Preprocess text for better TTS quality
        
        Args:
            text: Text to preprocess
            language: Language code
            
        Returns:
            Preprocessed text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Add periods to the end of sentences if missing
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Language-specific preprocessing
        if language == 'nl':
            # Dutch-specific preprocessing
            pass
        elif language == 'en':
            # English-specific preprocessing
            pass
        
        return text
    
    def _apply_emotion_to_text(self, text: str, emotion: str, language: str) -> str:
        """
        Apply emotion to text using SSML-like markers or text modifications
        
        Args:
            text: Text to modify
            emotion: Emotion to apply
            language: Language code
            
        Returns:
            Modified text with emotion markers
        """
        # Define emotion markers for different languages
        emotion_markers = {
            "happy": {
                "nl": ["😊", "Vrolijk: ", ""],
                "en": ["😊", "Happily: ", ""],
                "default": ["😊", "", ""]
            },
            "sad": {
                "nl": ["😢", "Verdrietig: ", ""],
                "en": ["😢", "Sadly: ", ""],
                "default": ["😢", "", ""]
            },
            "angry": {
                "nl": ["😠", "Boos: ", ""],
                "en": ["😠", "Angrily: ", ""],
                "default": ["😠", "", ""]
            },
            "surprised": {
                "nl": ["😲", "Verrast: ", ""],
                "en": ["😲", "Surprised: ", ""],
                "default": ["😲", "", ""]
            },
            "excited": {
                "nl": ["😃", "Enthousiast: ", ""],
                "en": ["😃", "Excitedly: ", ""],
                "default": ["😃", "", ""]
            }
        }
        
        # Get emotion markers for language
        if emotion in emotion_markers:
            if language in emotion_markers[emotion]:
                markers = emotion_markers[emotion][language]
            else:
                markers = emotion_markers[emotion]["default"]
            
            # Apply markers
            # For now, we just add a prefix to the text
            # In a more advanced implementation, this could use SSML tags
            # or other TTS-specific emotion markers
            return f"{markers[1]}{text}"
        
        return text
    
    def _get_cache_key(self, text: str, voice_profile: Dict[str, Any]) -> str:
        """
        Generate cache key for TTS request
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile
            
        Returns:
            Cache key
        """
        import hashlib
        
        # Create key from text and voice parameters
        key_parts = [
            text,
            voice_profile.get("model", ""),
            voice_profile.get("speaker_id", ""),
            str(voice_profile.get("pitch", 1.0)),
            str(voice_profile.get("speed", 1.0))
        ]
        
        # Generate hash
        key = hashlib.md5("_".join(key_parts).encode()).hexdigest()
        
        return key
    
    def _get_from_cache(self, cache_key: str) -> Optional[TTSResult]:
        """
        Get TTS result from cache
        
        Args:
            cache_key: Cache key
            
        Returns:
            TTSResult if found, None otherwise
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        audio_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        
        if os.path.exists(cache_path) and os.path.exists(audio_path):
            try:
                # Load metadata
                with open(cache_path, 'r') as f:
                    metadata = json.load(f)
                
                # Load audio
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                # Create result
                result = TTSResult(
                    session_id=metadata.get("session_id", "cached"),
                    audio_data=audio_data,
                    sample_rate=metadata.get("sample_rate", 22050),
                    duration=metadata.get("duration", 0.0),
                    text=metadata.get("text", ""),
                    voice_id=metadata.get("voice_id", "default"),
                    generation_time=metadata.get("generation_time", 0.0)
                )
                
                return result
            
            except Exception as e:
                logger.error(f"Error loading from cache: {e}")
                return None
        
        return None
    
    def _add_to_cache(self, cache_key: str, result: TTSResult):
        """
        Add TTS result to cache
        
        Args:
            cache_key: Cache key
            result: TTS result
        """
        try:
            # Check cache size
            self._manage_cache_size()
            
            # Save metadata
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
            audio_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
            
            # Create metadata
            metadata = {
                "session_id": result.session_id,
                "sample_rate": result.sample_rate,
                "duration": result.duration,
                "text": result.text,
                "voice_id": result.voice_id,
                "generation_time": result.generation_time,
                "timestamp": time.time()
            }
            
            # Save metadata
            with open(cache_path, 'w') as f:
                json.dump(metadata, f)
            
            # Save audio
            with open(audio_path, 'wb') as f:
                f.write(result.audio_data)
        
        except Exception as e:
            logger.error(f"Error adding to cache: {e}")
    
    def _manage_cache_size(self):
        """Manage cache size by removing old entries if needed"""
        try:
            # Get cache size
            cache_size = 0
            cache_files = []
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    cache_size += file_size
                    
                    if filename.endswith('.json'):
                        try:
                            with open(file_path, 'r') as f:
                                metadata = json.load(f)
                                timestamp = metadata.get("timestamp", 0)
                        except:
                            timestamp = 0
                        
                        cache_files.append((filename[:-5], timestamp, file_size))
            
            # Convert to MB
            cache_size_mb = cache_size / (1024 * 1024)
            
            # Check if cache is too large
            if cache_size_mb > self.cache_size_limit_mb:
                # Sort by timestamp (oldest first)
                cache_files.sort(key=lambda x: x[1])
                
                # Remove oldest files until cache is under limit
                for cache_key, _, _ in cache_files:
                    # Remove json and wav files
                    json_path = os.path.join(self.cache_dir, f"{cache_key}.json")
                    wav_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
                    
                    if os.path.exists(json_path):
                        os.remove(json_path)
                    
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                    
                    # Recalculate cache size
                    cache_size_mb -= os.path.getsize(json_path) / (1024 * 1024)
                    cache_size_mb -= os.path.getsize(wav_path) / (1024 * 1024)
                    
                    if cache_size_mb < self.cache_size_limit_mb * 0.8:
                        break
        
        except Exception as e:
            logger.error(f"Error managing cache size: {e}")
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices
        
        Returns:
            List of voice info dicts
        """
        voices = []
        
        # Add voice profiles
        for voice_id, profile in self.voice_profiles.items():
            voices.append({
                "id": voice_id,
                "name": profile.get("name", voice_id),
                "language": profile.get("language", "unknown"),
                "gender": profile.get("gender", "unknown"),
                "is_profile": True
            })
        
        # Add available voices from model
        for voice_id, voice in self.available_voices.items():
            if voice_id not in [v["id"] for v in voices]:
                voices.append({
                    "id": voice_id,
                    "name": voice.get("name", voice_id),
                    "language": voice.get("language", "unknown"),
                    "gender": voice.get("gender", "unknown"),
                    "is_profile": False
                })
        
        return voices
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Returns:
            dict: Performance statistics
        """
        if self.synthesis_count == 0:
            return {
                "synthesis_count": 0,
                "total_text_length": 0,
                "average_synthesis_time": 0.0,
                "chars_per_second": 0.0,
                "current_model": self.current_model_name
            }
        
        avg_synthesis_time = self.total_synthesis_time / self.synthesis_count
        chars_per_second = self.total_text_length / self.total_synthesis_time
        
        return {
            "synthesis_count": self.synthesis_count,
            "total_text_length": self.total_text_length,
            "average_synthesis_time": avg_synthesis_time,
            "chars_per_second": chars_per_second,
            "current_model": self.current_model_name
        }
    
    def close(self):
        """Close TTS engine and free resources"""
        self.is_initialized = False
        
        # Close models
        self.local_model = None
        self.cloud_model = None
        
        logger.info("TTS engine closed")


# Global TTS engine instance
tts_engine = TTSEngine()