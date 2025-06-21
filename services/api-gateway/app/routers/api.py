"""
API router for the API Gateway.
"""
import logging
import asyncio
import httpx
import sys
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from ..core.config import settings
from ..services.service_discovery import service_discovery

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.routers.api")

router = APIRouter()

async def get_target_service(path: str) -> Optional[Dict[str, Any]]:
    """
    Get the target service configuration for a path.
    
    Args:
        path: The request path
        
    Returns:
        Optional[Dict[str, Any]]: The service configuration or None if not found
    """
    for service_id, config in settings.SERVICE_ROUTES.items():
        if path.startswith(config["prefix"]):
            try:
                # Get dynamic service info from service discovery if available
                service_info = await service_discovery.get_service(service_id)
                
                if service_info and service_info.get("status") == "healthy":
                    # Validate required fields
                    host = service_info.get("host")
                    port = service_info.get("port")
                    
                    if host and port:
                        # Use discovered service info
                        target = f"http://{host}:{port}"
                        
                        return {
                            "id": service_id,
                            "prefix": config["prefix"],
                            "target": target,
                            "timeout": config.get("timeout", 30),
                            "retry_count": config.get("retry_count", 3)
                        }
                    else:
                        logger.warning(f"Service {service_id} missing host or port in discovery")
                else:
                    if service_info:
                        logger.warning(f"Service {service_id} found but not healthy in discovery")
                    else:
                        logger.warning(f"Service {service_id} not found in discovery")
            except Exception as e:
                logger.error(f"Error getting service info from discovery for {service_id}: {str(e)}")
            
            # Fall back to static configuration if available
            if "target" in config:
                logger.info(f"Using static configuration for {service_id}")
                return {
                    "id": service_id,
                    "prefix": config["prefix"],
                    "target": config["target"],
                    "timeout": config.get("timeout", 30),
                    "retry_count": config.get("retry_count", 3)
                }
            else:
                logger.error(f"No target URL available for service {service_id}")
                return None
    
    return None

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """
    Proxy requests to the appropriate backend service.
    
    Args:
        request: The incoming request
        path: The request path
        
    Returns:
        Response: The response from the backend service
    """
    # Get full path including query parameters
    full_path = request.url.path
    if request.url.query:
        full_path = f"{full_path}?{request.url.query}"
    
    # Get target service
    service = await get_target_service(full_path)
    
    if not service:
        logger.warning(f"No service found for path: {full_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No service found for path: {full_path}"
        )
        
    # Validate service configuration
    if not service.get("target"):
        logger.error(f"Invalid service configuration for {service.get('id', 'unknown')}: missing target URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid service configuration"
        )
    
    # Remove prefix from path
    target_path = full_path[len(service["prefix"]):]
    if not target_path.startswith("/"):
        target_path = f"/{target_path}"
    
    # Build target URL
    target_url = f"{service['target']}{target_path}"
    
    # Get request body
    body = await request.body()
    
    # Forward headers, excluding host and other potentially sensitive headers
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Define headers that should not be forwarded to non-auth services
    sensitive_headers = ["authorization", "cookie", "set-cookie"]
    
    # Define headers that should be forwarded to all services
    always_forward_headers = ["accept", "content-type", "user-agent", "accept-encoding"]
    
    # Process headers based on service
    if service["id"] == "auth":
        # For auth service, forward all headers including sensitive ones
        pass
    else:
        # For non-auth services, remove sensitive headers
        for header in sensitive_headers:
            headers.pop(header.lower(), None)
    
    # Add correlation ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Correlation-ID"] = request.state.request_id
    
    # Add user info if available
    if hasattr(request.state, "user"):
        # Only add user info for authenticated users
        if request.state.user and request.state.user.id:
            headers["X-User-ID"] = request.state.user.id
            headers["X-Username"] = request.state.user.username
            
            # Add user roles/scopes if available
            if hasattr(request.state.user, "scopes") and request.state.user.scopes:
                headers["X-User-Scopes"] = ",".join(request.state.user.scopes)
                
            # Add admin flag if available
            if hasattr(request.state.user, "is_admin"):
                headers["X-User-Is-Admin"] = str(request.state.user.is_admin).lower()
    
    # Create HTTP client with appropriate timeout
    timeout = httpx.Timeout(service["timeout"])
    retry_count = service.get("retry_count", 3)
    retry_delay = 0.5  # Initial delay in seconds
    
    # Initialize variables for retry logic
    response = None
    last_error = None
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Implement retry logic
            for attempt in range(retry_count + 1):  # +1 for the initial attempt
                try:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt}/{retry_count} for {target_url}")
                        # Exponential backoff
                        await asyncio.sleep(retry_delay * (2 ** (attempt - 1)))
                    
                    # Forward the request to the target service
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        content=body,
                        follow_redirects=True
                    )
                    
                    # If we get a 5xx response, we might want to retry
                    if response.status_code >= 500 and attempt < retry_count:
                        logger.warning(f"Received {response.status_code} from {target_url}, will retry")
                        # Ensure we don't leak the response object
                        await response.aclose()
                        response = None
                        continue
                    
                    # Otherwise, we have a response to work with
                    break
                    
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    last_error = e
                    # Make sure response is closed if it exists
                    if response is not None:
                        try:
                            await response.aclose()
                        except Exception:
                            pass
                        response = None
                        
                    if attempt < retry_count:
                        logger.warning(f"Request to {target_url} failed: {str(e)}, will retry")
                        continue
                    # Don't raise here, let the code below handle it
                    logger.error(f"Request to {target_url} failed after {attempt+1} attempts: {str(e)}")
                    # We'll handle this in the code below
            
            # If we still don't have a response after all retries, raise the last error
            if response is None:
                if last_error:
                    logger.error(f"All retry attempts failed for {target_url}: {str(last_error)}")
                    if isinstance(last_error, httpx.TimeoutException):
                        raise HTTPException(
                            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                            detail=f"Timeout while connecting to service: {service['id']}"
                        )
                    elif isinstance(last_error, httpx.ConnectError):
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Service unavailable: {service['id']}"
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error connecting to service: {service['id']}"
                        )
                logger.error(f"Failed to get response after retries for {target_url}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get response from service: {service['id']}"
                )
            
            # Check if the response is a streaming response
            # Look for chunked transfer encoding or content-type indicating a stream
            is_stream = False
            
            # Check transfer-encoding header
            if "transfer-encoding" in response.headers:
                is_stream = response.headers["transfer-encoding"].lower() == "chunked"
            
            # Also check content-type for event streams
            if not is_stream and "content-type" in response.headers:
                content_type = response.headers["content-type"].lower()
                is_stream = (
                    "event-stream" in content_type or 
                    "octet-stream" in content_type
                )
            
            if is_stream:
                # Handle streaming response
                async def stream_response():
                    # Flag to track if we need to close the response
                    response_needs_closing = True
                    
                    try:
                        # Use a timeout to prevent hanging based on Python version
                        if sys.version_info >= (3, 11):
                            from asyncio import timeout
                            async with timeout(service["timeout"]):
                                async for chunk in response.aiter_bytes():
                                    if chunk:  # Only yield non-empty chunks
                                        yield chunk
                        else:
                            # For Python 3.10 and earlier, we need a different approach
                            # Create a task for streaming and use wait_for
                            from asyncio import wait_for, create_task, CancelledError
                            
                            # Define a helper function to stream chunks
                            async def stream_chunks():
                                async for chunk in response.aiter_bytes():
                                    if chunk:  # Only yield non-empty chunks
                                        yield chunk
                            
                            # Create an async generator that yields chunks with timeout
                            stream_gen = stream_chunks()
                            try:
                                while True:
                                    # Get next chunk with timeout
                                    chunk = await wait_for(
                                        stream_gen.__anext__(), 
                                        timeout=service["timeout"]
                                    )
                                    yield chunk
                            except StopAsyncIteration:
                                # End of stream
                                pass
                        
                        # If we get here, the stream completed successfully
                        response_needs_closing = False
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout while streaming response from {service['id']}")
                        # Yield empty bytes to end the stream gracefully
                        yield b""
                    except Exception as e:
                        logger.error(f"Error streaming response from {service['id']}: {str(e)}")
                        # Yield empty bytes to end the stream gracefully
                        yield b""
                    finally:
                        # Close the response if needed
                        if response_needs_closing and response is not None:
                            try:
                                await response.aclose()
                            except Exception as e:
                                logger.error(f"Error closing response after streaming: {str(e)}")
                                pass
                
                # Create streaming response with the same headers
                headers = dict(response.headers)
                # Remove content-length if present as it's not applicable for streaming
                headers.pop("content-length", None)
                
                # Add custom header to indicate this is a proxied stream
                headers["X-Proxied-Stream"] = "true"
                
                return StreamingResponse(
                    stream_response(),
                    status_code=response.status_code,
                    headers=headers,
                    media_type=response.headers.get("content-type")
                )
            else:
                try:
                    # Handle regular response
                    # Get content and headers before closing the response
                    content = response.content
                    status_code = response.status_code
                    headers = dict(response.headers)
                    media_type = response.headers.get("content-type")
                    
                    # Close the response to free up resources
                    await response.aclose()
                    
                    return Response(
                        content=content,
                        status_code=status_code,
                        headers=headers,
                        media_type=media_type
                    )
                except Exception as e:
                    # Ensure response is closed even if there's an error
                    try:
                        await response.aclose()
                    except Exception:
                        pass
                    
                    # Re-raise the exception
                    logger.error(f"Error processing response from {service['id']}: {str(e)}")
                    raise
    except httpx.TimeoutException:
        # Ensure response is closed if it exists
        if response is not None:
            try:
                await response.aclose()
            except Exception:
                pass
        
        logger.error(f"Timeout while connecting to {service['id']} at {target_url}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout while connecting to service: {service['id']}"
        )
    except httpx.ConnectError:
        # Ensure response is closed if it exists
        if response is not None:
            try:
                await response.aclose()
            except Exception:
                pass
        
        logger.error(f"Connection error while connecting to {service['id']} at {target_url}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {service['id']}"
        )
    except Exception as e:
        # Ensure response is closed if it exists
        if response is not None:
            try:
                await response.aclose()
            except Exception:
                pass
        
        logger.error(f"Error while proxying request to {service['id']} at {target_url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )