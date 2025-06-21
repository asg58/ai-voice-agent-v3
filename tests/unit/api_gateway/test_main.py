"""
Unit tests for API Gateway main application
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the module to test
from services.api_gateway.app.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


def test_root_endpoint(test_client):
    """Test the root endpoint"""
    response = test_client.get("/")
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Welcome to the AI Voice Agent API Gateway" in response.json()["message"]
    assert "docs" in response.json()
    assert "health" in response.json()


def test_health_endpoint(test_client):
    """Test the health endpoint"""
    with patch('services.api_gateway.app.api.health.service_discovery') as mock_service_discovery:
        # Mock the service discovery client
        mock_service_discovery.get_all_services = AsyncMock(return_value=[])
        
        response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"


def test_openapi_endpoint(test_client):
    """Test the OpenAPI endpoint"""
    response = test_client.get("/api/v1/openapi.json")
    
    assert response.status_code == 200
    assert "openapi" in response.json()
    assert "paths" in response.json()
    assert "components" in response.json()


def test_docs_endpoint(test_client):
    """Test the docs endpoint"""
    response = test_client.get("/api/v1/docs")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_global_exception_handler(test_client):
    """Test the global exception handler"""
    # Create a route that raises an exception
    @app.get("/test-exception")
    async def test_exception():
        raise Exception("Test exception")
    
    # Test with debug mode off
    with patch('services.api_gateway.app.main.settings.DEBUG', False):
        response = test_client.get("/test-exception")
        
        assert response.status_code == 500
        assert "detail" in response.json()
        assert response.json()["detail"] == "Internal server error"
        assert "message" in response.json()
        assert response.json()["message"] == "An unexpected error occurred"
    
    # Test with debug mode on
    with patch('services.api_gateway.app.main.settings.DEBUG', True):
        response = test_client.get("/test-exception")
        
        assert response.status_code == 500
        assert "detail" in response.json()
        assert response.json()["detail"] == "Internal server error"
        assert "message" in response.json()
        assert response.json()["message"] == "Test exception"


@pytest.mark.asyncio
async def test_lifespan_handler():
    """Test the lifespan handler"""
    from services.api_gateway.app.main import lifespan_handler
    
    # Mock FastAPI app
    mock_app = MagicMock()
    
    # Test startup event
    with patch('services.api_gateway.app.main.initialize_components', AsyncMock()) as mock_init:
        await lifespan_handler(mock_app, "startup")
        mock_init.assert_called_once()
    
    # Test shutdown event
    with patch('services.api_gateway.app.main.cleanup_resources', AsyncMock()) as mock_cleanup:
        await lifespan_handler(mock_app, "shutdown")
        mock_cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_components():
    """Test initializing components"""
    from services.api_gateway.app.main import initialize_components
    
    with patch('services.api_gateway.app.main.rate_limiter', AsyncMock()) as mock_rate_limiter:
        with patch('services.api_gateway.app.main.service_discovery', AsyncMock()) as mock_service_discovery:
            await initialize_components()
            
            mock_rate_limiter.init_redis.assert_called_once()
            mock_service_discovery.register_service.assert_called_once()
            mock_service_discovery.refresh_services.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_resources():
    """Test cleaning up resources"""
    from services.api_gateway.app.main import cleanup_resources
    
    with patch('services.api_gateway.app.main.service_discovery', AsyncMock()) as mock_service_discovery:
        await cleanup_resources()
        
        mock_service_discovery.deregister_service.assert_called_once_with("api-gateway")
        mock_service_discovery.close.assert_called_once()