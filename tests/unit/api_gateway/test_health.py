"""
Unit tests for API Gateway health endpoints
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Import the module to test
from services.api_gateway.app.api import health


@pytest.fixture
def mock_service_discovery():
    """Mock service discovery for testing"""
    mock = AsyncMock()
    mock.get_all_services = AsyncMock(return_value=[
        {"id": "service1", "name": "Service 1", "host": "service1", "port": 8001},
        {"id": "service2", "name": "Service 2", "host": "service2", "port": 8002},
    ])
    mock.check_health = AsyncMock(return_value=True)
    return mock


@pytest.mark.asyncio
async def test_services_health_all_healthy(mock_service_discovery):
    """Test services_health when all services are healthy"""
    # Patch the service_discovery in the health module
    with patch('services.api_gateway.app.api.health.service_discovery', mock_service_discovery):
        # Call the function
        result = await health.services_health()
        
        # Verify the result
        assert result["status"] == "healthy"
        assert result["service"] == health.settings.APP_NAME
        assert len(result["services"]) == 2
        assert all(service["status"] == "healthy" for service in result["services"])
        assert "timestamp" in result


@pytest.mark.asyncio
async def test_services_health_degraded(mock_service_discovery):
    """Test services_health when some services are unhealthy"""
    # Configure mock to return unhealthy for service2
    mock_service_discovery.check_health = AsyncMock(side_effect=lambda service_id: service_id != "service2")
    
    # Patch the service_discovery in the health module
    with patch('services.api_gateway.app.api.health.service_discovery', mock_service_discovery):
        # Call the function
        result = await health.services_health()
        
        # Verify the result
        assert result["status"] == "degraded"
        assert result["service"] == health.settings.APP_NAME
        assert len(result["services"]) == 2
        
        # Check individual service statuses
        service_statuses = {s["id"]: s["status"] for s in result["services"]}
        assert service_statuses["service1"] == "healthy"
        assert service_statuses["service2"] == "unhealthy"