"""
Service models for the Service Discovery Service
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ServiceBase(BaseModel):
    """Base service model"""
    name: str = Field(..., description="Service name")
    host: str = Field(..., description="Service host")
    port: int = Field(..., description="Service port")
    health_check: str = Field(default="/health", description="Health check endpoint")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class ServiceCreate(ServiceBase):
    """Service creation model"""
    id: str = Field(..., description="Service ID")

    @validator("id")
    def id_must_be_valid(cls, v):
        """Validate service ID"""
        if not v or not v.strip():
            raise ValueError("Service ID cannot be empty")
        return v.strip()

class ServiceUpdate(BaseModel):
    """Service update model"""
    name: Optional[str] = Field(None, description="Service name")
    host: Optional[str] = Field(None, description="Service host")
    port: Optional[int] = Field(None, description="Service port")
    health_check: Optional[str] = Field(None, description="Health check endpoint")
    status: Optional[str] = Field(None, description="Service status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class Service(ServiceBase):
    """Service model returned to clients"""
    id: str = Field(..., description="Service ID")
    status: str = Field(default="unknown", description="Service status")
    registered_at: float = Field(..., description="Registration timestamp")
    last_check: float = Field(..., description="Last health check timestamp")
    last_seen: float = Field(..., description="Last seen timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "api-gateway",
                "name": "API Gateway",
                "host": "api-gateway",
                "port": 8000,
                "health_check": "/health",
                "status": "healthy",
                "registered_at": 1623456789.123,
                "last_check": 1623456789.123,
                "last_seen": 1623456789.123,
                "metadata": {
                    "version": "1.0.0",
                    "environment": "production"
                }
            }
        }

class HealthCheck(BaseModel):
    """Health check model"""
    status: str = Field(..., description="Health status")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "details": {
                    "last_check": 1623456789.123,
                    "last_seen": 1623456789.123
                }
            }
        }