"""
CSRF Protection Middleware using Double-Submit Cookie Pattern.

This middleware protects against Cross-Site Request Forgery attacks by:
1. Setting a CSRF token cookie on all responses
2. Validating that state-changing requests (POST, PUT, DELETE, PATCH) include
   a matching X-CSRF-Token header

For SPA applications, the frontend should:
1. Read the csrf_token cookie
2. Include it as X-CSRF-Token header in all state-changing requests
"""

import secrets
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Configuration
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_MAX_AGE = 3600 * 8  # 8 hours to match JWT lifetime

# Methods that require CSRF protection
UNSAFE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Paths exempt from CSRF (public endpoints, auth endpoints that don't change state)
CSRF_EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/forgot-password",
    "/api/health",
    "/api/health/detailed",
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def is_path_exempt(path: str) -> bool:
    """Check if path is exempt from CSRF protection."""
    # Exact match
    if path in CSRF_EXEMPT_PATHS:
        return True
    # Prefix matches for documentation paths
    if path.startswith("/docs") or path.startswith("/redoc"):
        return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware.

    Implements the Double-Submit Cookie pattern:
    - Sets a csrf_token cookie on all responses
    - Validates that POST/PUT/DELETE/PATCH requests include matching X-CSRF-Token header
    """

    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get existing CSRF token from cookie
        existing_token = request.cookies.get(CSRF_COOKIE_NAME)

        # For unsafe methods, validate CSRF token
        if request.method in UNSAFE_METHODS:
            if not is_path_exempt(request.url.path):
                # Get token from header
                header_token = request.headers.get(CSRF_HEADER_NAME)

                # Validate tokens match
                if not existing_token or not header_token:
                    logger.warning(
                        f"CSRF validation failed - missing token. "
                        f"Path: {request.url.path}, Method: {request.method}, "
                        f"Cookie present: {bool(existing_token)}, Header present: {bool(header_token)}"
                    )
                    return Response(
                        content='{"detail": "CSRF token missing"}',
                        status_code=status.HTTP_403_FORBIDDEN,
                        media_type="application/json"
                    )

                if not secrets.compare_digest(existing_token, header_token):
                    logger.warning(
                        f"CSRF validation failed - token mismatch. "
                        f"Path: {request.url.path}, Method: {request.method}"
                    )
                    return Response(
                        content='{"detail": "CSRF token invalid"}',
                        status_code=status.HTTP_403_FORBIDDEN,
                        media_type="application/json"
                    )

        # Process the request
        response: Response = await call_next(request)

        # Set or refresh CSRF token cookie
        if not existing_token:
            new_token = generate_csrf_token()
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=new_token,
                max_age=CSRF_COOKIE_MAX_AGE,
                httponly=False,  # Must be readable by JavaScript
                secure=self.is_production,  # HTTPS only in production
                samesite="strict"  # Prevent cross-site cookie sending
            )

        return response


def get_csrf_token_endpoint(request: Request) -> dict:
    """
    Endpoint to get CSRF token.

    Frontend can call this to ensure a CSRF token cookie is set.
    Returns the token value for convenience (matches cookie).
    """
    existing_token = request.cookies.get(CSRF_COOKIE_NAME)
    if existing_token:
        return {"csrf_token": existing_token}

    # Generate new token - will be set by middleware
    new_token = generate_csrf_token()
    return {"csrf_token": new_token, "note": "Token will be set in cookie"}
