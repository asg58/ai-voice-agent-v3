"""
Language Detection Module

Detects the language of spoken audio or text input.
Supports multiple detection methods and confidence scoring.
"""
import asyncio
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
import re
import json
from collections import Counter

from src.config import settings
from src.models import AudioChunk, TranscriptionResult

logger = logging.getLogger(__name__)

# Language codes and names mapping
LANGUAGE_CODES = {
    "nl": "Dutch",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish"
}

# Common words and phrases for language detection
LANGUAGE_MARKERS = {
    "nl": ["de", "het", "een", "ik", "jij", "wij", "zij", "hoe", "wat", "waarom", "wanneer", "waar", "wie", "welke", "goedemorgen", "goedemiddag", "goedenavond", "dankjewel", "alsjeblieft", "hallo", "dag", "doei"],
    "en": ["the", "a", "an", "I", "you", "we", "they", "how", "what", "why", "when", "where", "who", "which", "good morning", "good afternoon", "good evening", "thank you", "please", "hello", "hi", "bye"],
    "de": ["der", "die", "das", "ein", "eine", "ich", "du", "wir", "sie", "wie", "was", "warum", "wann", "wo", "wer", "welche", "guten morgen", "guten tag", "guten abend", "danke", "bitte", "hallo", "tschüss"],
    "fr": ["le", "la", "les", "un", "une", "je", "tu", "nous", "ils", "elles", "comment", "quoi", "pourquoi", "quand", "où", "qui", "quel", "bonjour", "bonsoir", "merci", "s'il vous plaît", "salut", "au revoir"],
    "es": ["el", "la", "los", "las", "un", "una", "yo", "tú", "nosotros", "ellos", "ellas", "cómo", "qué", "por qué", "cuándo", "dónde", "quién", "cuál", "buenos días", "buenas tardes", "buenas noches", "gracias", "por favor", "hola", "adiós"]
}

# Character frequency patterns for languages
CHAR_PATTERNS = {
    "nl": {"ij", "aa", "ee", "oo", "uu", "eu", "oe", "ui", "ou"},
    "en": {"th", "wh", "sh", "ch", "ph", "gh", "qu", "ck", "ng"},
    "de": {"sch", "ch", "ck", "tz", "ei", "ie", "eu", "äu", "ß"},
    "fr": {"ou", "au", "ai", "eu", "oi", "qu", "gn", "ç", "é", "è", "ê", "à", "ù"},
    "es": {"ñ", "ll", "rr", "ch", "qu", "á", "é", "í", "ó", "ú", "¿", "¡"}
}


