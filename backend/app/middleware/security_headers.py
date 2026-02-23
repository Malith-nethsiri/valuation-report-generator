"""
Security headers middleware.

Adds security headers (CSP, X-Frame-Options, HSTS, etc.) to all responses.
"""
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Content Security Policy
        # Allow Google Maps APIs, fonts, and Anthropic API
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://maps.googleapis.com https://maps.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com blob:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://maps.googleapis.com https://api.anthropic.com https://*.sentry.io; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )

        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"

        # HSTS header (only in production over HTTPS)
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
