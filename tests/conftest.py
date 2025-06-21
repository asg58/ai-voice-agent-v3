"""
Global pytest configuration and fixtures
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path to allow importing from modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Add services to Python path
services_path = project_root / "services"
sys.path.append(str(services_path))

# Create a mapping for hyphenated directory names
sys.path.insert(0, str(project_root))

# Import common fixtures that can be used across all tests
@pytest.fixture
def test_env():
    """Return a dictionary with test environment configuration"""
    return {
        "test_mode": True,
        "debug": True,
        "api_base_url": "http://localhost:8000",
        "mock_external_services": True
    }

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        async def get(self, key):
            return self.data.get(key)
            
        async def set(self, key, value, ex=None):
            self.data[key] = value
            
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
                
        async def exists(self, key):
            return key in self.data
            
        async def close(self):
            pass
    
    return MockRedis()

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    class MockDBSession:
        def __init__(self):
            self.committed = False
            self.rolled_back = False
            
        async def commit(self):
            self.committed = True
            
        async def rollback(self):
            self.rolled_back = True
            
        async def close(self):
            pass
            
        def __await__(self):
            async def _await_impl():
                return self
            return _await_impl().__await__()
    
    return MockDBSession()

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing external API calls"""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None, text=""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.text = text
            
        async def json(self):
            return self._json_data
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockHTTPClient:
        def __init__(self):
            self.responses = {}
            self.requests = []
            
        def add_response(self, url, method="GET", status_code=200, json_data=None, text=""):
            key = (method, url)
            self.responses[key] = MockResponse(status_code, json_data, text)
            
        async def request(self, method, url, **kwargs):
            self.requests.append((method, url, kwargs))
            key = (method, url)
            if key in self.responses:
                return self.responses[key]
            return MockResponse(404, {"error": "Not found"}, "Not found")
            
        async def get(self, url, **kwargs):
            return await self.request("GET", url, **kwargs)
            
        async def post(self, url, **kwargs):
            return await self.request("POST", url, **kwargs)
            
        async def put(self, url, **kwargs):
            return await self.request("PUT", url, **kwargs)
            
        async def delete(self, url, **kwargs):
            return await self.request("DELETE", url, **kwargs)
            
        async def close(self):
            pass
    
    return MockHTTPClient()