"""
Proxy API endpoints for Service Mesh
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from app.models.mesh import ProxyRequest, ProxyResponse
from app.services.proxy import ProxyService
from loguru import logger

router = APIRouter()

@router.post("/proxy", response_model=None)
async def proxy_request(
    request: ProxyRequest,
    proxy_service: ProxyService = Depends()
):
    """
    Proxy a request to a service.

    Args:
        request: Proxy request

    Returns:
        ProxyResponse: Proxy response
    """
    response = await proxy_service.proxy_request(request)
    return JSONResponse(
        content=response.body,
        status_code=response.status_code,
        headers=response.headers
    )


@router.post("/proxy/{service_name}/{path:path}", response_model=None)
async def proxy_path_request(
    service_name: str,
    path: str,
    request: Request,
    proxy_service: ProxyService = Depends()
):
    """
    Proxy a request to a service using path parameters.

    Args:
        service_name: Service name
        path: Request path
        request: FastAPI request

    Returns:
        JSONResponse: Proxy response
    """
    # Get request body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except Exception:
            body = None

    # Get query parameters
    query_params = {}
    for key, value in request.query_params.items():
        query_params[key] = value

    # Get headers
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ["host", "content-length"]:
            headers[key] = value
    
    # Create proxy request
    proxy_request = ProxyRequest(
        service_name=service_name,
        path=f"/{path}",
        method=request.method,
        headers=headers,
        query_params=query_params,
        body=body
    )

    # Proxy the request
    response = await proxy_service.proxy_request(proxy_request)

    # Return the response
    return JSONResponse(
        content=response.body,
        status_code=response.status_code,
        headers=response.headers
    )