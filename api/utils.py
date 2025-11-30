# api/utils.py
from typing import Any, Dict, Optional, List
from fastapi import HTTPException
from pydantic import ValidationError
from typing import Any, Optional
from api.exceptions import ResourceNotFoundError

from api.exceptions import (
    ResourceNotFoundError, 
    BadRequestError, 
    UnauthorizedError,
    ForbiddenError
)


def handle_validation_error(exc: ValidationError) -> Dict[str, Any]:
    """Format validation error into a user-friendly format."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append({
            "field": field,
            "message": message
        })
    
    return {
        "error": {
            "status_code": 422,
            "detail": "Validation Error",
            "fields": errors
        }
    }


def validate_resource_exists(resource: Optional[Any], resource_type: str, resource_id: str):
    """
    Validate that a resource exists, raising ResourceNotFoundError if not.
    
    Args:
        resource: The resource to check
        resource_type: Type of resource (e.g., "job", "report")
        resource_id: ID of the resource
    
    Raises:
        ResourceNotFoundError: If resource is None
    """
    if resource is None:
        raise ResourceNotFoundError(detail=f"{resource_type} with ID {resource_id} not found")


def validate_authorization(
    is_authorized: bool, 
    detail: str = "You are not authorized to access this resource"
):
    """
    Validate that the user is authorized to access a resource.
    
    Args:
        is_authorized: Whether the user is authorized
        detail: Error message if not authorized
    
    Raises:
        ForbiddenError: If not authorized
    """
    if not is_authorized:
        raise ForbiddenError(detail=detail)