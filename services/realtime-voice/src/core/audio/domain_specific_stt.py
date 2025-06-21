"""
Domain-Specific Speech Recognition Module

Provides domain-specific speech recognition capabilities:
- Domain detection
- Domain-specific vocabulary
- Custom language models
- Terminology adaptation
"""
import logging
import time
import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import defaultdict

from src.config import settings
from src.models import TranscriptionResult

logger = logging.getLogger(__name__)


class DomainSpecificSTT:
    """
    Domain-specific speech recognition manager
    
    Features:
    - Domain detection
    - Domain-specific vocabulary
    - Terminology adaptation
    - Post-processing rules
    """
    
    def __init__(self):
        """Initialize domain-specific STT manager"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.enabled = self.config.domain_specific_stt_enabled
        self.confidence_threshold = self.config.domain_specific_stt_confidence
        
        # Domain profiles
        self.domains_dir = os.path.join(settings.MODELS_DIR, "domains")
        self.domains = {}
        self.session_domains = {}
        
        # Domain-specific vocabulary
        self.domain_vocabulary = {}
        
        # Session state
        self.session_states = {}
        
        logger.info(f"Domain-specific STT manager initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> bool:
        """
        Initialize domain-specific STT manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create domains directory
            os.makedirs(self.domains_dir, exist_ok=True)
            
            # Load domain profiles
            await self._load_domain_profiles()
            
            self.is_initialized = True
            logger.info("Domain-specific STT manager initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize domain-specific STT manager: {e}")
            return False
    
    async def _load_domain_profiles(self):
        """Load domain profiles from storage"""
        try:
            # Load global domain profiles
            domains_path = os.path.join(self.domains_dir, "domains.json")
            
            if os.path.exists(domains_path):
                with open(domains_path, 'r') as f:
                    self.domains = json.load(f)
                logger.info(f"Loaded {len(self.domains)} domain profiles")
            else:
                # Create default domain profiles
                self.domains = {
                    "general": {
                        "name": "General",
                        "description": "General domain with common vocabulary",
                        "keywords": [],
                        "vocabulary": {},
                        "patterns": {},
                        "corrections": {}
                    },
                    "medical": {
                        "name": "Medical",
                        "description": "Medical domain with healthcare terminology",
                        "keywords": [
                            "patient", "doctor", "hospital", "diagnosis", "treatment",
                            "medication", "prescription", "symptom", "disease", "healthcare"
                        ],
                        "vocabulary": {
                            "hypertension": ["high blood pressure", "hoge bloeddruk"],
                            "myocardial infarction": ["heart attack", "hartaanval"],
                            "diabetes mellitus": ["diabetes", "suikerziekte"],
                            "cerebrovascular accident": ["stroke", "beroerte"],
                            "analgesic": ["pain medication", "pijnstiller"]
                        },
                        "patterns": {
                            "dosage": r"\b\d+\s*(?:mg|ml|g|mcg|microgram)\b",
                            "blood pressure": r"\b\d{2,3}(?:/| over )\d{2,3}\b"
                        },
                        "corrections": {
                            "hart aanval": "hartaanval",
                            "hoge bloed druk": "hoge bloeddruk",
                            "suiker ziekte": "suikerziekte"
                        }
                    },
                    "legal": {
                        "name": "Legal",
                        "description": "Legal domain with juridical terminology",
                        "keywords": [
                            "court", "judge", "lawyer", "attorney", "plaintiff", "defendant",
                            "contract", "law", "legal", "justice", "rechtbank", "advocaat"
                        ],
                        "vocabulary": {
                            "plaintiff": ["claimant", "eiser"],
                            "defendant": ["respondent", "gedaagde"],
                            "jurisprudence": ["case law", "jurisprudentie"],
                            "litigation": ["lawsuit", "rechtszaak"],
                            "affidavit": ["sworn statement", "beëdigde verklaring"]
                        },
                        "patterns": {
                            "case number": r"\b[A-Z]{1,3}-\d{2,6}(?:/\d{2,4})?\b",
                            "article reference": r"\bartikel\s+\d+(?:\.\d+)*\b"
                        },
                        "corrections": {
                            "rechts zaak": "rechtszaak",
                            "wettelijke vertegenwoordiger": "wettelijk vertegenwoordiger"
                        }
                    },
                    "technical": {
                        "name": "Technical",
                        "description": "Technical domain with IT and engineering terminology",
                        "keywords": [
                            "computer", "software", "hardware", "network", "server",
                            "database", "programming", "algorithm", "interface", "system"
                        ],
                        "vocabulary": {
                            "algorithm": ["algorithme"],
                            "interface": ["gebruikersinterface", "koppelvlak"],
                            "database": ["databank", "gegevensbank"],
                            "encryption": ["encryptie", "versleuteling"],
                            "authentication": ["authenticatie", "identiteitsverificatie"]
                        },
                        "patterns": {
                            "ip address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
                            "version number": r"\bv\d+(?:\.\d+){1,3}\b"
                        },
                        "corrections": {
                            "data base": "database",
                            "gebruikers interface": "gebruikersinterface",
                            "hard ware": "hardware"
                        }
                    },
                    "financial": {
                        "name": "Financial",
                        "description": "Financial domain with banking and investment terminology",
                        "keywords": [
                            "bank", "investment", "finance", "money", "loan", "mortgage",
                            "interest", "credit", "debit", "transaction", "financieel"
                        ],
                        "vocabulary": {
                            "mortgage": ["home loan", "hypotheek"],
                            "interest rate": ["interest", "rentepercentage"],
                            "investment": ["belegging", "investering"],
                            "transaction": ["transactie"],
                            "dividend": ["dividend", "winstuitkering"]
                        },
                        "patterns": {
                            "money amount": r"\b€\s*\d+(?:[,.]\d+)*\b",
                            "percentage": r"\b\d+(?:[,.]\d+)*\s*%\b"
                        },
                        "corrections": {
                            "rente percentage": "rentepercentage",
                            "hypotheek lening": "hypotheeklening",
                            "bank rekening": "bankrekening"
                        }
                    }
                }
                
                # Save default profiles
                with open(domains_path, 'w') as f:
                    json.dump(self.domains, f, indent=2)
                
                logger.info("Created default domain profiles")
            
            # Load domain vocabulary
            for domain_id, domain in self.domains.items():
                vocabulary = domain.get("vocabulary", {})
                self.domain_vocabulary[domain_id] = vocabulary
            
            # Load session-specific domain profiles
            for filename in os.listdir(self.domains_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]  # Remove "session_" prefix and ".json" suffix
                    
                    with open(os.path.join(self.domains_dir, filename), 'r') as f:
                        profile = json.load(f)
                    
                    self.session_domains[session_id] = profile
                    logger.debug(f"Loaded domain profile for session {session_id}")
        
        except Exception as e:
            logger.error(f"Failed to load domain profiles: {e}")
            # Create empty profiles
            self.domains = {
                "general": {
                    "name": "General",
                    "description": "General domain with common vocabulary",
                    "keywords": [],
                    "vocabulary": {},
                    "patterns": {},
                    "corrections": {}
                }
            }
    
    async def process_transcription(self, transcription: TranscriptionResult) -> TranscriptionResult:
        """
        Process transcription with domain-specific adaptations
        
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
            
            # Detect domain if not already set
            if not session_state["domain"]:
                domain, confidence = await self.detect_domain(transcription)
                
                if confidence > self.confidence_threshold:
                    session_state["domain"] = domain
                    session_state["domain_confidence"] = confidence
                    logger.info(f"Detected domain for session {session_id}: {domain} ({confidence:.2f})")
            
            # Get domain profile
            domain = session_state["domain"] or "general"
            domain_profile = self._get_domain_profile(domain)
            
            # Apply domain-specific adaptations
            adapted_text = self._apply_domain_adaptations(
                transcription.text,
                domain_profile,
                language
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
            "domain": None,
            "domain_confidence": 0.0,
            "transcription_history": [],
            "last_activity": time.time()
        }
    
    def _get_domain_profile(self, domain_id: str) -> Dict[str, Any]:
        """
        Get domain profile
        
        Args:
            domain_id: Domain ID
            
        Returns:
            Domain profile
        """
        return self.domains.get(domain_id, self.domains.get("general", {}))
    
    def _apply_domain_adaptations(self, text: str, domain_profile: Dict[str, Any], language: str) -> str:
        """
        Apply domain-specific adaptations to text
        
        Args:
            text: Text to adapt
            domain_profile: Domain profile
            language: Language code
            
        Returns:
            Adapted text
        """
        if not text:
            return text
        
        # Apply corrections
        corrections = domain_profile.get("corrections", {})
        for wrong, correct in corrections.items():
            # Use word boundary regex to avoid partial word matches
            text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text, flags=re.IGNORECASE)
        
        # Apply vocabulary substitutions
        vocabulary = domain_profile.get("vocabulary", {})
        for term, alternatives in vocabulary.items():
            # Check if any alternative is in the text
            for alt in alternatives:
                if re.search(r'\b' + re.escape(alt) + r'\b', text, re.IGNORECASE):
                    # Replace with the canonical term
                    text = re.sub(r'\b' + re.escape(alt) + r'\b', term, text, flags=re.IGNORECASE)
                    break
        
        # Apply pattern-based corrections
        patterns = domain_profile.get("patterns", {})
        for pattern_name, pattern in patterns.items():
            # Find all matches
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            # Process each match
            for match in matches:
                matched_text = match.group(0)
                
                # Apply pattern-specific formatting
                if pattern_name == "dosage":
                    # Format dosage consistently
                    formatted = self._format_dosage(matched_text)
                    text = text.replace(matched_text, formatted)
                
                elif pattern_name == "money amount":
                    # Format money amount consistently
                    formatted = self._format_money(matched_text)
                    text = text.replace(matched_text, formatted)
                
                elif pattern_name == "percentage":
                    # Format percentage consistently
                    formatted = self._format_percentage(matched_text)
                    text = text.replace(matched_text, formatted)
        
        return text
    
    def _format_dosage(self, text: str) -> str:
        """Format dosage consistently"""
        # Remove spaces between number and unit
        text = re.sub(r'(\d+)\s+(mg|ml|g|mcg|microgram)', r'\1\2', text)
        return text
    
    def _format_money(self, text: str) -> str:
        """Format money amount consistently"""
        # Ensure € symbol is followed by a space
        text = re.sub(r'€\s*(\d)', r'€ \1', text)
        return text
    
    def _format_percentage(self, text: str) -> str:
        """Format percentage consistently"""
        # Ensure % symbol has no space before it
        text = re.sub(r'(\d+(?:[,.]\d+)*)\s+%', r'\1%', text)
        return text
    
    async def detect_domain(self, transcription: TranscriptionResult) -> Tuple[str, float]:
        """
        Detect domain from transcription
        
        Args:
            transcription: Transcription result
            
        Returns:
            Tuple of (domain_id, confidence)
        """
        if not self.is_initialized or not self.enabled:
            return "general", 0.0
        
        try:
            # Get session ID
            session_id = transcription.session_id
            
            # Get session state
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            session_state = self.session_states[session_id]
            
            # Add transcription to history
            session_state["transcription_history"].append(transcription.text)
            
            # Keep only last 10 transcriptions
            if len(session_state["transcription_history"]) > 10:
                session_state["transcription_history"] = session_state["transcription_history"][-10:]
            
            # Combine all transcriptions
            all_text = " ".join(session_state["transcription_history"])
            
            # Score domains
            domain_scores = self._score_domains(all_text)
            
            # Get domain with highest score
            if domain_scores:
                domain, score = max(domain_scores.items(), key=lambda x: x[1])
                return domain, score
            
            # If no domain detected, return default
            return "general", 0.0
        
        except Exception as e:
            logger.error(f"Error detecting domain: {e}")
            return "general", 0.0
    
    def _score_domains(self, text: str) -> Dict[str, float]:
        """
        Score text against known domains
        
        Args:
            text: Text to score
            
        Returns:
            Dict of domain IDs and scores
        """
        scores = {}
        text_lower = text.lower()
        
        # Score each domain
        for domain_id, domain in self.domains.items():
            if domain_id == "general":
                continue
            
            score = 0
            total_keywords = len(domain.get("keywords", []))
            
            if total_keywords == 0:
                continue
            
            # Check for domain keywords
            for keyword in domain.get("keywords", []):
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                    score += 1
            
            # Check for domain vocabulary
            for term, alternatives in domain.get("vocabulary", {}).items():
                if re.search(r'\b' + re.escape(term.lower()) + r'\b', text_lower):
                    score += 1
                else:
                    for alt in alternatives:
                        if re.search(r'\b' + re.escape(alt.lower()) + r'\b', text_lower):
                            score += 1
                            break
            
            # Check for domain patterns
            for pattern in domain.get("patterns", {}).values():
                if re.search(pattern, text_lower):
                    score += 1
            
            # Calculate normalized score (0-1)
            # We divide by 2*total_keywords to normalize, as we check both keywords and vocabulary
            normalized_score = score / (2 * total_keywords) if total_keywords > 0 else 0
            
            # Only include domains with some evidence
            if normalized_score > 0:
                scores[domain_id] = normalized_score
        
        return scores
    
    def set_session_domain(self, session_id: str, domain_id: str) -> bool:
        """
        Set domain for session
        
        Args:
            session_id: Session ID
            domain_id: Domain ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if domain is valid
            if domain_id not in self.domains:
                logger.error(f"Invalid domain: {domain_id}")
                return False
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Set domain
            session_state["domain"] = domain_id
            session_state["domain_confidence"] = 1.0
            
            # Save session domain profile
            profile = {
                "domain": domain_id,
                "confidence": 1.0
            }
            
            self.session_domains[session_id] = profile
            
            # Save to file
            profile_path = os.path.join(self.domains_dir, f"session_{session_id}.json")
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            logger.info(f"Set domain for session {session_id}: {domain_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error setting session domain: {e}")
            return False
    
    def get_session_domain(self, session_id: str) -> Tuple[str, float]:
        """
        Get domain for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Tuple of (domain_id, confidence)
        """
        # Check if session has a specific domain profile
        if session_id in self.session_domains:
            profile = self.session_domains[session_id]
            return profile.get("domain", "general"), profile.get("confidence", 0.0)
        
        # Check if session state has a domain
        if session_id in self.session_states:
            session_state = self.session_states[session_id]
            
            if session_state["domain"]:
                return session_state["domain"], session_state["domain_confidence"]
        
        # Otherwise, return default
        return "general", 0.0
    
    def get_supported_domains(self) -> Dict[str, Dict[str, Any]]:
        """
        Get supported domains
        
        Returns:
            Dict of domain IDs and domain info
        """
        # Return simplified domain info
        return {
            domain_id: {
                "name": domain.get("name", domain_id),
                "description": domain.get("description", ""),
                "keywords": domain.get("keywords", [])[:5]  # Return only first 5 keywords
            }
            for domain_id, domain in self.domains.items()
        }
    
    def reset_session(self, session_id: str):
        """
        Reset session state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
        
        if session_id in self.session_domains:
            del self.session_domains[session_id]
            
            # Remove session domain profile file
            profile_path = os.path.join(self.domains_dir, f"session_{session_id}.json")
            if os.path.exists(profile_path):
                os.remove(profile_path)
    
    def close(self):
        """Close domain-specific STT manager and free resources"""
        self.session_states.clear()
        self.session_domains.clear()
        self.is_initialized = False
        logger.info("Domain-specific STT manager closed")


# Global domain-specific STT manager instance
domain_specific_stt = DomainSpecificSTT()