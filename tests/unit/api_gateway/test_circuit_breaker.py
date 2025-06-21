"""
Unit tests for API Gateway circuit breaker middleware
"""
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Import the module to test
from services.api_gateway.app.middleware.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    get_circuit_breaker,
    circuit_breaker_middleware
)


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker for testing"""
    return CircuitBreaker(
        name="test-service",
        failure_threshold=3,
        recovery_timeout=5,
        half_open_max_calls=2
    )


@pytest.fixture
def mock_request():
    """Create a mock request for testing"""
    mock = MagicMock()
    mock.url = MagicMock()
    mock.url.path = "/api/v1/test-service/endpoint"
    return mock


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "SERVICE_ROUTES": {
            "test-service": {
                "prefix": "/api/v1/test-service"
            }
        },
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD": 3,
        "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": 5
    }


def test_circuit_breaker_initial_state(circuit_breaker):
    """Test initial state of circuit breaker"""
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0
    assert circuit_breaker.half_open_calls == 0
    assert circuit_breaker.half_open_successes == 0


def test_circuit_breaker_record_success_closed(circuit_breaker):
    """Test recording success in closed state"""
    circuit_breaker.state = CircuitState.CLOSED
    circuit_breaker.failure_count = 2
    
    circuit_breaker.record_success()
    
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0


def test_circuit_breaker_record_success_half_open(circuit_breaker):
    """Test recording success in half-open state"""
    circuit_breaker.state = CircuitState.HALF_OPEN
    circuit_breaker.half_open_successes = 0
    circuit_breaker.half_open_max_calls = 2
    
    # First success
    circuit_breaker.record_success()
    assert circuit_breaker.state == CircuitState.HALF_OPEN
    assert circuit_breaker.half_open_successes == 1
    
    # Second success should close the circuit
    circuit_breaker.record_success()
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0
    assert circuit_breaker.half_open_calls == 0
    assert circuit_breaker.half_open_successes == 0


def test_circuit_breaker_record_failure_closed(circuit_breaker):
    """Test recording failure in closed state"""
    circuit_breaker.state = CircuitState.CLOSED
    circuit_breaker.failure_count = 0
    circuit_breaker.failure_threshold = 3
    
    # First failure
    circuit_breaker.record_failure()
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 1
    
    # Second failure
    circuit_breaker.record_failure()
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 2
    
    # Third failure should open the circuit
    circuit_breaker.record_failure()
    assert circuit_breaker.state == CircuitState.OPEN
    assert circuit_breaker.failure_count == 3


def test_circuit_breaker_record_failure_half_open(circuit_breaker):
    """Test recording failure in half-open state"""
    circuit_breaker.state = CircuitState.HALF_OPEN
    circuit_breaker.half_open_calls = 1
    circuit_breaker.half_open_successes = 1
    
    circuit_breaker.record_failure()
    
    assert circuit_breaker.state == CircuitState.OPEN
    assert circuit_breaker.half_open_calls == 0
    assert circuit_breaker.half_open_successes == 0


def test_circuit_breaker_allow_request_closed(circuit_breaker):
    """Test allow_request in closed state"""
    circuit_breaker.state = CircuitState.CLOSED
    
    assert circuit_breaker.allow_request() is True


def test_circuit_breaker_allow_request_open_timeout_not_elapsed(circuit_breaker):
    """Test allow_request in open state with timeout not elapsed"""
    circuit_breaker.state = CircuitState.OPEN
    circuit_breaker.last_failure_time = time.time()
    circuit_breaker.recovery_timeout = 30
    
    assert circuit_breaker.allow_request() is False


def test_circuit_breaker_allow_request_open_timeout_elapsed(circuit_breaker):
    """Test allow_request in open state with timeout elapsed"""
    circuit_breaker.state = CircuitState.OPEN
    circuit_breaker.last_failure_time = time.time() - 10
    circuit_breaker.recovery_timeout = 5
    
    assert circuit_breaker.allow_request() is True
    assert circuit_breaker.state == CircuitState.HALF_OPEN
    assert circuit_breaker.half_open_calls == 1


def test_circuit_breaker_allow_request_half_open(circuit_breaker):
    """Test allow_request in half-open state"""
    circuit_breaker.state = CircuitState.HALF_OPEN
    circuit_breaker.half_open_calls = 0
    circuit_breaker.half_open_max_calls = 2
    
    # First call
    assert circuit_breaker.allow_request() is True
    assert circuit_breaker.half_open_calls == 1
    
    # Second call
    assert circuit_breaker.allow_request() is True
    assert circuit_breaker.half_open_calls == 2
    
    # Third call should be rejected
    assert circuit_breaker.allow_request() is False
    assert circuit_breaker.half_open_calls == 2


def test_get_circuit_breaker():
    """Test getting a circuit breaker for a service"""
    with patch('services.api_gateway.app.middleware.circuit_breaker.circuit_breakers', {}):
        with patch('services.api_gateway.app.middleware.circuit_breaker.settings') as mock_settings:
            mock_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
            mock_settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30
            
            # First call should create a new circuit breaker
            cb1 = get_circuit_breaker("test-service")
            assert cb1.name == "test-service"
            assert cb1.failure_threshold == 5
            assert cb1.recovery_timeout == 30
            
            # Second call should return the same circuit breaker
            cb2 = get_circuit_breaker("test-service")
            assert cb2 is cb1


@pytest.mark.asyncio
async def test_circuit_breaker_middleware_no_target_service(mock_request):
    """Test circuit breaker middleware with no target service"""
    # Set path that doesn't match any service
    mock_request.url.path = "/api/v1/unknown/endpoint"
    
    # Mock settings
    with patch('services.api_gateway.app.middleware.circuit_breaker.settings') as mock_settings:
        mock_settings.SERVICE_ROUTES = {}
        
        # Mock the call_next function
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        # Call the middleware
        response = await circuit_breaker_middleware(mock_request, mock_call_next)
        
        # Verify the response
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


@pytest.mark.asyncio
async def test_circuit_breaker_middleware_circuit_open(mock_request):
    """Test circuit breaker middleware with circuit open"""
    # Mock circuit breaker
    mock_circuit = MagicMock()
    mock_circuit.allow_request.return_value = False
    mock_circuit.state = CircuitState.OPEN
    
    # Mock settings and get_circuit_breaker
    with patch('services.api_gateway.app.middleware.circuit_breaker.settings') as mock_settings:
        mock_settings.SERVICE_ROUTES = {
            "test-service": {
                "prefix": "/api/v1/test-service"
            }
        }
        
        with patch('services.api_gateway.app.middleware.circuit_breaker.get_circuit_breaker', 
                  return_value=mock_circuit):
            
            # Mock the call_next function
            async def mock_call_next(request):
                return JSONResponse(content={"message": "success"})
            
            # Call the middleware
            response = await circuit_breaker_middleware(mock_request, mock_call_next)
            
            # Verify the response
            assert response.status_code == 503
            assert "Service test-service is currently unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_circuit_breaker_middleware_success(mock_request):
    """Test circuit breaker middleware with successful request"""
    # Mock circuit breaker
    mock_circuit = MagicMock()
    mock_circuit.allow_request.return_value = True
    
    # Mock settings and get_circuit_breaker
    with patch('services.api_gateway.app.middleware.circuit_breaker.settings') as mock_settings:
        mock_settings.SERVICE_ROUTES = {
            "test-service": {
                "prefix": "/api/v1/test-service"
            }
        }
        
        with patch('services.api_gateway.app.middleware.circuit_breaker.get_circuit_breaker', 
                  return_value=mock_circuit):
            
            # Mock the call_next function
            async def mock_call_next(request):
                return JSONResponse(status_code=200, content={"message": "success"})
            
            # Call the middleware
            response = await circuit_breaker_middleware(mock_request, mock_call_next)
            
            # Verify the response
            assert response.status_code == 200
            assert response.json() == {"message": "success"}
            
            # Verify circuit breaker was updated
            mock_circuit.record_success.assert_called_once()
            mock_circuit.record_failure.assert_not_called()


@pytest.mark.asyncio
async def test_circuit_breaker_middleware_server_error(mock_request):
    """Test circuit breaker middleware with server error response"""
    # Mock circuit breaker
    mock_circuit = MagicMock()
    mock_circuit.allow_request.return_value = True
    
    # Mock settings and get_circuit_breaker
    with patch('services.api_gateway.app.middleware.circuit_breaker.settings') as mock_settings:
        mock_settings.SERVICE_ROUTES = {
            "test-service": {
                "prefix": "/api/v1/test-service"
            }
        }
        
        with patch('services.api_gateway.app.middleware.circuit_breaker.get_circuit_breaker', 
                  return_value=mock_circuit):
            
            # Mock the call_next function
            async def mock_call_next(request):
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})
            
            # Call the middleware
            response = await circuit_breaker_middleware(mock_request, mock_call_next)
            
            # Verify the response
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal server error"}
            
            # Verify circuit breaker was updated
            mock_circuit.record_success.assert_not_called()
            mock_circuit.record_failure.assert_called_once()