"""
Translation Module

Provides real-time translation capabilities:
- Text translation between languages
- Speech-to-speech translation
- Language detection and automatic translation
"""
import logging
import time
import os
import json
import asyncio
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import defaultdict

from src.config import settings
from src.models import TranscriptionResult, TTSRequest

logger = logging.getLogger(__name__)


class Translator:
    """
    Translation manager
    
    Features:
    - Text translation between languages
    - Speech-to-speech translation
    - Language detection and automatic translation
    """
    
    def __init__(self):
        """Initialize translation manager"""
        self.is_initialized = False
          # Get config
        self.config = settings
        
        # Configuration
        self.enabled = self.config.translation_enabled
        self.auto_translation_enabled = self.config.auto_translation_enabled
        self.default_target_language = self.config.default_target_language
        
        # Models
        self.translation_model = None
        
        # Session state
        self.session_states = {}
        
        # Supported languages
        self.supported_languages = {
            "en": "English",
            "nl": "Dutch",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "tr": "Turkish",
            "pl": "Polish",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish"
        }
        
        logger.info(f"Translation manager initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> bool:
        """
        Initialize translation manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize translation model
            await self._initialize_translation_model()
            
            self.is_initialized = True
            logger.info("Translation manager initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize translation manager: {e}")
            return False
    
    async def _initialize_translation_model(self):
        """Initialize translation model"""
        try:
            # Try to import transformers for translation
            from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
            
            # Initialize translation pipeline
            try:
                # Try to load Helsinki-NLP/opus-mt-mul-en model
                model_name = "Helsinki-NLP/opus-mt-mul-en"
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                self.translation_model = pipeline(
                    "translation",
                    model=model,
                    tokenizer=tokenizer
                )
                
                logger.info(f"Translation model initialized: {model_name}")
            
            except Exception as e:
                logger.warning(f"Failed to load translation model: {e}")
                logger.warning("Using simplified translation model")
                
                # Define simplified translation function
                def simple_translation(text, src_lang, tgt_lang):
                    # Define translation dictionary
                    translations = {
                        "nl": {
                            "en": {
                                "hallo": "hello",
                                "goedemorgen": "good morning",
                                "goedemiddag": "good afternoon",
                                "goedenavond": "good evening",
                                "tot ziens": "goodbye",
                                "dank je": "thank you",
                                "alstublieft": "please",
                                "ja": "yes",
                                "nee": "no",
                                "help": "help",
                                "ik begrijp het niet": "I don't understand",
                                "hoe gaat het": "how are you",
                                "het gaat goed": "I'm fine",
                                "wat is je naam": "what is your name",
                                "mijn naam is": "my name is"
                            }
                        },
                        "en": {
                            "nl": {
                                "hello": "hallo",
                                "good morning": "goedemorgen",
                                "good afternoon": "goedemiddag",
                                "good evening": "goedenavond",
                                "goodbye": "tot ziens",
                                "thank you": "dank je",
                                "please": "alstublieft",
                                "yes": "ja",
                                "no": "nee",
                                "help": "help",
                                "I don't understand": "ik begrijp het niet",
                                "how are you": "hoe gaat het",
                                "I'm fine": "het gaat goed",
                                "what is your name": "wat is je naam",
                                "my name is": "mijn naam is"
                            }
                        }
                    }
                    
                    # Check if source and target languages are supported
                    if src_lang not in translations or tgt_lang not in translations[src_lang]:
                        return text
                    
                    # Get translation dictionary
                    translation_dict = translations[src_lang][tgt_lang]
                    
                    # Translate text
                    translated_text = text
                    for src_word, tgt_word in translation_dict.items():
                        translated_text = translated_text.replace(src_word, tgt_word)
                    
                    return translated_text
                
                self.translation_model = simple_translation
                logger.info("Simplified translation model initialized")
        
        except ImportError:
            logger.warning("Transformers not available, using simplified translation")
            
            # Define simplified translation function
            def simple_translation(text, src_lang, tgt_lang):
                # Define translation dictionary
                translations = {
                    "nl": {
                        "en": {
                            "hallo": "hello",
                            "goedemorgen": "good morning",
                            "goedemiddag": "good afternoon",
                            "goedenavond": "good evening",
                            "tot ziens": "goodbye",
                            "dank je": "thank you",
                            "alstublieft": "please",
                            "ja": "yes",
                            "nee": "no",
                            "help": "help",
                            "ik begrijp het niet": "I don't understand",
                            "hoe gaat het": "how are you",
                            "het gaat goed": "I'm fine",
                            "wat is je naam": "what is your name",
                            "mijn naam is": "my name is"
                        }
                    },
                    "en": {
                        "nl": {
                            "hello": "hallo",
                            "good morning": "goedemorgen",
                            "good afternoon": "goedemiddag",
                            "good evening": "goedenavond",
                            "goodbye": "tot ziens",
                            "thank you": "dank je",
                            "please": "alstublieft",
                            "yes": "ja",
                            "no": "nee",
                            "help": "help",
                            "I don't understand": "ik begrijp het niet",
                            "how are you": "hoe gaat het",
                            "I'm fine": "het gaat goed",
                            "what is your name": "wat is je naam",
                            "my name is": "mijn naam is"
                        }
                    }
                }
                
                # Check if source and target languages are supported
                if src_lang not in translations or tgt_lang not in translations[src_lang]:
                    return text
                
                # Get translation dictionary
                translation_dict = translations[src_lang][tgt_lang]
                
                # Translate text
                translated_text = text
                for src_word, tgt_word in translation_dict.items():
                    translated_text = translated_text.replace(src_word, tgt_word)
                
                return translated_text
            
            self.translation_model = simple_translation
            logger.info("Simplified translation model initialized")
    
    async def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translated text
        """
        if not self.is_initialized or not self.enabled:
            return text
        
        try:
            # Check if languages are supported
            if source_language not in self.supported_languages:
                logger.warning(f"Source language not supported: {source_language}")
                return text
            
            if target_language not in self.supported_languages:
                logger.warning(f"Target language not supported: {target_language}")
                return text
            
            # Check if languages are the same
            if source_language == target_language:
                return text
            
            # Translate text
            if callable(self.translation_model):
                # Simple translation function
                translated_text = self.translation_model(text, source_language, target_language)
            else:
                # Transformers pipeline
                result = self.translation_model(
                    text,
                    src_lang=source_language,
                    tgt_lang=target_language
                )
                
                if isinstance(result, list) and len(result) > 0:
                    translated_text = result[0]["translation_text"]
                else:
                    translated_text = text
            
            logger.info(f"Translated text from {source_language} to {target_language}: {text[:30]}... -> {translated_text[:30]}...")
            
            return translated_text
        
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return text
    
    async def translate_transcription(self, transcription: TranscriptionResult, target_language: str) -> TranscriptionResult:
        """
        Translate transcription to target language
        
        Args:
            transcription: Transcription result
            target_language: Target language code
            
        Returns:
            Translated transcription result
        """
        if not self.is_initialized or not self.enabled:
            return transcription
        
        try:
            # Get source language
            source_language = transcription.language or "nl"
            
            # Check if languages are the same
            if source_language == target_language:
                return transcription
            
            # Translate text
            translated_text = await self.translate_text(
                transcription.text,
                source_language,
                target_language
            )
            
            # Create new transcription result
            translated_transcription = TranscriptionResult(
                session_id=transcription.session_id,
                text=translated_text,
                language=target_language,
                confidence=transcription.confidence,
                is_final=transcription.is_final,
                start_time=transcription.start_time,
                end_time=transcription.end_time,
                words=transcription.words,
                metadata=transcription.metadata
            )
            
            # Add original text to metadata
            if not translated_transcription.metadata:
                translated_transcription.metadata = {}
            
            translated_transcription.metadata["original_text"] = transcription.text
            translated_transcription.metadata["original_language"] = source_language
            
            return translated_transcription
        
        except Exception as e:
            logger.error(f"Error translating transcription: {e}")
            return transcription
    
    async def translate_tts_request(self, tts_request: TTSRequest, target_language: str) -> TTSRequest:
        """
        Translate TTS request to target language
        
        Args:
            tts_request: TTS request
            target_language: Target language code
            
        Returns:
            Translated TTS request
        """
        if not self.is_initialized or not self.enabled:
            return tts_request
        
        try:
            # Get source language
            source_language = tts_request.language or "nl"
            
            # Check if languages are the same
            if source_language == target_language:
                return tts_request
            
            # Translate text
            translated_text = await self.translate_text(
                tts_request.text,
                source_language,
                target_language
            )
            
            # Create new TTS request
            translated_tts_request = TTSRequest(
                session_id=tts_request.session_id,
                text=translated_text,
                language=target_language,
                voice=tts_request.voice,
                speed=tts_request.speed,
                pitch=tts_request.pitch,
                metadata=tts_request.metadata
            )
            
            # Add original text to metadata
            if not translated_tts_request.metadata:
                translated_tts_request.metadata = {}
            
            translated_tts_request.metadata["original_text"] = tts_request.text
            translated_tts_request.metadata["original_language"] = source_language
            
            return translated_tts_request
        
        except Exception as e:
            logger.error(f"Error translating TTS request: {e}")
            return tts_request
    
    def get_session_target_language(self, session_id: str) -> str:
        """
        Get target language for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Target language code
        """
        if not self.is_initialized or not self.enabled:
            return self.default_target_language
        
        try:
            # Check if session exists
            if session_id not in self.session_states:
                return self.default_target_language
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Get target language
            target_language = session_state.get("target_language", self.default_target_language)
            
            return target_language
        
        except Exception as e:
            logger.error(f"Error getting session target language: {e}")
            return self.default_target_language
    
    def set_session_target_language(self, session_id: str, target_language: str) -> bool:
        """
        Set target language for session
        
        Args:
            session_id: Session ID
            target_language: Target language code
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized or not self.enabled:
            return False
        
        try:
            # Check if language is supported
            if target_language not in self.supported_languages:
                logger.warning(f"Target language not supported: {target_language}")
                return False
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Set target language
            session_state["target_language"] = target_language
            
            logger.info(f"Set session {session_id} target language to {target_language}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting session target language: {e}")
            return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported languages
        
        Returns:
            Dict of language codes and names
        """
        return self.supported_languages
    
    def _create_session_state(self, session_id: str):
        """
        Create session state
        
        Args:
            session_id: Session ID
        """
        self.session_states[session_id] = {
            "target_language": self.default_target_language,
            "auto_translation": self.auto_translation_enabled,
            "last_activity": time.time()
        }
    
    def reset_session(self, session_id: str):
        """
        Reset session state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
    
    def close(self):
        """Close translation manager and free resources"""
        self.session_states.clear()
        self.is_initialized = False
        logger.info("Translation manager closed")


# Global translation manager instance
translator = Translator()