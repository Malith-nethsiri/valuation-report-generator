"""
FastAPI application factory.

Registers middleware, exception handlers, startup/shutdown events,
and mounts all domain routers. No route handlers are defined here.
"""
import asyncio
import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv

# Load environment variables before anything else
_env_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_env_dir, '.env.local'), override=True)
load_dotenv(os.path.join(_env_dir, '.env'))

# Sentry (production only)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENV = os.getenv("ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

if SENTRY_DSN and IS_PRODUCTION:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=ENV,
        send_default_pii=False,
        attach_stacktrace=True,
    )
    logging.info("Sentry initialized for production")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Local app imports (after env load)
from . import models
from .database import SessionLocal, engine
from .middleware.csrf_protection import CSRFMiddleware
from .middleware.rate_limiting import RateLimitMiddleware, configure_rate_limits, cleanup_task
from .middleware.security_headers import SecurityHeadersMiddleware
from .services.redis_client import close_redis_connection, get_redis_client
from .utils.error_responses import (
    add_request_id_middleware,
    generic_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from .routers import (
    admin_router,
    auth_router,
    password_router,
    oauth_router,
    autocomplete_router,
    health_router,
    jobs_router,
    locality_router,
    maps_router,
    narratives_router,
    ocr_router,
    properties_router,
    reports_router,
    users_router,
    vehicles_router,
)

# ===== CORS CONFIGURATION =====

cors_origins_env = os.getenv("CORS_ORIGINS")

if IS_PRODUCTION and not cors_origins_env:
    raise RuntimeError("CORS_ORIGINS must be set in production. Set ENV=development for local development.")

if cors_origins_env:
    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    origins = ["http://localhost:5173", "http://localhost:5174"]
    logger.warning("Using development CORS origins. Set CORS_ORIGINS for production.")

if IS_PRODUCTION and any("localhost" in origin for origin in origins):
    raise RuntimeError(
        "SECURITY ERROR: localhost origins detected in production CORS config! "
        "Remove localhost from CORS_ORIGINS or set ENV=development for local development."
    )

logger.info(f"CORS configured for origins: {origins}")

# ===== APP FACTORY =====

app = FastAPI(
    title="Data Collection & DOCX Generator API",
    description="API for collecting user data and generating DOCX documents",
    version="1.0.0",
)

# Middleware stack (order matters — last added = outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware, is_production=IS_PRODUCTION)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "X-CSRF-Token"],
    expose_headers=["Content-Disposition"],
)

# Request ID logging middleware
app.middleware("http")(add_request_id_middleware)

# Global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ===== ROUTERS =====
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(password_router)
app.include_router(oauth_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(reports_router)
app.include_router(jobs_router)
app.include_router(properties_router)
app.include_router(vehicles_router)
app.include_router(ocr_router)
app.include_router(autocomplete_router)
app.include_router(maps_router)
app.include_router(locality_router)
app.include_router(narratives_router)


# ===== STARTUP / SHUTDOWN =====

async def _cleanup_token_blacklist():
    """Background task: remove expired token blacklist entries every hour."""
    while True:
        try:
            await asyncio.sleep(3600)
            db = SessionLocal()
            try:
                deleted_count = db.query(models.TokenBlacklist).filter(
                    models.TokenBlacklist.expires_at < datetime.now(timezone.utc)
                ).delete()
                db.commit()
                if deleted_count > 0:
                    logger.info(f"[BLACKLIST_CLEANUP] Removed {deleted_count} expired token entries")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[BLACKLIST_CLEANUP] Error during cleanup: {e}")


@app.on_event("startup")
async def startup_event():
    """Configure rate limits, initialize Redis, and start background tasks."""
    logger.info("Application starting up...")

    # Verify database connectivity at startup (not at import time, to allow test isolation)
    try:
        from sqlalchemy import text as sa_text
        with engine.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
        logger.info("✓ Database connection established successfully")
    except Exception as e:
        logger.critical(f"✗ Database connection failed: {e}")
        raise RuntimeError(f"Cannot connect to database. Please check DATABASE_URL configuration: {e}")

    if os.getenv("AUTO_MIGRATE", "false").lower() == "true":
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command as alembic_command

            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

            if os.path.exists(alembic_ini_path):
                alembic_cfg = AlembicConfig(alembic_ini_path)
                alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
                alembic_command.upgrade(alembic_cfg, "head")
                logger.info("Database migrations completed successfully")
            else:
                logger.warning(f"alembic.ini not found at {alembic_ini_path}, skipping auto-migration")
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            if IS_PRODUCTION:
                raise RuntimeError(f"Database migration failed in production: {e}")
            else:
                logger.warning("Continuing without migrations (non-production mode)")

    configure_rate_limits()

    try:
        redis_client = await get_redis_client()
        if redis_client:
            logger.info("Redis connection initialized successfully")
        else:
            logger.warning("Redis not available - caching and job queue features disabled")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")

    asyncio.create_task(cleanup_task())
    asyncio.create_task(_cleanup_token_blacklist())

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown: close Redis and DB connections."""
    logger.info("Application shutting down gracefully...")

    try:
        await close_redis_connection()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

    try:
        pending = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if pending:
            logger.info(f"Waiting for {len(pending)} pending tasks to complete...")
            await asyncio.wait(pending, timeout=5.0)
    except Exception as e:
        logger.error(f"Error waiting for pending tasks: {e}")

    logger.info("Application shutdown complete")
