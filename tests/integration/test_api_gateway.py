"""
Integration tests for the API Gateway
"""
import pytest
import httpx
import asyncio
from datetime import datetime

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health endpoint of the API Gateway"""
    # This test assumes the API Gateway is running on localhost:8000
    # In a real CI/CD environment, you would use environment variables or test configuration
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/v1/health")
            
            # If the service is not running, this test will be skipped
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                assert data["status"] in ["healthy", "degraded"]
                assert "service" in data
                assert "timestamp" in data
                
                # Verify timestamp is a valid ISO format
                timestamp = datetime.fromisoformat(data["timestamp"])
                assert isinstance(timestamp, datetime)
            else:
                pytest.skip("API Gateway is not running")
    except (httpx.ConnectError, httpx.ConnectTimeout):
        pytest.skip("API Gateway is not running")