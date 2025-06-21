"""
Data processing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.edge_model import ProcessRequest, ProcessResponse
from app.services.edge_ai_model import EdgeAIModel
from loguru import logger

router = APIRouter()


def get_edge_ai_model() -> EdgeAIModel:
    """
    Dependency to get the Edge AI Model service.
    
    Returns:
        EdgeAIModel: Instance of the Edge AI Model service
    """
    return EdgeAIModel()


@router.post("/process", response_model=ProcessResponse, tags=["Processing"])
async def process_data(
    request: ProcessRequest,
    edge_model: EdgeAIModel = Depends(get_edge_ai_model)
) -> ProcessResponse:
    """
    Process data using AI models on edge devices.
    
    Args:
        request: Processing request with input data and optional parameters
        edge_model: Edge AI Model service instance
        
    Returns:
        ProcessResponse: Result of the processing
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Received processing request for data: {request.input[:50]}...")
        result = edge_model.process_on_edge(request.input, request.parameters)
        return ProcessResponse(result=result)
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")