"""
Emotion Recognition Module

Provides emotion recognition capabilities:
- Audio-based emotion recognition
- Text-based emotion recognition
- Multimodal emotion recognition
"""
import logging
import time
import os
import json
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import defaultdict

from src.config import settings
from src.models import AudioChunk, TranscriptionResult

logger = logging.getLogger(__name__)


class EmotionRecognition:
    """
    Emotion recognition manager
    
    Features:
    - Audio-based emotion recognition
    - Text-based emotion recognition
    - Multimodal emotion recognition
    """
    
    def __init__(self):
        """Initialize emotion recognition manager"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.enabled = self.config.emotion_recognition_enabled
        self.audio_emotion_enabled = self.config.audio_emotion_enabled
        self.text_emotion_enabled = self.config.text_emotion_enabled
        self.multimodal_emotion_enabled = self.config.multimodal_emotion_enabled
        
        # Models
        self.audio_emotion_model = None
        self.text_emotion_model = None
        self.multimodal_emotion_model = None
        
        # Session state
        self.session_states = {}
        
        # Emotion categories
        self.emotion_categories = [
            "neutral", "happy", "sad", "angry", "fearful", "disgusted", "surprised"
        ]
        
        logger.info(f"Emotion recognition manager initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> bool:
        """
        Initialize emotion recognition manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize models
            if self.audio_emotion_enabled:
                await self._initialize_audio_emotion_model()
            
            if self.text_emotion_enabled:
                await self._initialize_text_emotion_model()
            
            if self.multimodal_emotion_enabled:
                await self._initialize_multimodal_emotion_model()
            
            self.is_initialized = True
            logger.info("Emotion recognition manager initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize emotion recognition manager: {e}")
            return False
    
    async def _initialize_audio_emotion_model(self):
        """Initialize audio-based emotion recognition model"""
        try:
            # Try to import librosa for audio feature extraction
            import librosa
            
            # Define audio emotion recognition function
            def recognize_audio_emotion(audio_data, sample_rate):
                # Convert to float32 if needed
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                
                # Extract features
                # 1. MFCCs (Mel-frequency cepstral coefficients)
                mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
                
                # 2. Chroma features
                chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
                
                # 3. Spectral contrast
                contrast = librosa.feature.spectral_contrast(y=audio_data, sr=sample_rate)
                
                # 4. Tonnetz (tonal centroid features)
                tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(audio_data), sr=sample_rate)
                
                # Compute statistics
                mfccs_mean = np.mean(mfccs, axis=1)
                mfccs_std = np.std(mfccs, axis=1)
                chroma_mean = np.mean(chroma, axis=1)
                contrast_mean = np.mean(contrast, axis=1)
                tonnetz_mean = np.mean(tonnetz, axis=1)
                
                # Combine features
                features = np.concatenate([
                    mfccs_mean, mfccs_std, chroma_mean, contrast_mean, tonnetz_mean
                ])
                
                # Simple rule-based emotion recognition
                # In a real implementation, this would use a trained model
                
                # Energy-based features
                energy = np.mean(audio_data ** 2)
                energy_std = np.std(audio_data ** 2)
                zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
                
                # Compute emotion scores
                emotion_scores = {
                    "neutral": 0.2,
                    "happy": 0.1,
                    "sad": 0.1,
                    "angry": 0.1,
                    "fearful": 0.1,
                    "disgusted": 0.1,
                    "surprised": 0.1
                }
                
                # Apply rules
                if energy > 0.01:
                    emotion_scores["angry"] += 0.3
                    emotion_scores["happy"] += 0.2
                    emotion_scores["surprised"] += 0.2
                    emotion_scores["neutral"] -= 0.2
                    emotion_scores["sad"] -= 0.2
                
                if energy < 0.001:
                    emotion_scores["sad"] += 0.3
                    emotion_scores["fearful"] += 0.2
                    emotion_scores["neutral"] += 0.1
                    emotion_scores["happy"] -= 0.2
                    emotion_scores["angry"] -= 0.2
                
                if energy_std > 0.005:
                    emotion_scores["surprised"] += 0.3
                    emotion_scores["fearful"] += 0.2
                    emotion_scores["neutral"] -= 0.2
                
                if zero_crossings > 0.1:
                    emotion_scores["angry"] += 0.2
                    emotion_scores["disgusted"] += 0.2
                    emotion_scores["sad"] -= 0.1
                
                # Normalize scores
                total = sum(emotion_scores.values())
                emotion_scores = {k: v / total for k, v in emotion_scores.items()}
                
                # Get top emotion
                top_emotion = max(emotion_scores.items(), key=lambda x: x[1])
                
                return {
                    "emotion": top_emotion[0],
                    "score": top_emotion[1],
                    "all_scores": emotion_scores
                }
            
            self.audio_emotion_model = recognize_audio_emotion
            logger.info("Audio emotion recognition model initialized")
        
        except ImportError:
            logger.warning("Librosa not available, using simplified audio emotion recognition")
            
            # Define simplified audio emotion recognition function
            def simple_audio_emotion_recognition(audio_data, sample_rate):
                # Convert to float32 if needed
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                
                # Compute simple features
                energy = np.mean(audio_data ** 2)
                zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
                
                # Compute emotion scores
                emotion_scores = {
                    "neutral": 0.5,
                    "happy": 0.1,
                    "sad": 0.1,
                    "angry": 0.1,
                    "fearful": 0.1,
                    "disgusted": 0.05,
                    "surprised": 0.05
                }
                
                # Apply simple rules
                if energy > 0.01:
                    emotion_scores["angry"] += 0.2
                    emotion_scores["happy"] += 0.1
                    emotion_scores["neutral"] -= 0.1
                
                if energy < 0.001:
                    emotion_scores["sad"] += 0.2
                    emotion_scores["neutral"] += 0.1
                    emotion_scores["happy"] -= 0.1
                
                if zero_crossings > 0.1:
                    emotion_scores["angry"] += 0.1
                    emotion_scores["surprised"] += 0.1
                    emotion_scores["neutral"] -= 0.1
                
                # Normalize scores
                total = sum(emotion_scores.values())
                emotion_scores = {k: v / total for k, v in emotion_scores.items()}
                
                # Get top emotion
                top_emotion = max(emotion_scores.items(), key=lambda x: x[1])
                
                return {
                    "emotion": top_emotion[0],
                    "score": top_emotion[1],
                    "all_scores": emotion_scores
                }
            
            self.audio_emotion_model = simple_audio_emotion_recognition
            logger.info("Simplified audio emotion recognition initialized")
    
    async def _initialize_text_emotion_model(self):
        """Initialize text-based emotion recognition model"""
        try:
            # Define text emotion recognition function
            def recognize_text_emotion(text, language="en"):
                # Define emotion keywords
                emotion_keywords = {
                    "en": {
                        "happy": ["happy", "joy", "delighted", "pleased", "glad", "cheerful", "content", "satisfied", "excited", "thrilled"],
                        "sad": ["sad", "unhappy", "depressed", "down", "miserable", "heartbroken", "gloomy", "disappointed", "upset", "distressed"],
                        "angry": ["angry", "mad", "furious", "outraged", "annoyed", "irritated", "frustrated", "enraged", "hostile", "bitter"],
                        "fearful": ["afraid", "scared", "frightened", "terrified", "anxious", "worried", "nervous", "panicked", "alarmed", "uneasy"],
                        "disgusted": ["disgusted", "revolted", "repulsed", "sickened", "appalled", "horrified", "offended", "displeased", "loathing", "hateful"],
                        "surprised": ["surprised", "amazed", "astonished", "shocked", "stunned", "startled", "speechless", "bewildered", "dumbfounded", "awestruck"],
                        "neutral": ["ok", "fine", "neutral", "indifferent", "impartial", "unbiased", "objective", "detached", "dispassionate", "calm"]
                    },
                    "nl": {
                        "happy": ["blij", "gelukkig", "verheugd", "tevreden", "vrolijk", "opgewekt", "content", "voldaan", "opgetogen", "enthousiast"],
                        "sad": ["verdrietig", "bedroefd", "treurig", "somber", "ongelukkig", "neerslachtig", "droevig", "teleurgesteld", "ontdaan", "gedeprimeerd"],
                        "angry": ["boos", "kwaad", "woedend", "razend", "geïrriteerd", "geërgerd", "gefrustreerd", "woest", "vijandig", "verbitterd"],
                        "fearful": ["bang", "angstig", "bevreesd", "doodsbang", "bezorgd", "ongerust", "nerveus", "paniekerig", "gealarmeerd", "ongemakkelijk"],
                        "disgusted": ["walgend", "misselijk", "afkeer", "weerzin", "ontzet", "geschokt", "beledigd", "ontevreden", "afschuw", "hatelijk"],
                        "surprised": ["verrast", "verbaasd", "versteld", "geschokt", "verbluft", "geschrokken", "sprakeloos", "verwonderd", "stomverbaasd", "ontzag"],
                        "neutral": ["ok", "prima", "neutraal", "onverschillig", "onpartijdig", "objectief", "afstandelijk", "kalm", "rustig", "beheerst"]
                    }
                }
                
                # Detect language if not provided
                if language not in emotion_keywords:
                    if any(word in text.lower() for word in ["de", "het", "een", "ik", "jij", "wij", "zij", "en", "of", "maar"]):
                        language = "nl"
                    else:
                        language = "en"
                
                # Initialize emotion scores
                emotion_scores = {emotion: 0.0 for emotion in emotion_keywords[language].keys()}
                
                # Count emotion keywords
                text_lower = text.lower()
                for emotion, keywords in emotion_keywords[language].items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            emotion_scores[emotion] += 1.0
                
                # If no emotions detected, set neutral as default
                if sum(emotion_scores.values()) == 0:
                    emotion_scores["neutral"] = 1.0
                
                # Normalize scores
                total = sum(emotion_scores.values())
                emotion_scores = {k: v / total for k, v in emotion_scores.items()}
                
                # Get top emotion
                top_emotion = max(emotion_scores.items(), key=lambda x: x[1])
                
                return {
                    "emotion": top_emotion[0],
                    "score": top_emotion[1],
                    "all_scores": emotion_scores
                }
            
            self.text_emotion_model = recognize_text_emotion
            logger.info("Text emotion recognition model initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize text emotion recognition model: {e}")
            self.text_emotion_model = lambda text, language="en": {"emotion": "neutral", "score": 1.0, "all_scores": {"neutral": 1.0}}
    
    async def _initialize_multimodal_emotion_model(self):
        """Initialize multimodal emotion recognition model"""
        try:
            # Define multimodal emotion recognition function
            def recognize_multimodal_emotion(audio_result, text_result):
                # Get audio and text emotion scores
                audio_scores = audio_result.get("all_scores", {})
                text_scores = text_result.get("all_scores", {})
                
                # Initialize combined scores
                combined_scores = {}
                
                # Combine scores with weights
                audio_weight = 0.4
                text_weight = 0.6
                
                for emotion in self.emotion_categories:
                    audio_score = audio_scores.get(emotion, 0.0)
                    text_score = text_scores.get(emotion, 0.0)
                    
                    combined_scores[emotion] = (audio_score * audio_weight) + (text_score * text_weight)
                
                # Normalize scores
                total = sum(combined_scores.values())
                if total > 0:
                    combined_scores = {k: v / total for k, v in combined_scores.items()}
                else:
                    combined_scores = {emotion: 1.0 / len(self.emotion_categories) for emotion in self.emotion_categories}
                
                # Get top emotion
                top_emotion = max(combined_scores.items(), key=lambda x: x[1])
                
                return {
                    "emotion": top_emotion[0],
                    "score": top_emotion[1],
                    "all_scores": combined_scores,
                    "audio_emotion": audio_result.get("emotion"),
                    "text_emotion": text_result.get("emotion")
                }
            
            self.multimodal_emotion_model = recognize_multimodal_emotion
            logger.info("Multimodal emotion recognition model initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize multimodal emotion recognition model: {e}")
            self.multimodal_emotion_model = lambda audio_result, text_result: {"emotion": "neutral", "score": 1.0, "all_scores": {"neutral": 1.0}}
    
    async def recognize_emotion(self, audio_chunk: AudioChunk, transcription: TranscriptionResult) -> Dict[str, Any]:
        """
        Recognize emotion from audio and text
        
        Args:
            audio_chunk: Audio chunk
            transcription: Transcription result
            
        Returns:
            Dict of emotion recognition results
        """
        if not self.is_initialized or not self.enabled:
            return {"emotion": "neutral", "score": 1.0}
        
        try:
            # Get session ID
            session_id = audio_chunk.session_id
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Get language
            language = transcription.language or "nl"
            
            # Initialize results
            audio_result = {"emotion": "neutral", "score": 1.0, "all_scores": {"neutral": 1.0}}
            text_result = {"emotion": "neutral", "score": 1.0, "all_scores": {"neutral": 1.0}}
            multimodal_result = {"emotion": "neutral", "score": 1.0, "all_scores": {"neutral": 1.0}}
            
            # Recognize audio emotion
            if self.audio_emotion_enabled and self.audio_emotion_model:
                # Convert audio to numpy array
                audio_data = audio_chunk.to_numpy()
                
                # Recognize emotion
                audio_result = self.audio_emotion_model(audio_data, audio_chunk.sample_rate)
            
            # Recognize text emotion
            if self.text_emotion_enabled and self.text_emotion_model and transcription.text:
                # Recognize emotion
                text_result = self.text_emotion_model(transcription.text, language)
            
            # Recognize multimodal emotion
            if self.multimodal_emotion_enabled and self.multimodal_emotion_model:
                # Recognize emotion
                multimodal_result = self.multimodal_emotion_model(audio_result, text_result)
            
            # Update session state
            session_state["audio_emotion"] = audio_result
            session_state["text_emotion"] = text_result
            session_state["multimodal_emotion"] = multimodal_result
            session_state["emotion_history"].append(multimodal_result)
            
            # Keep only last 10 emotions
            if len(session_state["emotion_history"]) > 10:
                session_state["emotion_history"] = session_state["emotion_history"][-10:]
            
            # Update last activity
            session_state["last_activity"] = time.time()
            
            return multimodal_result
        
        except Exception as e:
            logger.error(f"Error recognizing emotion: {e}")
            return {"emotion": "neutral", "score": 1.0}
    
    def _create_session_state(self, session_id: str):
        """
        Create session state
        
        Args:
            session_id: Session ID
        """
        self.session_states[session_id] = {
            "audio_emotion": None,
            "text_emotion": None,
            "multimodal_emotion": None,
            "emotion_history": [],
            "last_activity": time.time()
        }
    
    def get_session_emotion(self, session_id: str) -> Dict[str, Any]:
        """
        Get emotion for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict of emotion recognition results
        """
        if not self.is_initialized or not self.enabled:
            return {"emotion": "neutral", "score": 1.0}
        
        try:
            # Check if session exists
            if session_id not in self.session_states:
                return {"emotion": "neutral", "score": 1.0}
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Get multimodal emotion
            multimodal_emotion = session_state.get("multimodal_emotion")
            
            if multimodal_emotion:
                return multimodal_emotion
            
            return {"emotion": "neutral", "score": 1.0}
        
        except Exception as e:
            logger.error(f"Error getting session emotion: {e}")
            return {"emotion": "neutral", "score": 1.0}
    
    def get_emotion_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get emotion history for session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of emotion recognition results
        """
        if not self.is_initialized or not self.enabled:
            return []
        
        try:
            # Check if session exists
            if session_id not in self.session_states:
                return []
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Get emotion history
            emotion_history = session_state.get("emotion_history", [])
            
            return emotion_history
        
        except Exception as e:
            logger.error(f"Error getting emotion history: {e}")
            return []
    
    def reset_session(self, session_id: str):
        """
        Reset session state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
    
    def close(self):
        """Close emotion recognition manager and free resources"""
        self.session_states.clear()
        self.is_initialized = False
        logger.info("Emotion recognition manager closed")


# Global emotion recognition manager instance
emotion_recognition = EmotionRecognition()