class LanguageDetector:
    """
    Language detection for audio and text
    
    Features:
    - Multiple detection methods (text analysis, audio features)
    - Confidence scoring
    - Language identification
    - Support for multiple languages
    - Adaptive detection based on conversation context
    """
    
    def __init__(self):
        """Initialize language detector"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.default_language = self.config.stt_language
        self.supported_languages = set(lang for lang in self.config.supported_languages if lang in LANGUAGE_CODES)
        self.session_languages = {}
        self.min_confidence = self.config.language_detection_min_confidence
        self.history_weight = 0.3
        self.enabled = self.config.language_detection_enabled
        
        # Language detection models
        self.text_model = None
        self.audio_model = None
        
        logger.info(f"Language detector initialized with default language: {self.default_language}")
        logger.info(f"Supported languages: {', '.join(self.supported_languages)}")
        logger.info(f"Language detection enabled: {self.enabled}")
    
    async def initialize(self) -> bool:
        """
        Initialize language detector
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize text-based language detection
            try:
                import fasttext
                # Check if model exists, if not download it
                model_path = f"{settings.MODELS_DIR}/lid.176.bin"
                import os
                if not os.path.exists(model_path):
                    logger.info("Downloading FastText language detection model...")
                    import urllib.request
                    os.makedirs(settings.MODELS_DIR, exist_ok=True)
                    urllib.request.urlretrieve(
                        "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin", 
                        model_path
                    )
                
                # Load model
                self.text_model = fasttext.load_model(model_path)
                logger.info("FastText language detection model loaded")
            except ImportError:
                logger.warning("FastText not available, using fallback language detection")
                self.text_model = None
            
            # Initialize audio-based language detection if available
            # This would typically use a specialized model for audio language ID
            # For now, we'll rely on text-based detection after transcription
            
            self.is_initialized = True
            logger.info("Language detector initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize language detector: {e}")
            return False
    
    async def detect_language(self, text: str, session_id: Optional[str] = None) -> Tuple[str, float]:
        """
        Detect language from text
        
        Args:
            text: Text to detect language from
            session_id: Session ID for context-aware detection
            
        Returns:
            Tuple of (language_code, confidence)
        """
        # If language detection is disabled, return default language
        if not self.enabled:
            return self.default_language, 1.0
            
        if not text or len(text.strip()) < 3:
            # Text too short, return default or session language
            if session_id and session_id in self.session_languages:
                return self.session_languages[session_id], 0.5
            return self.default_language, 0.5
        
        # Clean text
        text = text.lower().strip()
        
        # Get previous language for this session
        previous_lang = None
        previous_confidence = 0.0
        if session_id and session_id in self.session_languages:
            previous_lang = self.session_languages[session_id]
        
        # Try multiple detection methods and combine results
        results = {}
        
        # Method 1: FastText model (if available)
        if self.text_model:
            try:
                # Get prediction
                predictions = self.text_model.predict(text, k=3)
                labels, scores = predictions
                
                # Extract language codes and scores
                for i, label in enumerate(labels):
                    lang_code = label.replace("__label__", "")
                    if lang_code in self.supported_languages:
                        results[lang_code] = scores[i]
            except Exception as e:
                logger.error(f"Error in FastText language detection: {e}")
        
        # Method 2: Common word detection
        word_scores = self._detect_language_from_words(text)
        for lang, score in word_scores.items():
            if lang in results:
                results[lang] = max(results[lang], score * 0.8)  # Weight slightly less than FastText
            else:
                results[lang] = score * 0.8
        
        # Method 3: Character pattern detection
        char_scores = self._detect_language_from_chars(text)
        for lang, score in char_scores.items():
            if lang in results:
                results[lang] = max(results[lang], score * 0.7)  # Weight less than word detection
            else:
                results[lang] = score * 0.7
        
        # If no results, return default language
        if not results:
            if previous_lang:
                return previous_lang, 0.5
            return self.default_language, 0.5
        
        # Get best language
        best_lang = max(results, key=results.get)
        confidence = results[best_lang]
        
        # Apply session history weighting if available
        if previous_lang:
            if previous_lang in results:
                # Blend with previous language
                if previous_lang == best_lang:
                    # Same language, increase confidence
                    confidence = min(1.0, confidence + 0.1)
                else:
                    # Different language, check if it's close
                    prev_score = results[previous_lang]
                    if prev_score > confidence * 0.8:
                        # Previous language is close, stick with it unless very confident
                        if confidence < 0.8:
                            best_lang = previous_lang
                            confidence = prev_score
        
        # Update session language
        if session_id:
            self.session_languages[session_id] = best_lang
        
        # Log detection
        logger.debug(f"Detected language: {best_lang} ({LANGUAGE_CODES.get(best_lang, 'Unknown')}) with confidence {confidence:.2f}")
        
        return best_lang, confidence
    
    def _detect_language_from_words(self, text: str) -> Dict[str, float]:
        """
        Detect language based on common words and phrases
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict of language codes and confidence scores
        """
        # Split text into words
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return {}
        
        # Count words for each language
        lang_counts = {lang: 0 for lang in LANGUAGE_MARKERS}
        lang_weights = {lang: 0 for lang in LANGUAGE_MARKERS}
        
        # Check each word
        for word in words:
            for lang, markers in LANGUAGE_MARKERS.items():
                if word in markers:
                    lang_counts[lang] += 1
                    # Weight by word length (longer words are more distinctive)
                    lang_weights[lang] += len(word) / 3
        
        # Calculate scores
        total_words = len(words)
        results = {}
        
        for lang, count in lang_counts.items():
            if count > 0:
                # Score based on percentage of matched words and their weights
                score = (count / total_words) * 0.7 + (lang_weights[lang] / (total_words * 2)) * 0.3
                results[lang] = min(1.0, score * 2)  # Scale up but cap at 1.0
        
        return results
    
    def _detect_language_from_chars(self, text: str) -> Dict[str, float]:
        """
        Detect language based on character patterns
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict of language codes and confidence scores
        """
        text = text.lower()
        results = {lang: 0 for lang in CHAR_PATTERNS}
        
        # Count pattern occurrences
        for lang, patterns in CHAR_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                matches += text.count(pattern)
            
            # Calculate score based on text length
            if matches > 0:
                text_len = max(1, len(text))
                score = min(1.0, matches / (text_len * 0.2))  # Adjust scaling factor
                results[lang] = score
        
        return results
    
    async def detect_language_from_audio(self, audio_chunk: AudioChunk) -> Tuple[str, float]:
        """
        Detect language from audio
        
        Args:
            audio_chunk: Audio chunk to analyze
            
        Returns:
            Tuple of (language_code, confidence)
        """
        # For now, we don't have direct audio language detection
        # This would typically use a specialized model
        # Return default language with low confidence
        if audio_chunk.session_id in self.session_languages:
            return self.session_languages[audio_chunk.session_id], 0.5
        return self.default_language, 0.3
    
    def get_session_language(self, session_id: str) -> str:
        """
        Get detected language for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Language code
        """
        return self.session_languages.get(session_id, self.default_language)
    
    def set_session_language(self, session_id: str, language: str):
        """
        Set language for session
        
        Args:
            session_id: Session ID
            language: Language code
        """
        if language in self.supported_languages:
            self.session_languages[session_id] = language
            logger.info(f"Set session {session_id} language to {language} ({LANGUAGE_CODES.get(language, 'Unknown')})")
        else:
            logger.warning(f"Unsupported language: {language}")
    
    def reset_session(self, session_id: str):
        """
        Reset session language
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_languages:
            del self.session_languages[session_id]
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages
        
        Returns:
            List of language info dicts with code and name
        """
        return [
            {"code": code, "name": name}
            for code, name in LANGUAGE_CODES.items()
            if code in self.supported_languages
        ]
    
    def close(self):
        """Close language detector and free resources"""
        self.session_languages.clear()
        self.text_model = None
        self.audio_model = None
        self.is_initialized = False


# Global language detector instance
language_detector = LanguageDetector()