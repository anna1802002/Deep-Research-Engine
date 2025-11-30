# api/middleware.py (updated for streaming responses)
from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import logging
import asyncio
from typing import Dict, Set, Any, Optional, Callable
import hashlib
import json

from api.exceptions import APIError, RateLimitError

logger = logging.getLogger("deep_research.api.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and timing responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID
        request_id = hashlib.md5(f"{time.time()}-{request.client.host}".encode()).hexdigest()[:8]
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response {request_id}: {response.status_code} completed in {process_time:.3f}s"
            )
            
            # Add timing header and request ID
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            
            # Note: Error will be handled by ErrorHandlingMiddleware
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for basic rate limiting."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Set[float]] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Check if client has exceeded rate limit
        if self._is_rate_limited(client_ip):
            raise RateLimitError(
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.period)}
            )
        
        # Process request
        return await call_next(request)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        current_time = time.time()
        
        # Initialize client history if not exists
        if client_ip not in self.clients:
            self.clients[client_ip] = set()
        
        # Remove timestamps older than period
        self.clients[client_ip] = {
            timestamp for timestamp in self.clients[client_ip]
            if current_time - timestamp < self.period
        }
        
        # Check if client has exceeded rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return True
        
        # Add current timestamp to client history
        self.clients[client_ip].add(current_time)
        return False



class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and formatting errors."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", None)
            
            # Format error response based on exception type
            return self._handle_exception(e, request_id)
    
    def _handle_exception(self, exc: Exception, request_id: Optional[str] = None) -> JSONResponse:
        """Handle exception and return appropriate JSON response."""
        if isinstance(exc, APIError):
            # Handle custom API errors
            status_code = exc.status_code
            detail = exc.detail
            headers = exc.headers
        else:
            # Handle unexpected errors
            logger.exception("Unhandled exception")
            status_code = 500
            detail = "Internal server error"
            headers = None
        
        return self._format_error_response(status_code, detail, request_id, headers)
    
    def _format_error_response(
        self, 
        status_code: int, 
        detail: Any, 
        request_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """Format error response with consistent structure."""
        # Create error content
        content = {
            "error": {
                "status_code": status_code,
                "detail": detail
            }
        }
        
        # Add request ID if available
        if request_id:
            content["error"]["request_id"] = request_id
        
        # Create response
        response = JSONResponse(
            status_code=status_code,
            content=content
        )
        
        # Add headers if provided
        if headers:
            for name, value in headers.items():
                response.headers[name] = value
        
        return response

class ValidationErrorMiddleware(BaseHTTPMiddleware):
    """Middleware for formatting validation errors."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except StarletteHTTPException as exc:
            if exc.status_code == 422:
                # Format validation error
                return self._format_validation_error(exc)
            raise
    
    def _format_validation_error(self, exc: StarletteHTTPException) -> JSONResponse:
        """Format validation error into a user-friendly format."""
        # Extract original error detail
        detail = exc.detail
        
        # Convert to string if it's not already
        if not isinstance(detail, str):
            detail = json.dumps(detail)
        
        # Parse validation errors
        try:
            validation_errors = json.loads(detail)
            
            # Format errors
            formatted_errors = []
            for error in validation_errors:
                field = ".".join(str(loc) for loc in error.get("loc", []))
                message = error.get("msg", "")
                
                formatted_errors.append({
                    "field": field,
                    "message": message
                })
            
            # Create response
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "status_code": 422,
                        "detail": "Validation Error",
                        "fields": formatted_errors
                    }
                }
            )
        except (json.JSONDecodeError, AttributeError):
            # If parsing fails, return original error
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "status_code": 422,
                        "detail": detail
                    }
                }
            )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    def __init__(
        self, 
        app, 
        api_keys: Set[str],
        exclude_paths: Set[str] = None,
        key_header: str = "X-API-Key"
    ):
        super().__init__(app)
        self.api_keys = api_keys
        self.exclude_paths = exclude_paths or {"/", "/health", "/docs", "/redoc", "/openapi.json"}
        self.key_header = key_header
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip authentication for excluded paths
        if path in self.exclude_paths:
            return await call_next(request)
        
        # Check for API key
        api_key = request.headers.get(self.key_header)
        if not api_key or api_key not in self.api_keys:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "status_code": 401,
                        "detail": "Invalid or missing API key"
                    }
                }
            )
        
        # Store API key in request state for optional use
        request.state.api_key = api_key
        
        return await call_next(request)