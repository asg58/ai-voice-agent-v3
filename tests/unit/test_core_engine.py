"""
Unit Tests for Core Engine Service

Tests for the AI orchestration engine and related components.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from datetime import datetime

from services.core_engine.app.core.ai_orchestrator import AIOrchestrator
from services.core_engine.app.models.requests import ProcessingRequest, ConversationRequest
from services.core_engine.app.models.responses import ProcessingResponse, ConversationResponse


class TestAIOrchestrator:
    """Test cases for AIOrchestrator class."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create an AIOrchestrator instance for testing."""
        return AIOrchestrator()
    
    @pytest.fixture
    async def initialized_orchestrator(self, orchestrator):
        """Create and initialize an AIOrchestrator instance."""
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.cleanup()
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.models == {}
        assert orchestrator.services == {}
        assert not orchestrator.initialized
        assert isinstance(orchestrator.start_time, datetime)
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialize(self, orchestrator):
        """Test orchestrator initialization process."""
        await orchestrator.initialize()
        
        assert orchestrator.initialized
        assert 'openai' in orchestrator.models
        assert 'vector_db' in orchestrator.services
        assert orchestrator.models['openai']['status'] == 'connected'
        
        await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_text_processing(self, initialized_orchestrator):
        """Test text processing functionality."""
        input_data = {"text": "Hello, AI assistant!"}
        context = {"user_id": "test_user"}
        
        result = await initialized_orchestrator.process_request(
            input_data=input_data,
            request_type="text",
            context=context
        )
        
        assert result["type"] == "text"
        assert result["input"] == "Hello, AI assistant!"
        assert "AI processed:" in result["response"]
        assert result["context"] == context
    
    @pytest.mark.asyncio
    async def test_voice_processing(self, initialized_orchestrator):
        """Test voice processing functionality."""
        input_data = {"audio_data": b"fake_audio", "transcription": "Hello world"}
        
        result = await initialized_orchestrator.process_request(
            input_data=input_data,
            request_type="voice"
        )
        
        assert result["type"] == "voice"
        assert result["response"] == "Voice processed successfully"
        assert result["transcription"] == "Hello world"
    
    @pytest.mark.asyncio
    async def test_document_processing(self, initialized_orchestrator):
        """Test document processing functionality."""
        input_data = {"document": "test.pdf", "content": "Document content"}
        
        result = await initialized_orchestrator.process_request(
            input_data=input_data,
            request_type="document"
        )
        
        assert result["type"] == "document"
        assert result["response"] == "Document processed successfully"
        assert result["extracted_content"] == "Document content"
    
    @pytest.mark.asyncio
    async def test_conversation_handling(self, initialized_orchestrator):
        """Test conversation handling."""
        message = "What is the weather today?"
        session_id = "test_session_123"
        context = {"location": "Amsterdam"}
        
        response = await initialized_orchestrator.handle_conversation(
            message=message,
            session_id=session_id,
            context=context
        )
        
        assert isinstance(response, str)
        assert message in response
        assert "AI Assistant:" in response
    
    @pytest.mark.asyncio
    async def test_unsupported_request_type(self, initialized_orchestrator):
        """Test handling of unsupported request types."""
        with pytest.raises(ValueError, match="Unsupported request type"):
            await initialized_orchestrator.process_request(
                input_data={},
                request_type="unknown_type"
            )
    
    @pytest.mark.asyncio
    async def test_uninitialized_orchestrator_error(self, orchestrator):
        """Test error handling for uninitialized orchestrator."""
        with pytest.raises(RuntimeError, match="AI Orchestrator not initialized"):
            await orchestrator.process_request(
                input_data={},
                request_type="text"
            )
    
    @pytest.mark.asyncio
    async def test_get_status(self, initialized_orchestrator):
        """Test status retrieval."""
        status = await initialized_orchestrator.get_status()
        
        assert status["initialized"] is True
        assert "uptime_seconds" in status
        assert "start_time" in status
        assert "models" in status
        assert "services" in status
        assert status["health"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_cleanup(self, orchestrator):
        """Test cleanup functionality."""
        await orchestrator.initialize()
        assert orchestrator.initialized
        
        await orchestrator.cleanup()
        assert not orchestrator.initialized
        assert orchestrator.models == {}
        assert orchestrator.services == {}


class TestRequestModels:
    """Test cases for request models."""
    
    def test_processing_request_creation(self):
        """Test ProcessingRequest model creation."""
        request = ProcessingRequest(
            request_id="test_123",
            request_type="text",
            input_data={"text": "test input"},
            context={"user": "test_user"}
        )
        
        assert request.request_id == "test_123"
        assert request.request_type == "text"
        assert request.input_data == {"text": "test input"}
        assert request.context == {"user": "test_user"}
        assert isinstance(request.timestamp, datetime)
    
    def test_conversation_request_creation(self):
        """Test ConversationRequest model creation."""
        request = ConversationRequest(
            session_id="session_123",
            message="Hello AI",
            context={"location": "Amsterdam"}
        )
        
        assert request.session_id == "session_123"
        assert request.message == "Hello AI"
        assert request.context == {"location": "Amsterdam"}
        assert isinstance(request.timestamp, datetime)


class TestResponseModels:
    """Test cases for response models."""
    
    def test_processing_response_creation(self):
        """Test ProcessingResponse model creation."""
        response = ProcessingResponse(
            request_id="test_123",
            status="success",
            result={"output": "processed data"},
            processing_time=1.5
        )
        
        assert response.request_id == "test_123"
        assert response.status == "success"
        assert response.result == {"output": "processed data"}
        assert response.processing_time == 1.5
        assert isinstance(response.timestamp, datetime)
    
    def test_conversation_response_creation(self):
        """Test ConversationResponse model creation."""
        response = ConversationResponse(
            session_id="session_123",
            response="AI response here",
            status="success",
            context={"updated": "context"}
        )
        
        assert response.session_id == "session_123"
        assert response.response == "AI response here"
        assert response.status == "success"
        assert response.context == {"updated": "context"}
        assert isinstance(response.timestamp, datetime)


# Integration test examples
class TestIntegration:
    """Integration tests for core engine components."""
    
    @pytest.mark.asyncio
    async def test_full_processing_pipeline(self):
        """Test the complete processing pipeline."""
        orchestrator = AIOrchestrator()
        
        try:
            # Initialize
            await orchestrator.initialize()
            
            # Create a processing request
            input_data = {"text": "Process this text through AI"}
            
            # Process the request
            result = await orchestrator.process_request(
                input_data=input_data,
                request_type="text",
                context={"pipeline": "integration_test"}
            )
            
            # Verify result structure
            assert "type" in result
            assert "response" in result
            assert "processed_at" in result
            assert "context" in result
            
            # Verify processing worked
            assert result["type"] == "text"
            assert "AI processed:" in result["response"]
            
        finally:
            await orchestrator.cleanup()


# Fixtures for shared test data
@pytest.fixture
def sample_text_request():
    """Sample text processing request."""
    return {
        "request_id": "text_test_001",
        "request_type": "text",
        "input_data": {"text": "Sample text for processing"},
        "context": {"user_id": "test_user", "session_id": "test_session"}
    }


@pytest.fixture
def sample_voice_request():
    """Sample voice processing request."""
    return {
        "request_id": "voice_test_001",
        "request_type": "voice",
        "input_data": {
            "audio_data": b"fake_audio_bytes",
            "format": "wav",
            "sample_rate": 16000
        },
        "context": {"user_id": "test_user"}
    }


# Performance tests
class TestPerformance:
    """Performance tests for core engine."""
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test concurrent request processing."""
        orchestrator = AIOrchestrator()
        
        try:
            await orchestrator.initialize()
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = orchestrator.process_request(
                    input_data={"text": f"Concurrent request {i}"},
                    request_type="text"
                )
                tasks.append(task)
            
            # Process all requests concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all requests completed successfully
            assert len(results) == 10
            for i, result in enumerate(results):
                assert result["type"] == "text"
                assert f"Concurrent request {i}" in result["input"]
                
        finally:
            await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_processing_latency(self):
        """Test processing latency requirements."""
        orchestrator = AIOrchestrator()
        
        try:
            await orchestrator.initialize()
            
            start_time = asyncio.get_event_loop().time()
            
            result = await orchestrator.process_request(
                input_data={"text": "Latency test"},
                request_type="text"
            )
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            # Verify processing completed within acceptable time
            assert processing_time < 2.0  # Should complete within 2 seconds
            assert result["type"] == "text"
            
        finally:
            await orchestrator.cleanup()