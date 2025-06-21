"""
Voice Verification Module

Provides voice verification capabilities:
- Speaker recognition
- Voice biometrics
- Anti-spoofing
- Voice profile management
"""
import logging
import time
import os
import json
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import defaultdict
import pickle
import hashlib

from src.config import settings
from src.models import AudioChunk, TranscriptionResult

logger = logging.getLogger(__name__)


class VoiceVerification:
    """
    Voice verification manager for speaker recognition
    
    Features:
    - Speaker recognition
    - Voice biometrics
    - Anti-spoofing
    - Voice profile management
    """
    
    def __init__(self):
        """Initialize voice verification manager"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.enabled = self.config.voice_verification_enabled
        self.verification_threshold = self.config.voice_verification_threshold
        self.min_audio_duration = self.config.voice_verification_min_duration
        self.anti_spoofing_enabled = self.config.anti_spoofing_enabled
        
        # Voice profiles
        self.profiles_dir = os.path.join(settings.MODELS_DIR, "voice_profiles")
        self.voice_profiles = {}
        self.session_profiles = {}
        
        # Session state
        self.session_states = {}
        
        # Feature extraction
        self.feature_extractor = None
        
        logger.info(f"Voice verification manager initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> bool:
        """
        Initialize voice verification manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create profiles directory
            os.makedirs(self.profiles_dir, exist_ok=True)
            
            # Initialize feature extractor
            await self._initialize_feature_extractor()
            
            # Load voice profiles
            await self._load_voice_profiles()
            
            self.is_initialized = True
            logger.info("Voice verification manager initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize voice verification manager: {e}")
            return False
    
    async def _initialize_feature_extractor(self):
        """Initialize feature extractor"""
        try:
            # Try to import librosa for audio feature extraction
            import librosa
            
            # Define feature extraction function
            def extract_features(audio_data, sample_rate):
                # Convert to float32 if needed
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                
                # Extract MFCCs (Mel-frequency cepstral coefficients)
                mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=20)
                
                # Extract spectral contrast
                contrast = librosa.feature.spectral_contrast(y=audio_data, sr=sample_rate)
                
                # Extract chroma features
                chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
                
                # Compute statistics
                mfccs_mean = np.mean(mfccs, axis=1)
                mfccs_std = np.std(mfccs, axis=1)
                contrast_mean = np.mean(contrast, axis=1)
                chroma_mean = np.mean(chroma, axis=1)
                
                # Combine features
                features = np.concatenate([mfccs_mean, mfccs_std, contrast_mean, chroma_mean])
                
                return features
            
            self.feature_extractor = extract_features
            logger.info("Feature extractor initialized with librosa")
        
        except ImportError:
            logger.warning("Librosa not available, using simplified feature extraction")
            
            # Define simplified feature extraction function
            def simple_extract_features(audio_data, sample_rate):
                # Convert to float32 if needed
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                
                # Compute simple features
                energy = np.mean(audio_data ** 2)
                zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
                
                # Compute simple spectrum
                from scipy import signal
                frequencies, spectrum = signal.welch(audio_data, sample_rate, nperseg=1024)
                
                # Extract spectral features
                spectral_centroid = np.sum(frequencies * spectrum) / np.sum(spectrum) if np.sum(spectrum) > 0 else 0
                spectral_bandwidth = np.sqrt(np.sum(((frequencies - spectral_centroid) ** 2) * spectrum) / np.sum(spectrum)) if np.sum(spectrum) > 0 else 0
                
                # Compute statistics on chunks
                chunk_size = 1024
                chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size) if i+chunk_size <= len(audio_data)]
                
                if chunks:
                    chunk_energies = np.array([np.mean(chunk ** 2) for chunk in chunks])
                    energy_std = np.std(chunk_energies)
                    energy_range = np.max(chunk_energies) - np.min(chunk_energies)
                else:
                    energy_std = 0
                    energy_range = 0
                
                # Combine features
                features = np.array([
                    energy, zero_crossings, spectral_centroid, spectral_bandwidth,
                    energy_std, energy_range
                ])
                
                return features
            
            self.feature_extractor = simple_extract_features
            logger.info("Feature extractor initialized with simplified method")
    
    async def _load_voice_profiles(self):
        """Load voice profiles from storage"""
        try:
            # Load voice profiles
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith(".json"):
                    user_id = filename[:-5]  # Remove ".json" suffix
                    
                    profile_path = os.path.join(self.profiles_dir, filename)
                    with open(profile_path, 'r') as f:
                        profile_info = json.load(f)
                    
                    # Load voice features
                    features_path = os.path.join(self.profiles_dir, f"{user_id}.pkl")
                    if os.path.exists(features_path):
                        with open(features_path, 'rb') as f:
                            voice_features = pickle.load(f)
                    else:
                        voice_features = None
                    
                    # Create profile
                    profile = {
                        "user_id": user_id,
                        "name": profile_info.get("name", user_id),
                        "created_at": profile_info.get("created_at"),
                        "updated_at": profile_info.get("updated_at"),
                        "voice_features": voice_features,
                        "verification_count": profile_info.get("verification_count", 0),
                        "verification_success": profile_info.get("verification_success", 0),
                        "last_verification": profile_info.get("last_verification")
                    }
                    
                    self.voice_profiles[user_id] = profile
            
            logger.info(f"Loaded {len(self.voice_profiles)} voice profiles")
        
        except Exception as e:
            logger.error(f"Failed to load voice profiles: {e}")
            self.voice_profiles = {}
    
    async def verify_voice(self, audio_chunk: AudioChunk, user_id: str) -> Tuple[bool, float]:
        """
        Verify if audio matches user's voice profile
        
        Args:
            audio_chunk: Audio chunk to verify
            user_id: User ID to verify against
            
        Returns:
            Tuple of (is_verified, confidence)
        """
        if not self.is_initialized or not self.enabled:
            return True, 1.0  # Default to verified if disabled
        
        try:
            # Check if user has a voice profile
            if user_id not in self.voice_profiles:
                logger.warning(f"No voice profile for user {user_id}")
                return False, 0.0
            
            # Get user profile
            profile = self.voice_profiles[user_id]
            
            # Check if profile has voice features
            if not profile.get("voice_features") or len(profile["voice_features"]) == 0:
                logger.warning(f"No voice features for user {user_id}")
                return False, 0.0
            
            # Check audio duration
            if audio_chunk.duration and audio_chunk.duration < self.min_audio_duration:
                logger.warning(f"Audio too short for verification: {audio_chunk.duration}s < {self.min_audio_duration}s")
                return False, 0.0
            
            # Convert audio to numpy array
            audio_data = audio_chunk.to_numpy()
            
            # Check for spoofing if enabled
            if self.anti_spoofing_enabled:
                is_real, spoofing_confidence = self._check_anti_spoofing(audio_data, audio_chunk.sample_rate)
                
                if not is_real:
                    logger.warning(f"Possible spoofing detected for user {user_id} (confidence: {spoofing_confidence:.2f})")
                    return False, 0.0
            
            # Extract features
            features = self.feature_extractor(audio_data, audio_chunk.sample_rate)
            
            # Compare with profile features
            similarity, confidence = self._compare_features(features, profile["voice_features"])
            
            # Update verification stats
            profile["verification_count"] = profile.get("verification_count", 0) + 1
            if similarity:
                profile["verification_success"] = profile.get("verification_success", 0) + 1
            profile["last_verification"] = time.time()
            
            # Save updated profile
            self._save_profile(user_id, profile)
            
            # Return result
            return similarity, confidence
        
        except Exception as e:
            logger.error(f"Error verifying voice: {e}")
            return False, 0.0
    
    def _compare_features(self, features: np.ndarray, profile_features: np.ndarray) -> Tuple[bool, float]:
        """
        Compare voice features with profile features
        
        Args:
            features: Extracted voice features
            profile_features: Profile voice features
            
        Returns:
            Tuple of (is_similar, confidence)
        """
        try:
            # If profile features is a list of feature vectors, compare with each
            if isinstance(profile_features, list):
                similarities = []
                
                for prof_feat in profile_features:
                    # Compute cosine similarity
                    similarity = np.dot(features, prof_feat) / (np.linalg.norm(features) * np.linalg.norm(prof_feat))
                    similarities.append(similarity)
                
                # Use maximum similarity
                max_similarity = max(similarities)
                
                # Check if similarity is above threshold
                is_similar = max_similarity > self.verification_threshold
                
                return is_similar, max_similarity
            
            else:
                # Compute cosine similarity
                similarity = np.dot(features, profile_features) / (np.linalg.norm(features) * np.linalg.norm(profile_features))
                
                # Check if similarity is above threshold
                is_similar = similarity > self.verification_threshold
                
                return is_similar, similarity
        
        except Exception as e:
            logger.error(f"Error comparing features: {e}")
            return False, 0.0
    
    def _check_anti_spoofing(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[bool, float]:
        """
        Check for voice spoofing attempts
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            
        Returns:
            Tuple of (is_real, confidence)
        """
        try:
            # Simple spoofing detection based on audio statistics
            # In a real implementation, this would use a more sophisticated model
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Check for unusual patterns
            energy = np.mean(audio_data ** 2)
            zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
            
            # Compute energy variance in chunks
            chunk_size = 1024
            chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size) if i+chunk_size <= len(audio_data)]
            
            if chunks:
                chunk_energies = np.array([np.mean(chunk ** 2) for chunk in chunks])
                energy_std = np.std(chunk_energies)
                energy_range = np.max(chunk_energies) - np.min(chunk_energies)
            else:
                energy_std = 0
                energy_range = 0
            
            # Check for unusual values
            is_real = True
            confidence = 0.8  # Default confidence
            
            # Check for very low energy
            if energy < 0.0001:
                is_real = False
                confidence = 0.7
            
            # Check for very high energy
            if energy > 0.1:
                is_real = False
                confidence = 0.7
            
            # Check for very low energy variation
            if energy_std < 0.00001:
                is_real = False
                confidence = 0.8
            
            # Check for very high zero crossing rate
            if zero_crossings > 0.5:
                is_real = False
                confidence = 0.9
            
            return is_real, confidence
        
        except Exception as e:
            logger.error(f"Error in anti-spoofing check: {e}")
            return True, 0.5  # Default to real if error
    
    async def enroll_user(self, audio_chunks: List[AudioChunk], user_id: str, name: str = None) -> bool:
        """
        Enroll user with voice samples
        
        Args:
            audio_chunks: List of audio chunks for enrollment
            user_id: User ID
            name: User name (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized or not self.enabled:
            return False
        
        try:
            # Check if we have enough audio
            total_duration = sum(chunk.duration or 0 for chunk in audio_chunks)
            
            if total_duration < self.min_audio_duration * 3:
                logger.warning(f"Not enough audio for enrollment: {total_duration}s < {self.min_audio_duration * 3}s")
                return False
            
            # Extract features from each audio chunk
            features_list = []
            
            for chunk in audio_chunks:
                # Convert audio to numpy array
                audio_data = chunk.to_numpy()
                
                # Extract features
                features = self.feature_extractor(audio_data, chunk.sample_rate)
                features_list.append(features)
            
            # Create or update profile
            profile = self.voice_profiles.get(user_id, {})
            profile.update({
                "user_id": user_id,
                "name": name or user_id,
                "created_at": profile.get("created_at", time.time()),
                "updated_at": time.time(),
                "voice_features": features_list,
                "verification_count": profile.get("verification_count", 0),
                "verification_success": profile.get("verification_success", 0),
                "last_verification": profile.get("last_verification")
            })
            
            # Save profile
            self.voice_profiles[user_id] = profile
            self._save_profile(user_id, profile)
            
            logger.info(f"Enrolled user {user_id} with {len(features_list)} voice samples")
            return True
        
        except Exception as e:
            logger.error(f"Error enrolling user: {e}")
            return False
    
    def _save_profile(self, user_id: str, profile: Dict[str, Any]):
        """
        Save voice profile to storage
        
        Args:
            user_id: User ID
            profile: Voice profile
        """
        try:
            # Create profile info (without features)
            profile_info = {
                "user_id": profile["user_id"],
                "name": profile["name"],
                "created_at": profile["created_at"],
                "updated_at": profile["updated_at"],
                "verification_count": profile["verification_count"],
                "verification_success": profile["verification_success"],
                "last_verification": profile["last_verification"]
            }
            
            # Save profile info
            profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")
            with open(profile_path, 'w') as f:
                json.dump(profile_info, f, indent=2)
            
            # Save voice features
            if "voice_features" in profile and profile["voice_features"]:
                features_path = os.path.join(self.profiles_dir, f"{user_id}.pkl")
                with open(features_path, 'wb') as f:
                    pickle.dump(profile["voice_features"], f)
        
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete voice profile
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if profile exists
            if user_id not in self.voice_profiles:
                logger.warning(f"No voice profile for user {user_id}")
                return False
            
            # Remove from memory
            del self.voice_profiles[user_id]
            
            # Remove files
            profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")
            features_path = os.path.join(self.profiles_dir, f"{user_id}.pkl")
            
            if os.path.exists(profile_path):
                os.remove(profile_path)
            
            if os.path.exists(features_path):
                os.remove(features_path)
            
            logger.info(f"Deleted voice profile for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return False
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get voice profile
        
        Args:
            user_id: User ID
            
        Returns:
            Voice profile or None
        """
        # Check if profile exists
        if user_id not in self.voice_profiles:
            return None
        
        # Get profile
        profile = self.voice_profiles[user_id]
        
        # Return profile info (without features)
        return {
            "user_id": profile["user_id"],
            "name": profile.get("name", user_id),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at"),
            "verification_count": profile.get("verification_count", 0),
            "verification_success": profile.get("verification_success", 0),
            "last_verification": profile.get("last_verification"),
            "has_voice_features": bool(profile.get("voice_features"))
        }
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all voice profiles
        
        Returns:
            Dict of user IDs and profile info
        """
        # Return all profiles (without features)
        return {
            user_id: {
                "user_id": profile["user_id"],
                "name": profile.get("name", user_id),
                "created_at": profile.get("created_at"),
                "updated_at": profile.get("updated_at"),
                "verification_count": profile.get("verification_count", 0),
                "verification_success": profile.get("verification_success", 0),
                "last_verification": profile.get("last_verification"),
                "has_voice_features": bool(profile.get("voice_features"))
            }
            for user_id, profile in self.voice_profiles.items()
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
        """Close voice verification manager and free resources"""
        self.session_states.clear()
        self.is_initialized = False
        logger.info("Voice verification manager closed")


# Global voice verification manager instance
voice_verification = VoiceVerification()