"""
Unit tests for API Gateway service discovery client
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Import the module to test
from services.api_gateway.app.services.service_discovery import ServiceDiscoveryClient


@pytest.fixture
def mock_response():
    """Create a mock HTTP response"""
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status = MagicMock()
    mock.json = MagicMock(return_value=[
        {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001,
            "health_check": "/health",
            "status": "healthy"
        },
        {
            "id": "service2",
            "name": "Service 2",
            "host": "service2",
            "port": 8002,
            "health_check": "/health",
            "status": "healthy"
        }
    ])
    return mock


@pytest.fixture
def mock_client(mock_response):
    """Create a mock HTTP client"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=mock_response)
    mock.post = AsyncMock(return_value=mock_response)
    mock.delete = AsyncMock(return_value=mock_response)
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def service_discovery_client(mock_client):
    """Create a service discovery client with mocked HTTP client"""
    client = ServiceDiscoveryClient(base_url="http://service-discovery:8080")
    client.client = mock_client
    return client


@pytest.mark.asyncio
async def test_refresh_services_success(service_discovery_client, mock_client, mock_response):
    """Test refreshing services successfully"""
    result = await service_discovery_client.refresh_services()
    
    assert result is True
    mock_client.get.assert_called_once_with("http://service-discovery:8080/services")
    assert len(service_discovery_client.services_cache) == 2
    assert "service1" in service_discovery_client.services_cache
    assert "service2" in service_discovery_client.services_cache


@pytest.mark.asyncio
async def test_refresh_services_failure(service_discovery_client, mock_client):
    """Test refreshing services with failure"""
    # Make the request fail
    mock_client.get.side_effect = httpx.RequestError("Connection error")
    
    result = await service_discovery_client.refresh_services()
    
    assert result is False
    mock_client.get.assert_called_once_with("http://service-discovery:8080/services")
    assert len(service_discovery_client.services_cache) == 0


@pytest.mark.asyncio
async def test_get_service_cached(service_discovery_client):
    """Test getting a service from cache"""
    # Populate the cache
    service_discovery_client.services_cache = {
        "service1": {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001
        }
    }
    service_discovery_client.last_refresh = asyncio.get_event_loop().time()
    
    service = await service_discovery_client.get_service("service1")
    
    assert service is not None
    assert service["id"] == "service1"
    assert service["name"] == "Service 1"


@pytest.mark.asyncio
async def test_get_service_refresh(service_discovery_client, mock_client):
    """Test getting a service with cache refresh"""
    # Set last refresh to force a refresh
    service_discovery_client.last_refresh = 0
    
    service = await service_discovery_client.get_service("service1")
    
    mock_client.get.assert_called_once_with("http://service-discovery:8080/services")
    assert service is not None
    assert service["id"] == "service1"


@pytest.mark.asyncio
async def test_get_service_not_found(service_discovery_client):
    """Test getting a non-existent service"""
    # Populate the cache
    service_discovery_client.services_cache = {
        "service1": {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001
        }
    }
    service_discovery_client.last_refresh = asyncio.get_event_loop().time()
    
    service = await service_discovery_client.get_service("nonexistent")
    
    assert service is None


@pytest.mark.asyncio
async def test_get_all_services(service_discovery_client, mock_client):
    """Test getting all services"""
    # Set last refresh to force a refresh
    service_discovery_client.last_refresh = 0
    
    services = await service_discovery_client.get_all_services()
    
    mock_client.get.assert_called_once_with("http://service-discovery:8080/services")
    assert len(services) == 2
    assert services[0]["id"] == "service1"
    assert services[1]["id"] == "service2"


@pytest.mark.asyncio
async def test_register_service_success(service_discovery_client, mock_client):
    """Test registering a service successfully"""
    service_data = {
        "id": "new-service",
        "name": "New Service",
        "host": "new-service",
        "port": 8003
    }
    
    result = await service_discovery_client.register_service(service_data)
    
    assert result is True
    mock_client.post.assert_called_once_with(
        "http://service-discovery:8080/services",
        json=service_data
    )
    mock_client.get.assert_called_once_with("http://service-discovery:8080/services")


@pytest.mark.asyncio
async def test_register_service_failure(service_discovery_client, mock_client):
    """Test registering a service with failure"""
    # Make the request fail
    mock_client.post.side_effect = httpx.RequestError("Connection error")
    
    service_data = {
        "id": "new-service",
        "name": "New Service",
        "host": "new-service",
        "port": 8003
    }
    
    result = await service_discovery_client.register_service(service_data)
    
    assert result is False
    mock_client.post.assert_called_once_with(
        "http://service-discovery:8080/services",
        json=service_data
    )


@pytest.mark.asyncio
async def test_deregister_service_success(service_discovery_client, mock_client):
    """Test deregistering a service successfully"""
    # Populate the cache
    service_discovery_client.services_cache = {
        "service1": {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001
        }
    }
    
    result = await service_discovery_client.deregister_service("service1")
    
    assert result is True
    mock_client.delete.assert_called_once_with("http://service-discovery:8080/services/service1")
    assert "service1" not in service_discovery_client.services_cache


@pytest.mark.asyncio
async def test_deregister_service_failure(service_discovery_client, mock_client):
    """Test deregistering a service with failure"""
    # Make the request fail
    mock_client.delete.side_effect = httpx.RequestError("Connection error")
    
    # Populate the cache
    service_discovery_client.services_cache = {
        "service1": {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001
        }
    }
    
    result = await service_discovery_client.deregister_service("service1")
    
    assert result is False
    mock_client.delete.assert_called_once_with("http://service-discovery:8080/services/service1")
    assert "service1" in service_discovery_client.services_cache


@pytest.mark.asyncio
async def test_check_health_success(service_discovery_client, mock_client, mock_response):
    """Test checking service health successfully"""
    # Populate the cache
    service_discovery_client.services_cache = {
        "service1": {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001,
            "health_check": "/health"
        }
    }
    service_discovery_client.last_refresh = asyncio.get_event_loop().time()
    
    # Set up mock response for health check
    mock_response.status_code = 200
    
    result = await service_discovery_client.check_health("service1")
    
    assert result is True
    mock_client.get.assert_called_once_with("http://service1:8001/health", timeout=5.0)


@pytest.mark.asyncio
async def test_check_health_failure(service_discovery_client, mock_client):
    """Test checking service health with failure"""
    # Populate the cache
    service_discovery_client.services_cache = {
        "service1": {
            "id": "service1",
            "name": "Service 1",
            "host": "service1",
            "port": 8001,
            "health_check": "/health"
        }
    }
    service_discovery_client.last_refresh = asyncio.get_event_loop().time()
    
    # Make the request fail
    mock_client.get.side_effect = httpx.RequestError("Connection error")
    
    result = await service_discovery_client.check_health("service1")
    
    assert result is False
    mock_client.get.assert_called_once_with("http://service1:8001/health", timeout=5.0)


@pytest.mark.asyncio
async def test_check_health_service_not_found(service_discovery_client, mock_client):
    """Test checking health of non-existent service"""
    # Empty cache
    service_discovery_client.services_cache = {}
    service_discovery_client.last_refresh = asyncio.get_event_loop().time()
    
    result = await service_discovery_client.check_health("nonexistent")
    
    assert result is False
    mock_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_close(service_discovery_client, mock_client):
    """Test closing the HTTP client"""
    await service_discovery_client.close()
    
    mock_client.aclose.assert_called_once()