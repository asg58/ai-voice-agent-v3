"""
Edge AI Model definitions
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ProcessRequest(BaseModel):
    """
    Request model for processing data on the edge.
    
    Attributes:
        input: Input data to process
        parameters: Optional parameters for processing
    """
    input: str = Field(..., description="Input data to process")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional parameters for processing"
    )


class ProcessResponse(BaseModel):
    """
    Response model for processing data on the edge.
    
    Attributes:
        result: Result of the processing
    """
    result: str = Field(..., description="Result of the processing")


class HealthResponse(BaseModel):
    """
    Response model for health check.
    
    Attributes:
        status: Health status of the service
        version: Version of the service
    """
    status: str = Field(..., description="Health status of the service")
    version: str = Field(..., description="Version of the service")