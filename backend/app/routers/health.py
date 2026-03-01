"""
Health check router.

Provides endpoints for API health status, CSRF token, and detailed dependency checks.
"""
from fastapi import APIRouter, Depends, Request
from datetime import datetime, timezone
import os
import logging

from .. import schemas, models
from ..auth import require_admin
from ..middleware.csrf_protection import get_csrf_token_endpoint
from ..services.redis_client import redis_health_check

router = APIRouter()
logger = logging.getLogger(__name__)

ENV = os.getenv("ENV", "development").lower()


@router.get("/", response_model=schemas.HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "success",
        "message": "Data Collection & DOCX Generator API is running"
    }


@router.get("/api/health", response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "success",
        "message": "API is healthy and running"
    }


@router.get("/api/csrf-token")
async def csrf_token(request: Request):
    """
    Get CSRF token.

    Frontend should call this endpoint on initial load to ensure
    a CSRF token cookie is set. The token should then be included
    as X-CSRF-Token header on all state-changing requests.
    """
    return get_csrf_token_endpoint(request)


@router.get("/api/health/detailed")
async def detailed_health_check(
    _current_user: models.User = Depends(require_admin)
):
    """
    Detailed health check that validates all critical dependencies
    Returns status of database, Redis, API keys, and critical services
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }

    # Check database connection
    try:
        from ..database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "unhealthy"

    # Check Redis connection
    try:
        redis_status = await redis_health_check()
        health_status["checks"]["redis"] = redis_status
        if redis_status["status"] == "unhealthy":
            health_status["status"] = "degraded"  # Redis is optional, so degraded not unhealthy
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"

    # Check Anthropic API key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and len(anthropic_key) > 20:
        health_status["checks"]["anthropic_api"] = {"status": "configured", "message": "API key present"}
    else:
        health_status["checks"]["anthropic_api"] = {"status": "missing", "message": "API key not configured"}
        health_status["status"] = "degraded"

    # Check Google Vision API key
    vision_key = os.getenv("GOOGLE_VISION_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    if vision_key and len(vision_key) > 20:
        health_status["checks"]["google_vision_api"] = {"status": "configured", "message": "API key present"}
    else:
        health_status["checks"]["google_vision_api"] = {"status": "missing", "message": "API key not configured"}
        health_status["status"] = "degraded"

    # Check if OCR service can be imported
    try:
        from ..services.ocr import process_multiple_documents
        from ..services.ai import parse_with_claude
        health_status["checks"]["ocr_service"] = {"status": "healthy", "message": "Modules loaded"}
    except Exception as e:
        health_status["checks"]["ocr_service"] = {"status": "unhealthy", "message": f"Import failed: {str(e)}"}
        health_status["status"] = "unhealthy"

    # Check Sentry configuration (production only)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if ENV == "production":
        if sentry_dsn:
            health_status["checks"]["sentry"] = {"status": "configured", "message": "Error tracking enabled"}
        else:
            health_status["checks"]["sentry"] = {"status": "missing", "message": "Not configured (recommended for production)"}

    return health_status
