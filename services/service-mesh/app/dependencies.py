"""
Dependency injection for Service Mesh
"""

def get_service_discovery_client():
    from app.main import app
    return app.state.service_discovery_client

def get_config_loader():
    from app.main import app
    return app.state.config_loader

def get_circuit_breaker_registry():
    from app.main import app
    return app.state.circuit_breaker_registry

def get_rate_limiter_registry():
    from app.main import app
    return app.state.rate_limiter_registry

def get_router():
    from app.main import app
    return app.state.router

def get_proxy_service():
    from app.main import app
    return app.state.proxy_service

def get_telemetry_service():
    from app.main import app
    return app.state.telemetry_service
