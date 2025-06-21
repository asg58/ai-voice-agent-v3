"""
Accent Adaptation Module

Provides accent adaptation capabilities for improved speech recognition:
- Accent detection
- Speaker adaptation
- Pronunciation modeling
- Dialect handling
"""
import logging
import time
import numpy as np
import os
import json
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import defaultdict

from src.config import settings
from src.models import AudioChunk, TranscriptionResult

logger = logging.getLogger(__name__)


class AccentAdaptationManager:
    """
    Accent adaptation manager for improved speech recognition
    
    Features:
    - Accent detection
    - Speaker adaptation
    - Pronunciation modeling
    - Dialect handling
    """
    
    def __init__(self):
        """Initialize accent adaptation manager"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.enabled = self.config.accent_adaptation_enabled
        self.adaptation_strength = self.config.accent_adaptation_strength
        self.min_confidence = self.config.accent_adaptation_min_confidence
        
        # Accent profiles
        self.accent_profiles_dir = os.path.join(settings.MODELS_DIR, "accent_profiles")
        self.accent_profiles = {}
        self.session_accents = {}
        
        # Common pronunciation variations by accent/dialect
        self.pronunciation_maps = {
            "nl": {  # Dutch
                "standard": {},  # Standard Dutch (ABN)
                "flemish": {  # Flemish accent
                    "g": "h",
                    "ch": "h",
                    "ij": "ie"
                },
                "limburg": {  # Limburg accent
                    "g": "ch",
                    "v": "f",
                    "z": "s"
                },
                "brabant": {  # Brabant accent
                    "ij": "è",
                    "ui": "ù"
                },
                "amsterdam": {  # Amsterdam accent
                    "z": "s",
                    "v": "f"
                }
            },
            "en": {  # English
                "standard": {},  # Standard English
                "british": {
                    "r": "",  # Non-rhotic
                    "a": "ah"
                },
                "american": {
                    "t": "d",  # Flapping
                    "tt": "d"
                },
                "scottish": {
                    "o": "oe",
                    "u": "oo"
                }
            }
        }
        
        # Common word variations by accent/dialect
        self.word_maps = {
            "nl": {
                "standard": {},
                "flemish": {
                    "dat": "da",
                    "wat": "wa",
                    "niet": "nie"
                },
                "limburg": {
                    "mijn": "mien",
                    "zijn": "zien"
                },
                "brabant": {
                    "jij": "gij",
                    "jullie": "gullie"
                }
            },
            "en": {
                "standard": {},
                "british": {
                    "elevator": "lift",
                    "apartment": "flat"
                },
                "american": {
                    "lift": "elevator",
                    "flat": "apartment"
                }
            }
        }
        
        # Session state
        self.session_states = {}
        
        logger.info(f"Accent adaptation manager initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> bool:
        """
        Initialize accent adaptation manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create accent profiles directory
            os.makedirs(self.accent_profiles_dir, exist_ok=True)
            
            # Load accent profiles
            await self._load_accent_profiles()
            
            self.is_initialized = True
            logger.info("Accent adaptation manager initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize accent adaptation manager: {e}")
            return False
    
    async def _load_accent_profiles(self):
        """Load accent profiles from storage"""
        try:
            # Load global accent profiles
            profiles_path = os.path.join(self.accent_profiles_dir, "global_profiles.json")
            
            if os.path.exists(profiles_path):
                with open(profiles_path, 'r') as f:
                    self.accent_profiles = json.load(f)
                logger.info(f"Loaded {len(self.accent_profiles)} global accent profiles")
            else:
                # Create default accent profiles
                self.accent_profiles = {
                    "nl_standard": {
                        "language": "nl",
                        "accent": "standard",
                        "word_replacements": {},
                        "phoneme_replacements": {},
                        "confidence": 1.0
                    },
                    "nl_flemish": {
                        "language": "nl",
                        "accent": "flemish",
                        "word_replacements": self.word_maps["nl"]["flemish"],
                        "phoneme_replacements": self.pronunciation_maps["nl"]["flemish"],
                        "confidence": 1.0
                    },
                    "en_standard": {
                        "language": "en",
                        "accent": "standard",
                        "word_replacements": {},
                        "phoneme_replacements": {},
                        "confidence": 1.0
                    },
                    "en_british": {
                        "language": "en",
                        "accent": "british",
                        "word_replacements": self.word_maps["en"]["british"],
                        "phoneme_replacements": self.pronunciation_maps["en"]["british"],
                        "confidence": 1.0
                    }
                }
                
                # Save default profiles
                with open(profiles_path, 'w') as f:
                    json.dump(self.accent_profiles, f, indent=2)
                
                logger.info("Created default accent profiles")
            
            # Load session-specific accent profiles
            for filename in os.listdir(self.accent_profiles_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]  # Remove "session_" prefix and ".json" suffix
                    
                    with open(os.path.join(self.accent_profiles_dir, filename), 'r') as f:
                        profile = json.load(f)
                    
                    self.session_accents[session_id] = profile
                    logger.debug(f"Loaded accent profile for session {session_id}")
        
        except Exception as e:
            logger.error(f"Failed to load accent profiles: {e}")
            # Create empty profiles
            self.accent_profiles = {}
    
    async def process_transcription(self, transcription: TranscriptionResult) -> TranscriptionResult:
        """
        Process transcription with accent adaptation
        
        Args:
            transcription: Transcription result
            
        Returns:
            Adapted transcription result
        """
        if not self.is_initialized or not self.enabled:
            return transcription
        
        try:
            # Get session ID
            session_id = transcription.session_id
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Get language
            language = transcription.language or "nl"
            
            # Get accent profile
            accent_profile = self._get_session_accent_profile(session_id, language)
            
            # If no accent profile, return original transcription
            if not accent_profile:
                return transcription
            
            # Apply accent adaptation
            adapted_text = self._apply_accent_adaptation(
                transcription.text,
                language,
                accent_profile
            )
            
            # If text changed, create new transcription result
            if adapted_text != transcription.text:
                logger.info(f"Adapted transcription: '{transcription.text}' -> '{adapted_text}'")
                
                # Create new transcription result
                adapted_transcription = TranscriptionResult(
                    session_id=transcription.session_id,
                    text=adapted_text,
                    confidence=transcription.confidence,
                    language=transcription.language,
                    start_time=transcription.start_time,
                    end_time=transcription.end_time,
                    words=transcription.words,
                    is_final=transcription.is_final
                )
                
                return adapted_transcription
            
            return transcription
        
        except Exception as e:
            logger.error(f"Error processing transcription: {e}")
            return transcription
    
    def _create_session_state(self, session_id: str):
        """
        Create session state
        
        Args:
            session_id: Session ID
        """
        self.session_states[session_id] = {
            "accent_profile": None,
            "language": None,
            "accent_confidence": 0.0,
            "word_replacements": {},
            "phoneme_replacements": {},
            "transcription_history": [],
            "last_activity": time.time()
        }
    
    def _get_session_accent_profile(self, session_id: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Get accent profile for session
        
        Args:
            session_id: Session ID
            language: Language code
            
        Returns:
            Accent profile or None
        """
        # Check if session has a specific accent profile
        if session_id in self.session_accents:
            profile = self.session_accents[session_id]
            
            # Check if profile matches language
            if profile.get("language") == language:
                return profile
        
        # Get session state
        session_state = self.session_states[session_id]
        
        # If session state has an accent profile for this language, use it
        if session_state["accent_profile"] and session_state["language"] == language:
            return {
                "language": language,
                "accent": session_state["accent_profile"],
                "word_replacements": session_state["word_replacements"],
                "phoneme_replacements": session_state["phoneme_replacements"],
                "confidence": session_state["accent_confidence"]
            }
        
        # Otherwise, use default accent profile for language
        default_profile_id = f"{language}_standard"
        if default_profile_id in self.accent_profiles:
            return self.accent_profiles[default_profile_id]
        
        # If no default profile, return None
        return None
    
    def _apply_accent_adaptation(self, text: str, language: str, accent_profile: Dict[str, Any]) -> str:
        """
        Apply accent adaptation to text
        
        Args:
            text: Text to adapt
            language: Language code
            accent_profile: Accent profile
            
        Returns:
            Adapted text
        """
        # Get word replacements
        word_replacements = accent_profile.get("word_replacements", {})
        
        # Apply word replacements
        words = text.split()
        for i, word in enumerate(words):
            # Check if word has a replacement
            if word.lower() in word_replacements:
                # Replace with probability based on confidence
                confidence = accent_profile.get("confidence", 0.5)
                if np.random.random() < confidence * self.adaptation_strength:
                    words[i] = word_replacements[word.lower()]
        
        # Join words back into text
        adapted_text = " ".join(words)
        
        return adapted_text
    
    async def detect_accent(self, transcription: TranscriptionResult) -> Tuple[str, float]:
        """
        Detect accent from transcription
        
        Args:
            transcription: Transcription result
            
        Returns:
            Tuple of (accent_name, confidence)
        """
        if not self.is_initialized or not self.enabled:
            return "standard", 0.0
        
        try:
            # Get session ID and language
            session_id = transcription.session_id
            language = transcription.language or "nl"
            
            # Get session state
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            session_state = self.session_states[session_id]
            
            # Add transcription to history
            session_state["transcription_history"].append(transcription.text)
            
            # Keep only last 10 transcriptions
            if len(session_state["transcription_history"]) > 10:
                session_state["transcription_history"] = session_state["transcription_history"][-10:]
            
            # If we don't have enough transcriptions yet, return default
            if len(session_state["transcription_history"]) < 3:
                return "standard", 0.0
            
            # Combine all transcriptions
            all_text = " ".join(session_state["transcription_history"])
            
            # Check for accent markers in text
            accent_scores = self._score_accents(all_text, language)
            
            # Get accent with highest score
            if accent_scores:
                accent, score = max(accent_scores.items(), key=lambda x: x[1])
                
                # Update session state if confidence is high enough
                if score > self.min_confidence:
                    session_state["accent_profile"] = accent
                    session_state["language"] = language
                    session_state["accent_confidence"] = score
                    
                    # Get word and phoneme replacements for this accent
                    if language in self.word_maps and accent in self.word_maps[language]:
                        session_state["word_replacements"] = self.word_maps[language][accent]
                    
                    if language in self.pronunciation_maps and accent in self.pronunciation_maps[language]:
                        session_state["phoneme_replacements"] = self.pronunciation_maps[language][accent]
                    
                    logger.info(f"Detected accent for session {session_id}: {accent} ({score:.2f})")
                
                return accent, score
            
            # If no accent detected, return default
            return "standard", 0.0
        
        except Exception as e:
            logger.error(f"Error detecting accent: {e}")
            return "standard", 0.0
    
    def _score_accents(self, text: str, language: str) -> Dict[str, float]:
        """
        Score text against known accents
        
        Args:
            text: Text to score
            language: Language code
            
        Returns:
            Dict of accent names and scores
        """
        scores = {}
        
        # Check if language is supported
        if language not in self.word_maps:
            return scores
        
        # Get word maps for language
        word_maps = self.word_maps[language]
        
        # Score each accent
        for accent, word_map in word_maps.items():
            if accent == "standard":
                continue
            
            score = 0
            total = 0
            
            # Check for accent-specific words
            words = text.lower().split()
            for word in words:
                for accent_word, standard_word in word_map.items():
                    if word == accent_word:
                        score += 1
                    total += 1
            
            # Calculate score
            if total > 0:
                scores[accent] = score / total
        
        return scores
    
    def set_session_accent(self, session_id: str, accent: str, language: str = "nl") -> bool:
        """
        Set accent for session
        
        Args:
            session_id: Session ID
            accent: Accent name
            language: Language code
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if accent is valid
            if language not in self.word_maps or accent not in self.word_maps[language]:
                logger.error(f"Invalid accent: {accent} for language {language}")
                return False
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Set accent profile
            session_state["accent_profile"] = accent
            session_state["language"] = language
            session_state["accent_confidence"] = 1.0
            
            # Get word and phoneme replacements for this accent
            if language in self.word_maps and accent in self.word_maps[language]:
                session_state["word_replacements"] = self.word_maps[language][accent]
            
            if language in self.pronunciation_maps and accent in self.pronunciation_maps[language]:
                session_state["phoneme_replacements"] = self.pronunciation_maps[language][accent]
            
            # Save session accent profile
            profile = {
                "language": language,
                "accent": accent,
                "word_replacements": session_state["word_replacements"],
                "phoneme_replacements": session_state["phoneme_replacements"],
                "confidence": 1.0
            }
            
            self.session_accents[session_id] = profile
            
            # Save to file
            profile_path = os.path.join(self.accent_profiles_dir, f"session_{session_id}.json")
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            logger.info(f"Set accent for session {session_id}: {accent} ({language})")
            return True
        
        except Exception as e:
            logger.error(f"Error setting session accent: {e}")
            return False
    
    def get_session_accent(self, session_id: str) -> Tuple[str, str, float]:
        """
        Get accent for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Tuple of (accent_name, language, confidence)
        """
        # Check if session has a specific accent profile
        if session_id in self.session_accents:
            profile = self.session_accents[session_id]
            return profile.get("accent", "standard"), profile.get("language", "nl"), profile.get("confidence", 0.0)
        
        # Check if session state has an accent profile
        if session_id in self.session_states:
            session_state = self.session_states[session_id]
            
            if session_state["accent_profile"]:
                return session_state["accent_profile"], session_state["language"], session_state["accent_confidence"]
        
        # Otherwise, return default
        return "standard", "nl", 0.0
    
    def get_supported_accents(self, language: str = None) -> Dict[str, List[str]]:
        """
        Get supported accents
        
        Args:
            language: Language code (optional)
            
        Returns:
            Dict of language codes and accent names
        """
        if language:
            if language in self.word_maps:
                return {language: list(self.word_maps[language].keys())}
            return {language: ["standard"]}
        
        return {lang: list(accents.keys()) for lang, accents in self.word_maps.items()}
    
    def reset_session(self, session_id: str):
        """
        Reset session state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
        
        if session_id in self.session_accents:
            del self.session_accents[session_id]
            
            # Remove session accent profile file
            profile_path = os.path.join(self.accent_profiles_dir, f"session_{session_id}.json")
            if os.path.exists(profile_path):
                os.remove(profile_path)
    
    def close(self):
        """Close accent adaptation manager and free resources"""
        self.session_states.clear()
        self.session_accents.clear()
        self.is_initialized = False
        logger.info("Accent adaptation manager closed")


# Global accent adaptation manager instance
accent_adaptation_manager = AccentAdaptationManager()