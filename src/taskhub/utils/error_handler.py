"""
Standardized error handling utilities for Taskhub MCP server.
"""

import logging
from typing import Any, Dict, Optional
from functools import wraps
import traceback

logger = logging.getLogger(__name__)


class TaskhubError(Exception):
    """Base exception for Taskhub MCP server."""
    
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(TaskhubError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(TaskhubError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: str = "resource", resource_id: Optional[str] = None):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, "NOT_FOUND", details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class DatabaseError(TaskhubError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)
        self.operation = operation


class AuthorizationError(TaskhubError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, action: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)
        self.action = action


def handle_tool_errors(func):
    """Decorator to standardize error handling for tool functions."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TaskhubError as e:
            # Already handled custom error
            logger.error(f"Taskhub error in {func.__name__}: {e.message}", extra={
                "error_code": e.error_code,
                "details": e.details
            })
            return {
                "success": False,
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"An unexpected error occurred: {str(e)}",
                    "details": {"function": func.__name__, "traceback": traceback.format_exc()}
                }
            }
    
    return wrapper


def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> None:
    """Validate that required fields are present in data."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )


def validate_string_length(value: str, min_length: int = 0, max_length: int = 1000, field_name: str = "field") -> None:
    """Validate string length constraints."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field=field_name)
    
    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long",
            field=field_name
        )
    
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters",
            field=field_name
        )


def validate_positive_integer(value: int, field_name: str = "field") -> None:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field_name} must be a positive integer", field=field_name)