"""
Audio Preprocessing Module

Provides audio preprocessing capabilities including:
- Noise reduction
- Volume normalization
- Silence removal
- Audio filtering
- Signal enhancement
"""
import numpy as np
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
import scipy.signal as signal
from scipy.ndimage import median_filter

from src.config import settings
from src.models import AudioChunk

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """
    Audio preprocessing for improved speech recognition
    
    Features:
    - Noise reduction using spectral subtraction
    - Volume normalization
    - Bandpass filtering for speech frequencies
    - Silence detection and removal
    - Signal enhancement
    """
    
    def __init__(self):
        """Initialize audio preprocessor"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.sample_rate = self.config.audio_sample_rate
        self.noise_reduction_enabled = self.config.noise_reduction_enabled
        self.volume_normalization_enabled = self.config.volume_normalization_enabled
        self.bandpass_filter_enabled = self.config.bandpass_filter_enabled
        
        # Noise reduction parameters
        self.noise_reduction_strength = self.config.noise_reduction_strength
        self.noise_floor = np.array([])
        self.noise_floor_updated = False
        self.noise_estimate_frames = 5
        self.noise_frames_collected = 0
        
        # Volume normalization parameters
        self.target_rms = self.config.target_rms
        
        # Bandpass filter parameters
        self.speech_low_freq = 80  # Hz
        self.speech_high_freq = 7000  # Hz
        
        # Session state
        self.session_states = {}
        
        logger.info("Audio preprocessor initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize audio preprocessor
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Design bandpass filter if enabled
            if self.bandpass_filter_enabled:
                self._design_bandpass_filter()
            
            self.is_initialized = True
            logger.info("Audio preprocessor initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize audio preprocessor: {e}")
            return False
    
    def _design_bandpass_filter(self):
        """Design bandpass filter for speech frequencies"""
        # Normalize frequencies to Nyquist frequency
        nyquist = self.sample_rate / 2
        low = self.speech_low_freq / nyquist
        high = self.speech_high_freq / nyquist
        
        # Design filter
        self.bandpass_b, self.bandpass_a = signal.butter(4, [low, high], btype='band')
        logger.debug(f"Bandpass filter designed: {self.speech_low_freq}-{self.speech_high_freq} Hz")
    
    async def process_audio(self, audio_chunk: AudioChunk) -> AudioChunk:
        """
        Process audio chunk with noise reduction and other enhancements
        
        Args:
            audio_chunk: Audio chunk to process
            
        Returns:
            Processed audio chunk
        """
        if not self.is_initialized:
            logger.warning("Audio preprocessor not initialized, returning original audio")
            return audio_chunk
        
        try:
            # Get session ID
            session_id = audio_chunk.session_id
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Convert audio to numpy array
            audio_data = audio_chunk.to_numpy()
            
            # Skip processing if audio is too short
            if len(audio_data) < 160:  # 10ms at 16kHz
                return audio_chunk
            
            # Apply preprocessing steps
            processed_audio = audio_data.copy()
            
            # Update noise profile if needed
            if self.noise_reduction_enabled and not session_state["noise_profile_updated"]:
                # Use the first few frames to estimate noise
                if session_state["frame_count"] < self.noise_estimate_frames:
                    self._update_noise_profile(processed_audio, session_id)
                    session_state["frame_count"] += 1
                    
                    # Mark as updated after collecting enough frames
                    if session_state["frame_count"] >= self.noise_estimate_frames:
                        session_state["noise_profile_updated"] = True
                        logger.debug(f"Noise profile updated for session {session_id}")
            
            # Apply bandpass filter if enabled
            if self.bandpass_filter_enabled:
                processed_audio = self._apply_bandpass_filter(processed_audio)
            
            # Apply noise reduction if enabled and profile is ready
            if self.noise_reduction_enabled and session_state["noise_profile_updated"]:
                processed_audio = self._apply_noise_reduction(processed_audio, session_id)
            
            # Apply volume normalization if enabled
            if self.volume_normalization_enabled:
                processed_audio = self._normalize_volume(processed_audio)
            
            # Create new audio chunk with processed audio
            processed_chunk = AudioChunk(
                session_id=audio_chunk.session_id,
                data=processed_audio.tobytes(),
                sample_rate=audio_chunk.sample_rate,
                channels=audio_chunk.channels,
                timestamp=audio_chunk.timestamp,
                duration=audio_chunk.duration
            )
            
            return processed_chunk
        
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return audio_chunk
    
    def _create_session_state(self, session_id: str):
        """
        Create session state
        
        Args:
            session_id: Session ID
        """
        self.session_states[session_id] = {
            "noise_profile": None,
            "noise_profile_updated": False,
            "frame_count": 0,
            "last_activity": time.time()
        }
    
    def _update_noise_profile(self, audio_data: np.ndarray, session_id: str):
        """
        Update noise profile for session
        
        Args:
            audio_data: Audio data
            session_id: Session ID
        """
        session_state = self.session_states[session_id]
        
        # Compute magnitude spectrum
        n_fft = min(2048, len(audio_data))
        noise_spectrum = np.abs(np.fft.rfft(audio_data, n=n_fft))
        
        # Update noise profile (running average)
        if session_state["noise_profile"] is None:
            session_state["noise_profile"] = noise_spectrum
        else:
            # Weighted average (more weight to lower values as they're likely noise)
            alpha = 0.3
            session_state["noise_profile"] = alpha * np.minimum(
                session_state["noise_profile"], noise_spectrum
            ) + (1 - alpha) * session_state["noise_profile"]
    
    def _apply_noise_reduction(self, audio_data: np.ndarray, session_id: str) -> np.ndarray:
        """
        Apply spectral subtraction noise reduction
        
        Args:
            audio_data: Audio data
            session_id: Session ID
            
        Returns:
            Noise-reduced audio data
        """
        session_state = self.session_states[session_id]
        noise_profile = session_state["noise_profile"]
        
        if noise_profile is None or len(noise_profile) == 0:
            return audio_data
        
        # Compute magnitude spectrum
        n_fft = min(2048, len(audio_data))
        
        # Get complex spectrum
        spectrum = np.fft.rfft(audio_data, n=n_fft)
        mag_spectrum = np.abs(spectrum)
        phase_spectrum = np.angle(spectrum)
        
        # Ensure noise profile matches spectrum size
        if len(noise_profile) != len(mag_spectrum):
            noise_profile = np.resize(noise_profile, len(mag_spectrum))
        
        # Apply spectral subtraction with flooring
        strength = self.noise_reduction_strength
        mag_spectrum = np.maximum(
            mag_spectrum - strength * noise_profile,
            0.01 * mag_spectrum  # Floor to avoid complete silence
        )
        
        # Reconstruct signal
        enhanced_spectrum = mag_spectrum * np.exp(1j * phase_spectrum)
        enhanced_audio = np.fft.irfft(enhanced_spectrum, len(audio_data))
        
        # Ensure output is same length as input and convert to int16
        enhanced_audio = enhanced_audio[:len(audio_data)]
        
        return enhanced_audio.astype(np.int16)
    
    def _apply_bandpass_filter(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter to focus on speech frequencies
        
        Args:
            audio_data: Audio data
            
        Returns:
            Filtered audio data
        """
        # Apply filter
        filtered_audio = signal.filtfilt(self.bandpass_b, self.bandpass_a, audio_data)
        
        # Convert back to int16
        return filtered_audio.astype(np.int16)
    
    def _normalize_volume(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio volume to target RMS
        
        Args:
            audio_data: Audio data
            
        Returns:
            Volume-normalized audio data
        """
        # Calculate current RMS
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        
        # Skip if audio is silent
        if rms < 1.0:
            return audio_data
        
        # Calculate gain
        gain = self.target_rms / (rms + 1e-6)
        
        # Apply gain with clipping protection
        normalized_audio = audio_data.astype(np.float32) * gain
        
        # Clip to int16 range
        normalized_audio = np.clip(normalized_audio, -32768, 32767)
        
        # Convert back to int16
        return normalized_audio.astype(np.int16)
    
    def reset_session(self, session_id: str):
        """
        Reset session state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
    
    def close(self):
        """Close audio preprocessor and free resources"""
        self.session_states.clear()
        self.is_initialized = False
        logger.info("Audio preprocessor closed")


# Global audio preprocessor instance
audio_preprocessor = AudioPreprocessor()