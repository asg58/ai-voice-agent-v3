"""
Conversation Analysis Module

Provides conversation analysis capabilities:
- Sentiment analysis
- Topic detection
- Intent recognition
- Entity extraction
- Conversation metrics
"""
import logging
import time
import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import defaultdict
import asyncio

from src.config import settings
from src.models import ConversationMessage, ConversationSession

logger = logging.getLogger(__name__)


class ConversationAnalysis:
    """
    Conversation analysis manager
    
    Features:
    - Sentiment analysis
    - Topic detection
    - Intent recognition
    - Entity extraction
    - Conversation metrics
    """
    
    def __init__(self):
        """Initialize conversation analysis manager"""
        self.is_initialized = False
        
        # Get config
        self.config = settings.ServiceConfig()
        
        # Configuration
        self.enabled = self.config.conversation_analysis_enabled
        self.sentiment_analysis_enabled = self.config.sentiment_analysis_enabled
        self.topic_detection_enabled = self.config.topic_detection_enabled
        self.intent_recognition_enabled = self.config.intent_recognition_enabled
        self.entity_extraction_enabled = self.config.entity_extraction_enabled
        
        # Models
        self.sentiment_model = None
        self.topic_model = None
        self.intent_model = None
        self.entity_model = None
        
        # Session state
        self.session_states = {}
        
        logger.info(f"Conversation analysis manager initialized (enabled: {self.enabled})")
    
    async def initialize(self) -> bool:
        """
        Initialize conversation analysis manager
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize models
            if self.sentiment_analysis_enabled:
                await self._initialize_sentiment_model()
            
            if self.topic_detection_enabled:
                await self._initialize_topic_model()
            
            if self.intent_recognition_enabled:
                await self._initialize_intent_model()
            
            if self.entity_extraction_enabled:
                await self._initialize_entity_model()
            
            self.is_initialized = True
            logger.info("Conversation analysis manager initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize conversation analysis manager: {e}")
            return False
    
    async def _initialize_sentiment_model(self):
        """Initialize sentiment analysis model"""
        try:
            # Try to import transformers for sentiment analysis
            from transformers import pipeline
            
            # Initialize sentiment analysis pipeline
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment"
            )
            
            logger.info("Sentiment analysis model initialized")
        
        except ImportError:
            logger.warning("Transformers not available, using simplified sentiment analysis")
            
            # Define simplified sentiment analysis function
            def simple_sentiment_analysis(text):
                # Define positive and negative word lists
                positive_words = {
                    "en": ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "happy", "pleased", "satisfied", "love", "like"],
                    "nl": ["goed", "geweldig", "uitstekend", "verbazingwekkend", "prachtig", "fantastisch", "blij", "tevreden", "voldaan", "houden van", "leuk"]
                }
                
                negative_words = {
                    "en": ["bad", "terrible", "awful", "horrible", "poor", "disappointing", "sad", "unhappy", "dissatisfied", "hate", "dislike"],
                    "nl": ["slecht", "verschrikkelijk", "afschuwelijk", "vreselijk", "arm", "teleurstellend", "verdrietig", "ongelukkig", "ontevreden", "haat", "afkeer"]
                }
                
                # Detect language
                if any(word in text.lower() for word in ["de", "het", "een", "ik", "jij", "wij", "zij", "en", "of", "maar"]):
                    language = "nl"
                else:
                    language = "en"
                
                # Count positive and negative words
                positive_count = sum(1 for word in positive_words[language] if re.search(r'\b' + re.escape(word) + r'\b', text.lower()))
                negative_count = sum(1 for word in negative_words[language] if re.search(r'\b' + re.escape(word) + r'\b', text.lower()))
                
                # Calculate sentiment score
                if positive_count > negative_count:
                    label = "positive"
                    score = 0.5 + 0.5 * (positive_count / (positive_count + negative_count + 1))
                elif negative_count > positive_count:
                    label = "negative"
                    score = 0.5 - 0.5 * (negative_count / (positive_count + negative_count + 1))
                else:
                    label = "neutral"
                    score = 0.5
                
                return [{"label": label, "score": score}]
            
            self.sentiment_model = simple_sentiment_analysis
            logger.info("Simplified sentiment analysis initialized")
    
    async def _initialize_topic_model(self):
        """Initialize topic detection model"""
        try:
            # Define topic detection function
            def detect_topics(text, language="en"):
                # Define topic keywords
                topics = {
                    "en": {
                        "weather": ["weather", "temperature", "rain", "sunny", "forecast", "climate", "cold", "hot", "warm", "storm"],
                        "health": ["health", "doctor", "hospital", "medicine", "sick", "illness", "disease", "symptom", "treatment", "cure"],
                        "technology": ["technology", "computer", "software", "hardware", "internet", "app", "website", "digital", "tech", "device"],
                        "finance": ["finance", "money", "bank", "investment", "loan", "credit", "debt", "financial", "budget", "expense"],
                        "travel": ["travel", "vacation", "trip", "flight", "hotel", "booking", "destination", "tourism", "tourist", "journey"],
                        "food": ["food", "restaurant", "meal", "recipe", "cooking", "chef", "dish", "cuisine", "ingredient", "taste"],
                        "entertainment": ["entertainment", "movie", "film", "music", "concert", "show", "performance", "actor", "actress", "singer"],
                        "sports": ["sports", "game", "team", "player", "match", "competition", "tournament", "championship", "athlete", "coach"],
                        "education": ["education", "school", "university", "college", "student", "teacher", "professor", "course", "class", "learning"],
                        "politics": ["politics", "government", "election", "politician", "party", "president", "minister", "policy", "vote", "campaign"]
                    },
                    "nl": {
                        "weer": ["weer", "temperatuur", "regen", "zonnig", "voorspelling", "klimaat", "koud", "heet", "warm", "storm"],
                        "gezondheid": ["gezondheid", "dokter", "ziekenhuis", "medicijn", "ziek", "ziekte", "aandoening", "symptoom", "behandeling", "genezing"],
                        "technologie": ["technologie", "computer", "software", "hardware", "internet", "app", "website", "digitaal", "tech", "apparaat"],
                        "financiën": ["financiën", "geld", "bank", "investering", "lening", "krediet", "schuld", "financieel", "budget", "uitgave"],
                        "reizen": ["reizen", "vakantie", "trip", "vlucht", "hotel", "boeking", "bestemming", "toerisme", "toerist", "reis"],
                        "eten": ["eten", "restaurant", "maaltijd", "recept", "koken", "chef", "gerecht", "keuken", "ingrediënt", "smaak"],
                        "entertainment": ["entertainment", "film", "muziek", "concert", "show", "optreden", "acteur", "actrice", "zanger", "zangeres"],
                        "sport": ["sport", "spel", "team", "speler", "wedstrijd", "competitie", "toernooi", "kampioenschap", "atleet", "coach"],
                        "onderwijs": ["onderwijs", "school", "universiteit", "hogeschool", "student", "leraar", "professor", "cursus", "klas", "leren"],
                        "politiek": ["politiek", "overheid", "verkiezing", "politicus", "partij", "president", "minister", "beleid", "stem", "campagne"]
                    }
                }
                
                # Detect language if not provided
                if language not in topics:
                    if any(word in text.lower() for word in ["de", "het", "een", "ik", "jij", "wij", "zij", "en", "of", "maar"]):
                        language = "nl"
                    else:
                        language = "en"
                
                # Count topic keywords
                topic_scores = {}
                
                for topic, keywords in topics[language].items():
                    count = sum(1 for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text.lower()))
                    if count > 0:
                        topic_scores[topic] = count
                
                # Sort topics by score
                sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
                
                # Return top topics
                return [
                    {"topic": topic, "score": score / sum(topic_scores.values())}
                    for topic, score in sorted_topics[:3] if score > 0
                ]
            
            self.topic_model = detect_topics
            logger.info("Topic detection model initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize topic detection model: {e}")
            self.topic_model = lambda text, language="en": []
    
    async def _initialize_intent_model(self):
        """Initialize intent recognition model"""
        try:
            # Define intent recognition function
            def recognize_intent(text, language="en"):
                # Define intent patterns
                intents = {
                    "en": {
                        "greeting": [
                            r'\b(?:hello|hi|hey|good\s+(?:morning|afternoon|evening)|greetings)\b',
                        ],
                        "farewell": [
                            r'\b(?:goodbye|bye|see\s+you|farewell|later)\b',
                        ],
                        "thanks": [
                            r'\b(?:thank|thanks|appreciate|grateful)\b',
                        ],
                        "help": [
                            r'\b(?:help|assist|support|guide)\b',
                            r'\bcan\s+you\s+help\b',
                            r'\bhow\s+(?:do|can|should)\s+I\b',
                        ],
                        "info": [
                            r'\b(?:what|who|where|when|why|how)\b',
                            r'\bcan\s+you\s+tell\s+me\b',
                            r'\bI\s+(?:want|need)\s+to\s+know\b',
                        ],
                        "booking": [
                            r'\b(?:book|reserve|schedule|appointment)\b',
                            r'\bI\s+(?:want|need|would\s+like)\s+to\s+(?:book|reserve|schedule)\b',
                        ],
                        "complaint": [
                            r'\b(?:complaint|problem|issue|wrong|error|mistake|unhappy|dissatisfied)\b',
                            r'\bI\s+(?:have|am\s+having)\s+(?:a|an)\s+(?:problem|issue)\b',
                        ],
                        "feedback": [
                            r'\b(?:feedback|review|opinion|suggest|recommendation)\b',
                            r'\bI\s+(?:want|would\s+like)\s+to\s+(?:give|provide)\s+feedback\b',
                        ]
                    },
                    "nl": {
                        "greeting": [
                            r'\b(?:hallo|hoi|hey|goedemorgen|goedemiddag|goedenavond|groeten)\b',
                        ],
                        "farewell": [
                            r'\b(?:doei|tot\s+ziens|tot\s+later|dag|vaarwel)\b',
                        ],
                        "thanks": [
                            r'\b(?:bedankt|dank|dankjewel|dankuwel|dank\s+je|dank\s+u)\b',
                        ],
                        "help": [
                            r'\b(?:help|hulp|assistentie|ondersteuning)\b',
                            r'\bkun\s+je\s+(?:me|mij)\s+helpen\b',
                            r'\bhoe\s+(?:kan|moet)\s+ik\b',
                        ],
                        "info": [
                            r'\b(?:wat|wie|waar|wanneer|waarom|hoe)\b',
                            r'\bkun\s+je\s+(?:me|mij)\s+vertellen\b',
                            r'\bik\s+(?:wil|moet)\s+weten\b',
                        ],
                        "booking": [
                            r'\b(?:boeken|reserveren|afspraak|plannen)\b',
                            r'\bik\s+(?:wil|zou\s+graag)\s+(?:boeken|reserveren|een\s+afspraak\s+maken)\b',
                        ],
                        "complaint": [
                            r'\b(?:klacht|probleem|kwestie|fout|verkeerd|ontevreden)\b',
                            r'\bik\s+(?:heb|ervaar)\s+(?:een)\s+(?:probleem|kwestie)\b',
                        ],
                        "feedback": [
                            r'\b(?:feedback|recensie|mening|suggestie|aanbeveling)\b',
                            r'\bik\s+(?:wil|zou\s+graag)\s+(?:feedback|een\s+mening)\s+(?:geven|delen)\b',
                        ]
                    }
                }
                
                # Detect language if not provided
                if language not in intents:
                    if any(word in text.lower() for word in ["de", "het", "een", "ik", "jij", "wij", "zij", "en", "of", "maar"]):
                        language = "nl"
                    else:
                        language = "en"
                
                # Check for intents
                detected_intents = []
                
                for intent, patterns in intents[language].items():
                    for pattern in patterns:
                        if re.search(pattern, text.lower()):
                            detected_intents.append({"intent": intent, "score": 0.8})
                            break
                
                # If no intent detected, return "other"
                if not detected_intents:
                    detected_intents.append({"intent": "other", "score": 0.5})
                
                return detected_intents
            
            self.intent_model = recognize_intent
            logger.info("Intent recognition model initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize intent recognition model: {e}")
            self.intent_model = lambda text, language="en": [{"intent": "other", "score": 0.5}]
    
    async def _initialize_entity_model(self):
        """Initialize entity extraction model"""
        try:
            # Define entity extraction function
            def extract_entities(text, language="en"):
                entities = []
                
                # Extract dates
                date_patterns = {
                    "en": [
                        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
                        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december),?\s+\d{4}\b',
                        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
                        r'\b\d{4}-\d{2}-\d{2}\b'
                    ],
                    "nl": [
                        r'\b(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{1,2},?\s+\d{4}\b',
                        r'\b\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december),?\s+\d{4}\b',
                        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
                        r'\b\d{4}-\d{2}-\d{2}\b'
                    ]
                }
                
                # Detect language if not provided
                if language not in date_patterns:
                    if any(word in text.lower() for word in ["de", "het", "een", "ik", "jij", "wij", "zij", "en", "of", "maar"]):
                        language = "nl"
                    else:
                        language = "en"
                
                # Extract dates
                for pattern in date_patterns[language]:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entities.append({
                            "entity": "date",
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                # Extract times
                time_patterns = [
                    r'\b\d{1,2}:\d{2}\b',
                    r'\b\d{1,2}(?:am|pm)\b',
                    r'\b\d{1,2}\s+(?:am|pm)\b',
                    r'\b(?:noon|midnight)\b'
                ]
                
                for pattern in time_patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entities.append({
                            "entity": "time",
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                # Extract money
                money_patterns = [
                    r'\$\s*\d+(?:[,.]\d+)*',
                    r'€\s*\d+(?:[,.]\d+)*',
                    r'\d+(?:[,.]\d+)*\s*(?:dollars|euros|pounds|yen|euro|dollar|pound|euro\'s)'
                ]
                
                for pattern in money_patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entities.append({
                            "entity": "money",
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                # Extract percentages
                percentage_patterns = [
                    r'\d+(?:[,.]\d+)*\s*%',
                    r'\d+(?:[,.]\d+)*\s*percent',
                    r'\d+(?:[,.]\d+)*\s*procent'
                ]
                
                for pattern in percentage_patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entities.append({
                            "entity": "percentage",
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                # Extract phone numbers
                phone_patterns = [
                    r'\+\d{1,3}\s*\d{3}[\s-]?\d{3}[\s-]?\d{4}',
                    r'\(\d{3}\)\s*\d{3}[\s-]?\d{4}',
                    r'\d{3}[\s-]?\d{3}[\s-]?\d{4}'
                ]
                
                for pattern in phone_patterns:
                    for match in re.finditer(pattern, text):
                        entities.append({
                            "entity": "phone",
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                # Extract email addresses
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                
                for match in re.finditer(email_pattern, text):
                    entities.append({
                        "entity": "email",
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end()
                    })
                
                # Extract URLs
                url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!./?=&]*)?'
                
                for match in re.finditer(url_pattern, text):
                    entities.append({
                        "entity": "url",
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end()
                    })
                
                return entities
            
            self.entity_model = extract_entities
            logger.info("Entity extraction model initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize entity extraction model: {e}")
            self.entity_model = lambda text, language="en": []
    
    async def analyze_message(self, message: ConversationMessage, session: ConversationSession) -> Dict[str, Any]:
        """
        Analyze conversation message
        
        Args:
            message: Conversation message
            session: Conversation session
            
        Returns:
            Dict of analysis results
        """
        if not self.is_initialized or not self.enabled:
            return {}
        
        try:
            # Get session ID
            session_id = session.session_id
            
            # Create session state if it doesn't exist
            if session_id not in self.session_states:
                self._create_session_state(session_id)
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Get language
            language = session.language or "nl"
            
            # Initialize analysis results
            analysis = {}
            
            # Analyze sentiment
            if self.sentiment_analysis_enabled and message.role == "user":
                sentiment = await self._analyze_sentiment(message.content, language)
                analysis["sentiment"] = sentiment
                
                # Update session sentiment
                session_state["sentiment_history"].append(sentiment)
                session_state["current_sentiment"] = sentiment
            
            # Detect topics
            if self.topic_detection_enabled and message.role == "user":
                topics = await self._detect_topics(message.content, language)
                analysis["topics"] = topics
                
                # Update session topics
                for topic in topics:
                    session_state["topics"][topic["topic"]] = session_state["topics"].get(topic["topic"], 0) + topic["score"]
            
            # Recognize intent
            if self.intent_recognition_enabled and message.role == "user":
                intents = await self._recognize_intent(message.content, language)
                analysis["intents"] = intents
                
                # Update session intents
                for intent in intents:
                    session_state["intents"][intent["intent"]] = session_state["intents"].get(intent["intent"], 0) + 1
            
            # Extract entities
            if self.entity_extraction_enabled and message.role == "user":
                entities = await self._extract_entities(message.content, language)
                analysis["entities"] = entities
                
                # Update session entities
                for entity in entities:
                    entity_type = entity["entity"]
                    entity_value = entity["value"]
                    
                    if entity_type not in session_state["entities"]:
                        session_state["entities"][entity_type] = []
                    
                    if entity_value not in session_state["entities"][entity_type]:
                        session_state["entities"][entity_type].append(entity_value)
            
            # Update message count
            if message.role == "user":
                session_state["user_message_count"] += 1
                session_state["total_user_words"] += len(message.content.split())
            elif message.role == "assistant":
                session_state["assistant_message_count"] += 1
                session_state["total_assistant_words"] += len(message.content.split())
            
            # Update last activity
            session_state["last_activity"] = time.time()
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return {}
    
    def _create_session_state(self, session_id: str):
        """
        Create session state
        
        Args:
            session_id: Session ID
        """
        self.session_states[session_id] = {
            "sentiment_history": [],
            "current_sentiment": None,
            "topics": {},
            "intents": {},
            "entities": {},
            "user_message_count": 0,
            "assistant_message_count": 0,
            "total_user_words": 0,
            "total_assistant_words": 0,
            "last_activity": time.time()
        }
    
    async def _analyze_sentiment(self, text: str, language: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            Sentiment analysis result
        """
        try:
            if self.sentiment_model:
                result = self.sentiment_model(text)
                
                if isinstance(result, list) and len(result) > 0:
                    return {
                        "label": result[0]["label"],
                        "score": result[0]["score"]
                    }
            
            return {
                "label": "neutral",
                "score": 0.5
            }
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "label": "neutral",
                "score": 0.5
            }
    
    async def _detect_topics(self, text: str, language: str) -> List[Dict[str, Any]]:
        """
        Detect topics in text
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of detected topics
        """
        try:
            if self.topic_model:
                return self.topic_model(text, language)
            
            return []
        
        except Exception as e:
            logger.error(f"Error detecting topics: {e}")
            return []
    
    async def _recognize_intent(self, text: str, language: str) -> List[Dict[str, Any]]:
        """
        Recognize intent in text
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of recognized intents
        """
        try:
            if self.intent_model:
                return self.intent_model(text, language)
            
            return [{"intent": "other", "score": 0.5}]
        
        except Exception as e:
            logger.error(f"Error recognizing intent: {e}")
            return [{"intent": "other", "score": 0.5}]
    
    async def _extract_entities(self, text: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of extracted entities
        """
        try:
            if self.entity_model:
                return self.entity_model(text, language)
            
            return []
        
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """
        Get analysis for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session analysis
        """
        if not self.is_initialized or not self.enabled:
            return {}
        
        try:
            # Check if session exists
            if session_id not in self.session_states:
                return {}
            
            # Get session state
            session_state = self.session_states[session_id]
            
            # Calculate metrics
            avg_user_words = session_state["total_user_words"] / session_state["user_message_count"] if session_state["user_message_count"] > 0 else 0
            avg_assistant_words = session_state["total_assistant_words"] / session_state["assistant_message_count"] if session_state["assistant_message_count"] > 0 else 0
            
            # Get top topics
            top_topics = sorted(session_state["topics"].items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Get top intents
            top_intents = sorted(session_state["intents"].items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Create analysis result
            analysis = {
                "session_id": session_id,
                "metrics": {
                    "user_message_count": session_state["user_message_count"],
                    "assistant_message_count": session_state["assistant_message_count"],
                    "total_user_words": session_state["total_user_words"],
                    "total_assistant_words": session_state["total_assistant_words"],
                    "avg_user_words": avg_user_words,
                    "avg_assistant_words": avg_assistant_words
                },
                "sentiment": {
                    "current": session_state["current_sentiment"],
                    "history": session_state["sentiment_history"][-5:] if session_state["sentiment_history"] else []
                },
                "topics": {topic: score for topic, score in top_topics},
                "intents": {intent: count for intent, count in top_intents},
                "entities": session_state["entities"]
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error getting session analysis: {e}")
            return {}
    
    def reset_session(self, session_id: str):
        """
        Reset session state
        
        Args:
            session_id: Session ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
    
    def close(self):
        """Close conversation analysis manager and free resources"""
        self.session_states.clear()
        self.is_initialized = False
        logger.info("Conversation analysis manager closed")


# Global conversation analysis manager instance
conversation_analysis = ConversationAnalysis()