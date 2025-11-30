# api/exceptions.py
from typing import Optional, Dict, Any
from fastapi import HTTPException

class APIError(HTTPException):
    """Base class for API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class RateLimitError(APIError):
    """Error raised when rate limit is exceeded."""
    
    def __init__(
        self,
        detail: Any = "Rate limit exceeded",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=429, detail=detail, headers=headers)


class ResourceNotFoundError(APIError):
    """Error raised when a requested resource is not found."""
    
    def __init__(
        self,
        detail: Any = "Resource not found",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=404, detail=detail, headers=headers)


class UnauthorizedError(APIError):
    """Error raised when access is denied due to invalid credentials."""
    
    def __init__(
        self,
        detail: Any = "Unauthorized",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=401, detail=detail, headers=headers)


class ForbiddenError(APIError):
    """Error raised when access is denied due to insufficient permissions."""
    
    def __init__(
        self,
        detail: Any = "Forbidden",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=403, detail=detail, headers=headers)


class BadRequestError(APIError):
    """Error raised for malformed requests."""
    
    def __init__(
        self,
        detail: Any = "Bad request",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=400, detail=detail, headers=headers)


class ServiceUnavailableError(APIError):
    """Error raised when service is temporarily unavailable."""
    
    def __init__(
        self,
        detail: Any = "Service temporarily unavailable",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=503, detail=detail, headers=headers)