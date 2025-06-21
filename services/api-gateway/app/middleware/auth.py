"""
Authentication middleware for the API Gateway.
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from ..core.config import settings

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.middleware.auth")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

class TokenData(BaseModel):
    """Token data model."""
    sub: str
    exp: datetime
    scopes: list[str] = []
    user_id: Optional[str] = None
    is_admin: bool = False

class User(BaseModel):
    """User model."""
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    scopes: list[str] = []

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
        
    Raises:
        ValueError: If data is None or empty
    """
    # Validate input data
    if not data:
        raise ValueError("Token data cannot be None or empty")
    
    # Create a copy to avoid modifying the original
    to_encode = data.copy()
    
    # Ensure required claims are present
    if "sub" not in to_encode:
        raise ValueError("Token data must contain 'sub' claim")
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Get current time for issued at and not before claims
    current_time = datetime.utcnow()
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": current_time,  # Issued at
        "nbf": current_time,  # Not valid before
        "iss": settings.APP_NAME,  # Issuer
    })
    
    # Encode the token
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        # Log the error and re-raise
        logger.error(f"Error encoding JWT token: {str(e)}")
        raise

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate and decode the JWT token to get the current user.
    
    Args:
        token: The JWT token
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: If the token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate the token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": False,  # No audience claim in our tokens
                "require_exp": True,
                "require_iat": True,
                "require_nbf": True
            }
        )
        
        # Extract user information
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
        
        # Check issuer
        issuer = payload.get("iss")
        if issuer != settings.APP_NAME:
            logger.warning(f"Token has invalid issuer: {issuer}")
            raise credentials_exception
        
        # Extract other user information
        user_id = payload.get("user_id")
        is_admin = payload.get("is_admin", False)
        scopes = payload.get("scopes", [])
        
        # Create token data object
        token_data = TokenData(
            sub=username,
            exp=datetime.fromtimestamp(payload.get("exp")),
            user_id=user_id,
            is_admin=is_admin,
            scopes=scopes
        )
    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        raise credentials_exception
    
    # In a real implementation, you would fetch the user from a database
    # For now, we'll create a user object from the token data
    user = User(
        id=token_data.user_id or "unknown",
        username=token_data.sub,
        is_admin=token_data.is_admin,
        scopes=token_data.scopes
    )
    
    return user

async def auth_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to handle authentication for protected routes.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The response from the next handler
    """
    # Skip authentication for public endpoints
    path = request.url.path
    
    # List of paths that don't require authentication
    public_paths = [
        f"{settings.API_V1_STR}/auth/token",
        f"{settings.API_V1_STR}/auth/register",
        f"{settings.API_V1_STR}/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    # Check if the path is public
    is_public = any(path.startswith(public_path) for public_path in public_paths)
    
    # Also check if the path is a health check endpoint
    is_health_check = path.startswith("/health") or path.endswith("/health")
    
    if is_public or is_health_check:
        return await call_next(request)
    
    # Get the authorization header
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        # No token provided, continue without user context
        return await call_next(request)
    
    # Extract the token
    try:
        parts = authorization.split()
        if len(parts) != 2:
            # Malformed authorization header
            return await call_next(request)
            
        scheme, token = parts
        if scheme.lower() != "bearer":
            # Not a bearer token
            return await call_next(request)
    except Exception:
        # Any error in parsing the authorization header
        return await call_next(request)
    
    try:
        # Validate the token and get the user
        try:
            # First, check if the token is well-formed
            if not token or len(token) < 10:  # Arbitrary minimum length for a valid JWT
                logger.warning("Token is too short to be valid")
                # For invalid tokens, we should return a 401 to indicate the client needs to reauthenticate
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token. Please log in again."},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            # Check token format (should be 3 parts separated by dots)
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Token has invalid format (not 3 parts)")
                # For malformed tokens, we should return a 401 to indicate the client needs to reauthenticate
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token format. Please log in again."},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            # Now try to decode it
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": False,  # No audience claim in our tokens
                    "require_exp": True,
                    "require_iat": False,  # For backward compatibility
                    "require_nbf": False   # For backward compatibility
                }
            )
            
            # Check for required claims
            username: str = payload.get("sub")
            if username is None:
                # Token doesn't contain a subject claim
                logger.warning("Token missing 'sub' claim")
                # For tokens missing required claims, return 401
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token missing required claims. Please log in again."},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            # Check issuer if present
            issuer = payload.get("iss")
            if issuer is not None and issuer != settings.APP_NAME:
                logger.warning(f"Token has invalid issuer: {issuer}")
                # For tokens with invalid issuer, return 401
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token has invalid issuer. Please log in again."},
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except JWTError as e:
            # Invalid token, return 401 to indicate the client needs to reauthenticate
            logger.warning(f"JWT validation error: {str(e)}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token signature or claims. Please log in again."},
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            # Any other error in token validation
            logger.warning(f"Unexpected error during token validation: {str(e)}")
            return await call_next(request)
        
        # Extract user information from token
        user_id = payload.get("user_id")
        is_admin = payload.get("is_admin", False)
        scopes = payload.get("scopes", [])
        
        # Check token expiration
        exp = payload.get("exp")
        if exp is None:
            logger.warning(f"Token missing expiration for user {username}")
            # Token without expiration is invalid
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing expiration. Please log in again."},
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # Convert exp to float if it's not already
        try:
            exp_time = float(exp)
        except (ValueError, TypeError):
            logger.warning(f"Invalid expiration format in token for user {username}")
            # For tokens with invalid expiration format, return 401
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has invalid expiration format. Please log in again."},
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # Get current time
        current_time = time.time()
        
        # Check if token is expired
        if exp_time < current_time:
            logger.warning(f"Token expired for user {username}")
            
            # Return a 401 Unauthorized response for expired tokens
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired. Please log in again."},
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # Check if token is about to expire (within 5 minutes)
        # This allows the client to refresh the token before it expires
        if exp_time - current_time < 300:  # 300 seconds = 5 minutes
            # Add a header to indicate the token is about to expire
            # The client can use this to trigger a token refresh
            request.state.token_expiring_soon = True
            logger.debug(f"Token for user {username} is expiring soon")
        
        # Create user object
        user = User(
            id=user_id or "unknown",
            username=username,
            is_admin=is_admin,
            scopes=scopes
        )
        
        # Attach user to request state
        request.state.user = user
        logger.debug(f"Authenticated user: {username}")
    except Exception as e:
        # Any other error in token processing
        logger.error(f"Error processing authentication token: {str(e)}")
        # Continue without user context for any error
        # In a production environment, you might want to return a 401 for certain errors
    
    # Call the next handler to get the response
    response = await call_next(request)
    
    # Add token expiration warning header if needed
    if hasattr(request.state, "token_expiring_soon") and request.state.token_expiring_soon:
        # Add a header to indicate the token is about to expire
        response.headers["X-Token-Expiring-Soon"] = "true"
    
    return response