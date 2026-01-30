"""
Standardized error response format and exception handlers.

Provides consistent error responses across the API with proper status codes,
error messages, and request tracking.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
import uuid

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Detailed error information for validation errors"""
    field: str
    message: str
    type: str


class ErrorResponse(BaseModel):
    """
    Standardized error response format.

    All API errors return this consistent structure.
    """
    status: str = "error"
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: str
    path: Optional[str] = None


def create_error_response(
    error: str,
    message: str,
    status_code: int = 500,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        error: Error type/category (e.g., "ValidationError", "DatabaseError")
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional list of detailed error information
        request_id: Optional request tracking ID
        path: Optional request path

    Returns:
        JSONResponse with standardized error format
    """
    error_response = ErrorResponse(
        error=error,
        message=message,
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        path=path
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True)
    )


# ===== EXCEPTION HANDLERS =====

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors (422 Unprocessable Entity).

    Transforms Pydantic errors into user-friendly format with field-level details.
    """
    request_id = request.state.request_id if hasattr(request.state, 'request_id') else str(uuid.uuid4())

    # Transform Pydantic errors to ErrorDetail format
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        error_details.append(ErrorDetail(
            field=field or "unknown",
            message=error["msg"],
            type=error["type"]
        ))

    logger.warning(
        f"Validation error [Request ID: {request_id}] "
        f"Path: {request.url.path} - {len(error_details)} validation errors"
    )

    return create_error_response(
        error="ValidationError",
        message=f"Request validation failed. {len(error_details)} field(s) have errors.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=error_details,
        request_id=request_id,
        path=str(request.url.path)
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle SQLAlchemy database errors (500 Internal Server Error).

    Logs full error details but returns sanitized message to client.
    """
    request_id = request.state.request_id if hasattr(request.state, 'request_id') else str(uuid.uuid4())

    # Log full error for debugging
    logger.error(
        f"Database error [Request ID: {request_id}] "
        f"Path: {request.url.path} - {type(exc).__name__}: {str(exc)}\n"
        f"{traceback.format_exc()}"
    )

    # Return sanitized error to client (don't expose internal DB details)
    return create_error_response(
        error="DatabaseError",
        message="A database error occurred. Please try again later or contact support if the problem persists.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        path=str(request.url.path)
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions (500 Internal Server Error).

    Catches any exceptions that weren't handled by specific handlers.
    """
    request_id = request.state.request_id if hasattr(request.state, 'request_id') else str(uuid.uuid4())

    # Log full error for debugging
    logger.error(
        f"Unhandled exception [Request ID: {request_id}] "
        f"Path: {request.url.path} - {type(exc).__name__}: {str(exc)}\n"
        f"{traceback.format_exc()}"
    )

    # Return generic error to client (don't expose internal details)
    return create_error_response(
        error="InternalServerError",
        message="An unexpected error occurred. Please try again later or contact support if the problem persists.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        path=str(request.url.path)
    )


# ===== REQUEST LOGGING MIDDLEWARE =====

async def add_request_id_middleware(request: Request, call_next):
    """
    Middleware to add unique request ID for tracking.

    Also logs request duration and status.
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log incoming request
    logger.info(
        f"[Request ID: {request_id}] "
        f"{request.method} {request.url.path}"
    )

    # Track request duration
    import time
    start_time = time.time()

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"[Request ID: {request_id}] "
            f"{request.method} {request.url.path} -> "
            f"Status: {response.status_code} | Duration: {duration:.3f}s"
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        # Log error
        duration = time.time() - start_time
        logger.error(
            f"[Request ID: {request_id}] "
            f"{request.method} {request.url.path} -> "
            f"ERROR: {type(e).__name__} | Duration: {duration:.3f}s"
        )
        raise


# ===== COMMON ERROR RESPONSES =====

def not_found_response(resource: str, request_id: Optional[str] = None) -> JSONResponse:
    """Create 404 Not Found response"""
    return create_error_response(
        error="NotFound",
        message=f"{resource} not found.",
        status_code=status.HTTP_404_NOT_FOUND,
        request_id=request_id
    )


def unauthorized_response(message: str = "Authentication required.", request_id: Optional[str] = None) -> JSONResponse:
    """Create 401 Unauthorized response"""
    return create_error_response(
        error="Unauthorized",
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
        request_id=request_id
    )


def forbidden_response(message: str = "Access forbidden.", request_id: Optional[str] = None) -> JSONResponse:
    """Create 403 Forbidden response"""
    return create_error_response(
        error="Forbidden",
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
        request_id=request_id
    )


def conflict_response(message: str, request_id: Optional[str] = None) -> JSONResponse:
    """Create 409 Conflict response"""
    return create_error_response(
        error="Conflict",
        message=message,
        status_code=status.HTTP_409_CONFLICT,
        request_id=request_id
    )


def bad_request_response(message: str, request_id: Optional[str] = None) -> JSONResponse:
    """Create 400 Bad Request response"""
    return create_error_response(
        error="BadRequest",
        message=message,
        status_code=status.HTTP_400_BAD_REQUEST,
        request_id=request_id
    )


def too_many_requests_response(message: str = "Too many requests. Please try again later.", request_id: Optional[str] = None) -> JSONResponse:
    """Create 429 Too Many Requests response"""
    return create_error_response(
        error="TooManyRequests",
        message=message,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id
    )


def internal_server_error_response(request_id: Optional[str] = None) -> JSONResponse:
    """Create 500 Internal Server Error response without exposing details"""
    return create_error_response(
        error="InternalServerError",
        message="An unexpected error occurred. Please try again.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id
    )


def safe_exception_handler(
    exception: Exception,
    context: str,
    user_message: str = "An unexpected error occurred. Please try again."
) -> Dict[str, str]:
    """
    Safely handle exceptions without leaking internal details.

    Args:
        exception: The caught exception
        context: Context string for logging (e.g., "creating report")
        user_message: User-friendly message to return

    Returns:
        Dict with error information suitable for HTTPException detail
    """
    # Log the full error for debugging
    logger.error(
        f"[ERROR] Error while {context}: {type(exception).__name__}: {str(exception)}\n"
        f"{traceback.format_exc()}"
    )

    # Return sanitized error message
    return user_message
