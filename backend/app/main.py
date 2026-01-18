from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os
import logging
import asyncio
from datetime import timedelta, datetime
from typing import Optional, List

# Load environment variables FIRST (before Sentry init)
load_dotenv()

# Initialize Sentry before other imports (production only)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENV = os.getenv("ENV", "development").lower()

if SENTRY_DSN and ENV == "production":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,
        environment=ENV,
        send_default_pii=False,  # Don't send PII by default
        attach_stacktrace=True,
    )
    logging.info("Sentry initialized for production")

from . import models, schemas, crud
from .database import engine, get_db
from .docx_generator import generate_user_data_docx, get_filename_for_user
from .autocomplete import get_all_autocomplete_data, search_autocomplete
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .services.ocr_service import process_uploaded_document, process_multiple_documents
from .services.redis_client import get_redis_client, close_redis_connection, redis_health_check
from .utils.extent_calculator import calculate_extent_data
from .utils.error_responses import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
    add_request_id_middleware
)
from .middleware.rate_limiting import (
    RateLimitMiddleware,
    configure_rate_limits,
    cleanup_task
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== FILE UPLOAD SECURITY CONSTANTS =====
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_FILES_PER_UPLOAD = 10

ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/jpg',
    'application/pdf'
}

ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.pdf'
}

# Mapping of magic number signatures to MIME types
MAGIC_NUMBER_SIGNATURES = {
    b'\xFF\xD8\xFF': 'image/jpeg',  # JPEG
    b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
    b'RIFF': 'image/webp',  # WEBP (needs additional check)
    b'%PDF': 'application/pdf',  # PDF
}


def verify_file_type_by_magic_number(file_content: bytes) -> Optional[str]:
    """
    Verify file type using magic number (file signature).

    Returns MIME type if valid, None otherwise.
    """
    # Check magic number signatures
    for signature, mime_type in MAGIC_NUMBER_SIGNATURES.items():
        if file_content.startswith(signature):
            # Special handling for WEBP (check for WEBP after RIFF)
            if signature == b'RIFF' and len(file_content) >= 12:
                if file_content[8:12] == b'WEBP':
                    return mime_type
                else:
                    continue  # Not a WEBP file
            return mime_type

    return None


async def validate_upload_file(file: UploadFile) -> None:
    """
    Validate uploaded file for security.

    Checks:
    - File size (≤ 10MB)
    - File extension is allowed
    - Magic number matches extension (prevents file type spoofing)

    Raises HTTPException if validation fails.
    """
    import os

    # Read file content for validation
    file_content = await file.read()
    file_size = len(file_content)

    # Reset file pointer for later use
    await file.seek(0)

    # 1. Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{file.filename}' is too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB, got {file_size / (1024*1024):.2f}MB"
        )

    # 2. Check file extension
    filename_lower = file.filename.lower() if file.filename else ""
    file_ext = os.path.splitext(filename_lower)[1]

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' has unsupported extension '{file_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 3. Verify magic number (actual file type)
    detected_mime = verify_file_type_by_magic_number(file_content)

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' appears to be a different type than its extension suggests. File validation failed for security reasons."
        )

    # 4. Cross-check: ensure declared content type matches detected type
    if file.content_type and detected_mime:
        # Normalize content types (some browsers send image/jpg instead of image/jpeg)
        declared_type = file.content_type.lower()
        if declared_type == 'image/jpg':
            declared_type = 'image/jpeg'

        if declared_type != detected_mime and not (declared_type.startswith('image/') and detected_mime.startswith('image/')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' type mismatch. Declared: {file.content_type}, Detected: {detected_mime}"
            )


# Create database tables
models.Base.metadata.create_all(bind=engine)

# Environment mode
ENV = os.getenv("ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

# Initialize FastAPI app
app = FastAPI(
    title="Data Collection & DOCX Generator API",
    description="API for collecting user data and generating DOCX documents",
    version="1.0.0",
    # Disable docs in production for security (uncomment if needed)
    # docs_url=None if IS_PRODUCTION else "/docs",
    # redoc_url=None if IS_PRODUCTION else "/redoc",
)

# Configure CORS with production validation
cors_origins_env = os.getenv("CORS_ORIGINS")

if IS_PRODUCTION and not cors_origins_env:
    logger.critical("CORS_ORIGINS environment variable is required in production!")
    raise RuntimeError("CORS_ORIGINS must be set in production. Set ENV=development for local development.")

if cors_origins_env:
    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Development defaults
    origins = ["http://localhost:5173", "http://localhost:5174"]
    logger.warning("Using development CORS origins. Set CORS_ORIGINS for production.")

# Validate no localhost in production
if IS_PRODUCTION and any("localhost" in origin for origin in origins):
    logger.warning("WARNING: localhost origins detected in production CORS config!")

logger.info(f"CORS configured for origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)


# ===== SECURITY HEADERS MIDDLEWARE =====
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: StarletteRequest, call_next):
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

        # Set security headers
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

app.add_middleware(SecurityHeadersMiddleware)


# Add request logging middleware
app.middleware("http")(add_request_id_middleware)

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ===== STARTUP EVENT =====
@app.on_event("startup")
async def startup_event():
    """Configure rate limits, initialize Redis, and start background tasks on application startup"""
    logger.info("Application starting up...")

    # Configure rate limits for all endpoints
    configure_rate_limits()

    # Initialize Redis connection
    try:
        redis_client = await get_redis_client()
        if redis_client:
            logger.info("Redis connection initialized successfully")
        else:
            logger.warning("Redis not available - caching and job queue features disabled")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")

    # Start background task for periodic bucket cleanup
    asyncio.create_task(cleanup_task())

    logger.info("Application startup complete")


# ===== SHUTDOWN EVENT =====
@app.on_event("shutdown")
async def shutdown_event():
    """
    Graceful shutdown handler.

    This is called when the application receives SIGTERM/SIGINT signals,
    allowing for clean resource cleanup before the process exits.
    """
    logger.info("Application shutting down gracefully...")

    # Close Redis connection
    try:
        await close_redis_connection()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

    try:
        # Close database connections
        from .database import engine
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

    # Allow pending async tasks to complete (with timeout)
    try:
        pending = asyncio.all_tasks()
        # Filter out the current task
        pending = [t for t in pending if t != asyncio.current_task()]
        if pending:
            logger.info(f"Waiting for {len(pending)} pending tasks to complete...")
            # Wait up to 5 seconds for tasks to complete
            await asyncio.wait(pending, timeout=5.0)
    except Exception as e:
        logger.error(f"Error waiting for pending tasks: {e}")

    logger.info("Application shutdown complete")


@app.get("/", response_model=schemas.HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "success",
        "message": "Data Collection & DOCX Generator API is running"
    }

@app.get("/api/health", response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "success",
        "message": "API is healthy and running"
    }

@app.get("/api/health/detailed")
async def detailed_health_check():
    """
    Detailed health check that validates all critical dependencies
    Returns status of database, Redis, API keys, and critical services
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Check database connection
    try:
        from .database import SessionLocal
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
        from .services.ocr_service import process_multiple_documents
        from .services.ai_parser import parse_with_claude
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

# Authentication Endpoints
@app.post("/api/auth/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    - **email**: User's email address (must be unique)
    - **password**: Password (minimum 6 characters)
    - **full_name**: User's full name
    - **phone**: Phone number (optional)
    """
    # Check if user already exists
    existing_user = crud.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Create new user
        db_user = crud.create_user(db, user_data)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": db_user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

from .services.login_limiter import LoginLimiter
from fastapi import Request

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
async def login_user(
    user_credentials: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login user and return access token

    - **email**: User's email address
    - **password**: User's password
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    is_allowed, remaining_attempts = await LoginLimiter.check_rate_limit(
        client_ip, user_credentials.email
    )

    if not is_allowed:
        lockout_remaining = await LoginLimiter.get_lockout_remaining(
            client_ip, user_credentials.email
        )
        lockout_minutes = (lockout_remaining or 900) // 60

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please try again in {lockout_minutes} minutes.",
            headers={"Retry-After": str(lockout_remaining or 900)}
        )

    # Authenticate user
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        # Record failed attempt
        is_locked, remaining = await LoginLimiter.record_failed_attempt(
            client_ip, user_credentials.email
        )

        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Your account has been temporarily locked for 15 minutes.",
                headers={"Retry-After": "900"}
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password. {remaining} attempts remaining.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Clear failed attempts on successful login
    await LoginLimiter.clear_attempts(client_ip, user_credentials.email)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user


# ===== PASSWORD RESET ENDPOINTS =====
from .services.email_service import EmailService
from .auth import get_password_hash
import secrets

@app.post("/api/auth/forgot-password", response_model=schemas.PasswordResetResponse)
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.

    Sends a reset link to the provided email if it exists in the system.
    Always returns success to prevent email enumeration.
    """
    # Find user by email
    user = crud.get_user_by_email(db, email=request.email)

    if user:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)

        # Set token expiration (1 hour from now)
        from datetime import timezone
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        # Save token to user
        user.password_reset_token = reset_token
        user.password_reset_expires = expiration
        db.commit()

        # Send reset email
        email_sent = EmailService.send_password_reset_email(user.email, reset_token)

        if not email_sent:
            logger.warning(f"Failed to send password reset email to {user.email}")
    else:
        logger.info(f"Password reset requested for non-existent email: {request.email}")

    # Always return success to prevent email enumeration
    return schemas.PasswordResetResponse(
        success=True,
        message="If an account with that email exists, a password reset link has been sent."
    )


@app.post("/api/auth/reset-password", response_model=schemas.PasswordResetResponse)
async def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using the token from the email.
    """
    # Find user with this reset token
    user = db.query(models.User).filter(
        models.User.password_reset_token == request.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token is expired
    from datetime import timezone
    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(timezone.utc):
        # Clear the expired token
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    # Hash new password and update user
    user.password_hash = get_password_hash(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    logger.info(f"Password reset successful for user: {user.email}")

    return schemas.PasswordResetResponse(
        success=True,
        message="Your password has been reset successfully. You can now log in with your new password."
    )


# ===== ADMIN ENDPOINTS (Protected) =====
from .auth import require_admin

@app.get("/api/admin/users", response_model=List[schemas.UserResponse])
async def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only).

    - **skip**: Number of users to skip (pagination)
    - **limit**: Maximum number of users to return
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@app.get("/api/admin/users/{user_id}", response_model=schemas.UserResponse)
async def admin_get_user(
    user_id: int,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (Admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


class RoleUpdate(schemas.BaseModel):
    role: str


@app.patch("/api/admin/users/{user_id}/role", response_model=schemas.UserResponse)
async def admin_update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's role (Admin only).

    - **user_id**: ID of the user to update
    - **role**: New role ('user' or 'admin')
    """
    # Validate role
    if role_update.role not in ['user', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )

    # Find user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Prevent self-demotion
    if user.id == admin_user.id and role_update.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin"
        )

    # Update role
    user.role = role_update.role
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {admin_user.email} changed user {user.email} role to {role_update.role}")
    return user


# User Profile Endpoints
@app.put("/api/profile", response_model=schemas.UserResponse)
async def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    updated_user = crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

# Bank Account Management Endpoints
@app.get("/api/users/me/bank-accounts", response_model=List[schemas.BankAccount])
async def get_my_bank_accounts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bank accounts for the current user"""
    accounts = crud.get_bank_accounts(db, current_user.id)
    return accounts or []

@app.post("/api/users/me/bank-accounts", response_model=schemas.BankAccount, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account: schemas.BankAccountCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new bank account"""
    new_account = crud.add_bank_account(db, current_user.id, account)
    if not new_account:
        raise HTTPException(status_code=500, detail="Failed to create bank account")
    return new_account

@app.patch("/api/users/me/bank-accounts/{account_id}", response_model=schemas.BankAccount)
async def update_bank_account(
    account_id: str,
    account_update: schemas.BankAccountUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing bank account"""
    updated_account = crud.update_bank_account(db, current_user.id, account_id, account_update)
    if not updated_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
    return updated_account

@app.delete("/api/users/me/bank-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_account(
    account_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bank account"""
    success = crud.delete_bank_account(db, current_user.id, account_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
    return None

# Letterhead Template Endpoints
@app.get("/api/letterhead-templates", response_model=schemas.TemplateListResponse)
async def get_letterhead_templates():
    """Get all available letterhead templates"""
    from .letterhead_templates import get_all_templates
    templates = get_all_templates()
    return {"templates": [t.to_dict() for t in templates]}

# Report Endpoints (Protected)
@app.post("/api/reports", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: schemas.ReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new report for the authenticated user"""
    logger.info(f"[CREATE REPORT] Received data from frontend:")
    logger.debug(f"  property_village: {report_data.property_village}")
    logger.debug(f"  property_district: {report_data.property_district}")
    logger.debug(f"  grama_niladari_division: {report_data.grama_niladari_division}")
    logger.debug(f"  property_divisional_secretariat: {report_data.property_divisional_secretariat}")
    logger.debug(f"  korale: {report_data.korale}")
    logger.debug(f"  pradeshiya_sabha: {report_data.pradeshiya_sabha}")
    logger.debug(f"  access_directions_text: {report_data.access_directions_text}")
    logger.debug(f"  location_map_image_data: {report_data.location_map_image_data}")
    logger.debug(f"  property_latitude: {report_data.property_latitude}")
    logger.debug(f"  property_longitude: {report_data.property_longitude}")
    # Property Description fields
    logger.debug(f"  === PROPERTY DESCRIPTION FIELDS ===")
    logger.debug(f"  land_shape: {report_data.land_shape}")
    logger.debug(f"  land_type: {report_data.land_type}")
    logger.debug(f"  soil_type: {report_data.soil_type}")
    logger.debug(f"  flood_risk: {report_data.flood_risk}")
    logger.debug(f"  land_description_text: {report_data.land_description_text}")
    logger.debug(f"  buildings: {report_data.buildings}")
    logger.debug(f"  occupier_name: {report_data.occupier_name}")
    logger.debug(f"  property_photos count: {len(report_data.property_photos) if report_data.property_photos else 0}")

    try:
        db_report = crud.create_report(db, report_data, current_user.id)
        logger.info(f"[CREATE REPORT] Report created with ID: {db_report.id}")
        return db_report
    except Exception as e:
        logger.error(f"[CREATE REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating report: {str(e)}"
        )

@app.get("/api/reports", response_model=list[schemas.ReportResponse])
async def get_user_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for the authenticated user (paginated)"""
    return crud.get_user_reports(db, current_user.id, skip=skip, limit=limit)

@app.get("/api/reports/{report_id}")
async def get_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific report by ID (must belong to authenticated user)"""
    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    # For multi-property reports, include properties in response
    if db_report.is_multi_property:
        # Get all associated properties ordered by property_order
        properties = db_report.properties

        # Convert to response format
        response_data = {
            **{key: getattr(db_report, key) for key in db_report.__dict__ if not key.startswith('_')},
            'properties': properties
        }
        return response_data

    return db_report

@app.put("/api/reports/{report_id}")
async def update_report(
    report_id: int,
    request_body: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a report (must belong to authenticated user)"""
    logger.info(f"[UPDATE_REPORT] Received PUT request for report {report_id}")
    logger.info(f"[UPDATE_REPORT] Request body keys: {list(request_body.keys())}")

    # Extract properties from request if present
    properties_data = request_body.pop('properties', None)
    property_metadata = request_body.pop('property_metadata', None)

    logger.info(f"[UPDATE_REPORT] Properties data present: {properties_data is not None}")
    if properties_data:
        logger.info(f"[UPDATE_REPORT] Properties count: {len(properties_data)}")

    # If properties are being sent, ensure report is marked as multi-property
    if properties_data:
        request_body['is_multi_property'] = True
        request_body['property_count'] = len(properties_data)
        logger.info(f"[UPDATE_REPORT] Setting is_multi_property=True because properties provided")

    # Update report common fields
    report_update = schemas.ReportUpdate(**request_body)
    updated_report = crud.update_report(db, report_id, report_update, current_user.id)
    if not updated_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    logger.info(f"[UPDATE_REPORT] Report is_multi_property: {updated_report.is_multi_property}")

    # Handle properties for multi-property reports
    if properties_data:
        logger.info(f"[UPDATE_REPORT] Updating properties for multi-property report {report_id}")
        logger.info(f"[UPDATE_REPORT] Received {len(properties_data)} properties")

        # Get current properties associated with this report
        current_property_ids = {rp.property_id for rp in updated_report.property_associations}
        logger.info(f"[UPDATE_REPORT] Current property IDs in DB: {current_property_ids}")

        # Get incoming property IDs (only those that are existing properties with integer IDs)
        incoming_property_ids = {
            prop_data.get('id') for prop_data in properties_data
            if prop_data.get('id') and isinstance(prop_data.get('id'), int)
        }
        logger.info(f"[UPDATE_REPORT] Incoming property IDs from frontend: {incoming_property_ids}")

        # Find properties to delete (exist in DB but not in incoming data)
        properties_to_delete = current_property_ids - incoming_property_ids
        logger.info(f"[UPDATE_REPORT] Properties to delete: {properties_to_delete}")

        # Delete removed properties
        for property_id in properties_to_delete:
            logger.info(f"[UPDATE_REPORT] Deleting property {property_id} from report")
            # Delete the association
            db.query(models.ReportProperty).filter(
                models.ReportProperty.report_id == report_id,
                models.ReportProperty.property_id == property_id
            ).delete()

            # Optionally delete the property itself if it's not used in other reports
            property_usage_count = db.query(models.ReportProperty).filter(
                models.ReportProperty.property_id == property_id
            ).count()

            if property_usage_count == 0:
                logger.info(f"[UPDATE_REPORT] Property {property_id} not used in any other reports, deleting")
                db.query(models.Property).filter(models.Property.id == property_id).delete()

        # Update or create properties
        for prop_data in properties_data:
            property_id = prop_data.get('id')

            # If property has an integer ID, it exists - update it
            if property_id and isinstance(property_id, int):
                logger.info(f"[UPDATE_REPORT] Updating existing property {property_id}")
                property_update = schemas.PropertyUpdate(**prop_data)
                crud.update_property(db, property_id, property_update, current_user.id)
            else:
                # Create new property
                logger.info(f"[UPDATE_REPORT] Creating new property")
                property_create = schemas.PropertyCreate(**prop_data)
                new_property = crud.create_property(db, property_create, current_user.id)

                # Associate with report
                # Check if association already exists
                existing_assoc = db.query(models.ReportProperty).filter(
                    models.ReportProperty.report_id == report_id,
                    models.ReportProperty.property_id == new_property.id
                ).first()

                if not existing_assoc:
                    property_order = prop_data.get('property_order', len(properties_data))
                    report_property = models.ReportProperty(
                        report_id=report_id,
                        property_id=new_property.id,
                        property_order=property_order
                    )
                    db.add(report_property)

        db.commit()
        db.refresh(updated_report)

    # Return with properties if multi-property
    if updated_report.is_multi_property:
        properties = updated_report.properties
        response_data = {
            **{key: getattr(updated_report, key) for key in updated_report.__dict__ if not key.startswith('_')},
            'properties': properties
        }
        return response_data

    return updated_report

@app.delete("/api/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a report (must belong to authenticated user)"""
    success = crud.delete_report(db, report_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    return None

@app.post("/api/reports/{report_id}/duplicate", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate an existing report as a new draft"""
    logger.info(f"[DUPLICATE_REPORT] User {current_user.email} duplicating report {report_id}")

    new_report = crud.duplicate_report(db, report_id, current_user.id)
    if not new_report:
        logger.warning(f"[DUPLICATE_REPORT] Report {report_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    logger.info(f"[DUPLICATE_REPORT] Successfully created duplicate report {new_report.id}")
    return new_report

@app.post("/api/reports/{report_id}/generate")
async def generate_report_docx(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a DOCX file from report data combined with user profile data
    """
    logger.info(f"[DOCX_GENERATION] Starting generation for report_id={report_id}, user={current_user.email}")

    # Get report data from database
    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        logger.warning(f"[DOCX_GENERATION] Report {report_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    logger.info(f"[DOCX_GENERATION] Report found - status: {db_report.status}, type: {db_report.report_type}")
    logger.debug(f"[DOCX_GENERATION] Has buildings: {bool(db_report.buildings)}, num_buildings: {len(db_report.buildings) if db_report.buildings else 0}")

    try:
        # Generate DOCX file with both report and user data
        logger.info(f"[DOCX_GENERATION] Calling generate_user_data_docx...")
        docx_stream = generate_user_data_docx(db_report, current_user)
        logger.info(f"[DOCX_GENERATION] DOCX generated successfully, size: {len(docx_stream.getvalue())} bytes")

        filename = get_filename_for_user(db_report)
        logger.info(f"[DOCX_GENERATION] Filename: {filename}")

        # Return as downloadable file
        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[DOCX_GENERATION_ERROR] Error type: {type(e).__name__}")
        logger.error(f"[DOCX_GENERATION_ERROR] Error message: {str(e)}")
        logger.error(f"[DOCX_GENERATION_ERROR] Full traceback:\n{error_trace}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating DOCX file: {type(e).__name__}: {str(e)}"
        )


# ===== ASYNC JOB ENDPOINTS FOR DOCUMENT GENERATION =====
from .services.job_service import JobService
from .services.file_storage import FileStorage

@app.post("/api/reports/{report_id}/generate-async", response_model=schemas.JobResponse)
async def generate_report_docx_async(
    report_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start async DOCX generation job for a report.

    Returns immediately with a job_id that can be polled for status.
    """
    logger.info(f"[ASYNC_DOCX] Starting async generation for report_id={report_id}, user={current_user.email}")

    # Verify report exists and belongs to user
    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    # Create a job
    job = JobService.create_job(
        db=db,
        user_id=current_user.id,
        report_id=report_id,
        job_type="docx_generation"
    )

    # Queue the background task
    background_tasks.add_task(JobService.process_docx_job, job.id)

    logger.info(f"[ASYNC_DOCX] Job {job.id} created and queued")
    return job


@app.get("/api/jobs/{job_id}", response_model=schemas.JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a background job.

    Used for polling progress of document generation.
    """
    job = JobService.get_job(db, job_id, current_user.id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Build response
    download_ready = job.status == "completed" and job.result_url is not None

    return schemas.JobStatusResponse(
        id=job.id,
        status=job.status,
        progress_percent=job.progress_percent or 0,
        progress_message=job.progress_message,
        error_message=job.error_message,
        download_ready=download_ready,
        download_url=f"/api/jobs/{job.id}/download" if download_ready else None,
        filename=job.result_filename
    )


@app.get("/api/jobs/{job_id}/download")
async def download_job_result(
    job_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the result of a completed job.
    """
    job = JobService.get_job(db, job_id, current_user.id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job.status})"
        )

    if not job.result_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job result not available"
        )

    # Get file from storage
    result = FileStorage.get_file(job.result_url)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File has expired or been deleted"
        )

    content, filename, content_type = result

    # Return as downloadable file
    from io import BytesIO
    return StreamingResponse(
        BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/api/jobs", response_model=List[schemas.JobResponse])
async def list_user_jobs(
    limit: int = 10,
    status_filter: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List recent jobs for the current user.
    """
    jobs = JobService.get_user_jobs(
        db=db,
        user_id=current_user.id,
        limit=min(limit, 50),  # Cap at 50
        status_filter=status_filter
    )
    return jobs


# ===== PROPERTY ENDPOINTS (Protected) =====
@app.post("/api/properties", response_model=schemas.PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: schemas.PropertyCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property for the authenticated user"""
    logger.info(f"[CREATE PROPERTY] User: {current_user.email}")
    try:
        db_property = crud.create_property(db, property_data, current_user.id)
        logger.info(f"[CREATE PROPERTY] Property created with ID: {db_property.id}")
        return db_property
    except ValueError as e:
        logger.error(f"[CREATE PROPERTY] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[CREATE PROPERTY] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating property: {str(e)}"
        )

@app.get("/api/properties", response_model=list[schemas.PropertyResponse])
async def get_user_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all properties for the authenticated user (paginated)"""
    return crud.get_user_properties(db, current_user.id, skip=skip, limit=limit)

@app.get("/api/properties/templates", response_model=list[schemas.PropertyTemplateResponse])
async def get_property_templates(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all property templates (Property Library) for the authenticated user"""
    templates = crud.get_property_templates(db, current_user.id)
    return [
        schemas.PropertyTemplateResponse(
            id=p.id,
            template_name=p.template_name,
            property_village=p.property_village,
            property_district=p.property_district,
            land_extent_formatted=p.land_extent_formatted,
            last_valued_date=p.last_valued_date,
            valuation_market_value=p.valuation_market_value
        )
        for p in templates
    ]

@app.get("/api/properties/{property_id}", response_model=schemas.PropertyResponse)
async def get_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific property by ID (must belong to authenticated user)"""
    db_property = crud.get_property(db, property_id, current_user.id)
    if db_property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found"
        )
    return db_property

@app.put("/api/properties/{property_id}", response_model=schemas.PropertyResponse)
async def update_property(
    property_id: int,
    property_update: schemas.PropertyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a property (must belong to authenticated user)"""
    try:
        updated_property = crud.update_property(db, property_id, property_update, current_user.id)
        if not updated_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )
        return updated_property
    except ValueError as e:
        logger.error(f"[UPDATE PROPERTY] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete("/api/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a property (must belong to authenticated user, and not used in any reports)"""
    try:
        success = crud.delete_property(db, property_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )
        return None
    except ValueError as e:
        # Property is in use
        logger.warning(f"[DELETE PROPERTY] Cannot delete: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

# ===== MULTI-PROPERTY REPORT ENDPOINTS (Protected) =====
@app.post("/api/reports/multi-property", response_model=schemas.MultiPropertyReportResponse, status_code=status.HTTP_201_CREATED)
async def create_multi_property_report(
    report_data: schemas.MultiPropertyReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a multi-property report with existing or new properties"""
    logger.info(f"[CREATE MULTI-PROPERTY REPORT] User: {current_user.email}")
    logger.info(f"  Property IDs: {report_data.property_ids}")
    logger.info(f"  New properties: {len(report_data.properties or [])}")

    try:
        db_report = crud.create_multi_property_report(db, report_data, current_user.id)
        logger.info(f"[CREATE MULTI-PROPERTY REPORT] Report created with ID: {db_report.id}")
        logger.info(f"  Property count: {db_report.property_count}")
        logger.info(f"  Total valuation: {db_report.total_valuation_amount}")

        # Build response with properties
        response = schemas.MultiPropertyReportResponse(
            id=db_report.id,
            is_multi_property=db_report.is_multi_property,
            property_count=db_report.property_count,
            total_valuation_amount=db_report.total_valuation_amount,
            properties=[rp.property for rp in db_report.property_associations],
            invoice_data=db_report.invoice_data
        )
        return response
    except ValueError as e:
        logger.error(f"[CREATE MULTI-PROPERTY REPORT] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[CREATE MULTI-PROPERTY REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating multi-property report: {str(e)}"
        )

@app.post("/api/reports/{report_id}/properties/{property_id}", response_model=schemas.ReportPropertyResponse, status_code=status.HTTP_201_CREATED)
async def add_property_to_report(
    report_id: int,
    property_id: int,
    property_order: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an existing property to a report"""
    logger.info(f"[ADD PROPERTY TO REPORT] Report: {report_id}, Property: {property_id}")

    try:
        report_property = crud.add_property_to_report(
            db, report_id, property_id, current_user.id, property_order
        )
        logger.info(f"  Added with order: {report_property.property_order}")
        return report_property
    except ValueError as e:
        logger.error(f"[ADD PROPERTY TO REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete("/api/reports/{report_id}/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property_from_report(
    report_id: int,
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a property from a report"""
    logger.info(f"[REMOVE PROPERTY FROM REPORT] Report: {report_id}, Property: {property_id}")

    try:
        crud.remove_property_from_report(db, report_id, property_id, current_user.id)
        logger.info(f"  Property removed successfully")
        return None
    except ValueError as e:
        logger.error(f"[REMOVE PROPERTY FROM REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.put("/api/reports/{report_id}/properties/reorder", status_code=status.HTTP_200_OK)
async def reorder_report_properties(
    report_id: int,
    property_order_map: dict[int, int],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reorder properties in a report (drag-drop support)

    Body: {"property_id": new_order, ...}
    Example: {1: 2, 2: 1, 3: 3} swaps first two properties
    """
    logger.info(f"[REORDER PROPERTIES] Report: {report_id}")
    logger.info(f"  New order: {property_order_map}")

    try:
        crud.reorder_report_properties(db, report_id, property_order_map, current_user.id)
        logger.info(f"  Properties reordered successfully")
        return {"status": "success", "message": "Properties reordered"}
    except ValueError as e:
        logger.error(f"[REORDER PROPERTIES] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.put("/api/reports/{report_id}/properties/{property_id}", response_model=schemas.PropertyResponse)
async def update_report_property(
    report_id: int,
    property_id: int,
    property_update: schemas.PropertyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an individual property within a report

    Supports updating all property fields including status ('draft' or 'completed')
    """
    logger.info(f"[UPDATE REPORT PROPERTY] Report: {report_id}, Property: {property_id}")

    # Verify user owns the report
    db_report = crud.get_report(db, report_id, current_user.id)
    if not db_report:
        logger.error(f"  Report not found or access denied")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied"
        )

    # Update the property
    db_property = crud.update_property(db, property_id, property_update, current_user.id)
    if not db_property:
        logger.error(f"  Property not found or access denied")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or access denied"
        )

    logger.info(f"  Property updated successfully (status: {db_property.status})")
    return db_property

@app.post("/api/reports/{report_id}/properties/{property_id}/duplicate", response_model=schemas.PropertyResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_report_property(
    report_id: int,
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate a property within a report (deep copy including images)

    Creates a new property with all data copied from the original.
    The duplicated property starts with status='draft' and is added to the report.
    """
    logger.info(f"[DUPLICATE PROPERTY] Report: {report_id}, Property: {property_id}")

    try:
        new_property = crud.duplicate_property(db, report_id, property_id, current_user.id)
        logger.info(f"  Property duplicated successfully (new ID: {new_property.id})")
        return new_property
    except ValueError as e:
        logger.error(f"[DUPLICATE PROPERTY] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.patch("/api/properties/{property_id}/status")
async def update_property_status(
    property_id: int,
    status_update: schemas.PropertyStatusUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the status of a property ('draft' or 'completed')

    Body: {"status": "completed"} or {"status": "draft"}
    """
    logger.info(f"[UPDATE PROPERTY STATUS] Property: {property_id}")

    status_value = status_update.status

    try:
        db_property = crud.update_property_status(db, property_id, status_value, current_user.id)
        if not db_property:
            logger.error(f"  Property not found or access denied")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found or access denied"
            )

        logger.info(f"  Status updated to: {status_value}")
        return {"status": "success", "property_id": property_id, "new_status": status_value}
    except ValueError as e:
        logger.error(f"[UPDATE PROPERTY STATUS] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/reports/{report_id}/properties", response_model=list[schemas.ReportPropertyResponse])
async def get_report_properties(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all properties for a report, ordered by property_order"""
    # Verify user owns the report
    db_report = crud.get_report(db, report_id, current_user.id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    return crud.get_report_properties(db, report_id)

# OCR Document Processing Endpoint
@app.post("/api/ocr/extract")
async def extract_data_from_document(
    files: List[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract property data from uploaded documents (survey plan, deed pages, etc.) using OCR.

    - **files**: Multiple image files (JPEG, PNG, WEBP, PDF) - max 10 files, 10MB each
    - **document_type**: Optional hint ('survey_plan', 'deed', 'title_certificate')

    Returns combined extracted data with confidence scores.
    """
    try:
        # 1. Check maximum number of files
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many files uploaded. Maximum {MAX_FILES_PER_UPLOAD} files allowed, got {len(files)} files"
            )

        # 2. Validate each file (size, extension, magic number)
        for file in files:
            await validate_upload_file(file)

        # Process all documents
        result = await process_multiple_documents(files, document_type)

        # Comprehensive safety checks
        if result is None:
            logger.error("[OCR_ENDPOINT] process_multiple_documents returned None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OCR processing returned None - server may be reloading. Please try again in a few seconds."
            )

        if not isinstance(result, dict):
            logger.error(f"[OCR_ENDPOINT] Invalid result type: {type(result)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing returned unexpected type: {type(result)}. Server may be reloading."
            )

        # Check for success flag (with defensive .get())
        success = result.get('success') if isinstance(result, dict) else False
        if not success:
            error_msg = result.get('error', 'OCR processing failed') if isinstance(result, dict) else 'Unknown error'
            logger.error(f"[OCR_ENDPOINT] Processing failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        # If extent data was extracted, calculate all derived fields
        extracted_data = result.get('extracted_data', {})
        if extracted_data.get('land_extent_acres') is not None:
            extent_data = calculate_extent_data(
                acres=extracted_data.get('land_extent_acres', 0),
                roods=extracted_data.get('land_extent_roods', 0),
                perches=extracted_data.get('land_extent_perches', 0)
            )
            # Add calculated fields to extracted data
            extracted_data.update(extent_data)
            result['extracted_data'] = extracted_data

        return {
            "status": "success",
            "message": "Document processed successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

# Autocomplete API Endpoints (Public - no authentication required)
@app.get("/api/autocomplete")
async def get_autocomplete_data():
    """
    Get all autocomplete data for professional credentials form
    Returns membership levels, banks, qualifications, designations, etc.
    """
    try:
        return get_all_autocomplete_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching autocomplete data: {str(e)}"
        )

@app.get("/api/autocomplete/{category}")
async def search_autocomplete_category(
    category: str,
    q: str = "",
    limit: int = 10
):
    """
    Search within a specific autocomplete category
    Categories: membership_levels, academic_qualifications, professional_designations,
               post_nominal_letters, sri_lankan_banks, office_departments, provinces
    """
    try:
        if limit > 50:
            limit = 50  # Prevent excessive results

        results = search_autocomplete(category, q, limit)
        return {
            "category": category,
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching autocomplete data: {str(e)}"
        )

# Administrative Divisions Endpoint
@app.get("/api/administrative-divisions")
async def get_administrative_divisions():
    """
    Get Sri Lankan administrative divisions (Districts and DS Divisions)
    Returns hierarchical data: {district: [{name, gn_count}, ...]}
    """
    try:
        import json
        import os

        # Load administrative divisions data
        json_path = os.path.join(os.path.dirname(__file__), "administrative_divisions.json")

        if not os.path.exists(json_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrative divisions data not found"
            )

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "status": "success",
            "data": data,
            "total_districts": len(data),
            "total_ds_divisions": sum(len(v) for v in data.values())
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrative divisions data file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading administrative divisions: {str(e)}"
        )

@app.get("/api/administrative-divisions/{district}")
async def get_ds_divisions_by_district(district: str):
    """
    Get DS Divisions for a specific district
    Returns: [{name, gn_count}, ...]
    """
    try:
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), "administrative_divisions.json")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Find district (case-insensitive)
        district_data = None
        for key in data.keys():
            if key.lower() == district.lower():
                district_data = data[key]
                break

        if not district_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"District '{district}' not found"
            )

        return {
            "status": "success",
            "district": district,
            "ds_divisions": district_data
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrative divisions data file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading DS divisions: {str(e)}"
        )

# Google Maps API Proxy Endpoints (Public - for frontend use)
@app.post("/api/maps/geocode")
async def geocode_address_endpoint(request: dict):
    """
    Geocode an address to get coordinates and location details
    Request body: {address: string}
    """
    try:
        from .maps_service import maps_service
        address = request.get("address")
        if not address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address is required"
            )

        result = maps_service.geocode_address(address)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error geocoding address: {str(e)}"
        )

@app.post("/api/maps/places/autocomplete")
async def places_autocomplete_endpoint(request: dict):
    """
    Get place suggestions using Google Places Autocomplete
    Request body: {input: string, location?: string}
    """
    try:
        from .maps_service import maps_service
        input_text = request.get("input")
        if not input_text or len(input_text) < 2:
            return []

        location = request.get("location")
        results = maps_service.places_autocomplete(input_text, location)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching autocomplete suggestions: {str(e)}"
        )

@app.post("/api/maps/places/details")
async def place_details_endpoint(request: dict):
    """
    Get detailed information about a place from place_id
    Request body: {place_id: string}
    """
    try:
        from .maps_service import maps_service
        place_id = request.get("place_id")
        if not place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Place ID is required"
            )

        result = maps_service.get_place_details(place_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place not found"
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching place details: {str(e)}"
        )

@app.post("/api/maps/directions")
async def directions_endpoint(request: dict):
    """
    Get route directions between two points
    Request body: {origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float}
    """
    try:
        from .maps_service import maps_service
        origin_lat = request.get("origin_lat")
        origin_lng = request.get("origin_lng")
        dest_lat = request.get("dest_lat")
        dest_lng = request.get("dest_lng")

        if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Origin and destination coordinates are required"
            )

        result = maps_service.get_directions(origin_lat, origin_lng, dest_lat, dest_lng)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        # Also generate professional directions text
        if result.get("steps"):
            starting_point = request.get("starting_point_name", "the starting point")
            result["professional_text"] = maps_service.generate_professional_directions_text(
                result["steps"],
                starting_point,
                result["distance_text"]
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching directions: {str(e)}"
        )

@app.post("/api/maps/static-map")
async def static_map_endpoint(request: dict):
    """
    Generate static map URL with route
    Request body: {origin_lat, origin_lng, dest_lat, dest_lng, polyline, width?, height?}
    """
    try:
        from .maps_service import maps_service
        import traceback

        logger.debug(f"[DEBUG] Received static map request: {request}")

        origin_lat = request.get("origin_lat")
        origin_lng = request.get("origin_lng")
        dest_lat = request.get("dest_lat")
        dest_lng = request.get("dest_lng")
        polyline = request.get("polyline")

        logger.debug(f"[DEBUG] Extracted params - origin: ({origin_lat}, {origin_lng}), dest: ({dest_lat}, {dest_lng}), polyline length: {len(polyline) if polyline else 0}")

        if not all([origin_lat, origin_lng, dest_lat, dest_lng, polyline]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All coordinates and polyline are required"
            )

        width = request.get("width", 800)
        height = request.get("height", 600)

        url = maps_service.generate_static_map_url(
            origin_lat, origin_lng, dest_lat, dest_lng, polyline, width, height
        )

        logger.debug(f"[DEBUG] Generated map URL: {url}")

        return {"map_url": url}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Static map generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating static map: {str(e)}"
        )

@app.post("/api/maps/transform-access")
async def transform_access_endpoint(request: dict):
    """
    Transform Google Maps directions with road condition details into professional valuation report format.
    Request body: {
        starting_point_name: str (e.g., "Clock tower junction of Kurunegala town"),
        property_position: str ("left" or "right"),
        total_distance_km: float,
        total_duration_mins: int,
        steps: [{instruction, distance, duration, maneuver}],  # Google Maps turn-by-turn steps
        road_conditions: [{  # NEW: Simplified road conditions
            road_type: str ("paved_road", "carpet_road", "gravel_road", "sand_road", "earth_road"),
            condition: str ("excellent", "good", "fair", "poor"),
            notes: str (optional)
        }],
        road_segments: [{...}]  # DEPRECATED: Old format (kept for backward compatibility)
    }
    """
    try:
        from .services.access_transformer import (
            transform_directions_to_professional,
            generate_fallback_access_text,
            extract_navigation_entities
        )

        starting_point_name = request.get("starting_point_name")
        steps = request.get("steps", [])  # Google Maps turn-by-turn steps
        road_conditions = request.get("road_conditions", [])  # NEW: Simplified road conditions
        road_segments = request.get("road_segments", [])  # OLD: For backward compatibility
        total_distance_km = request.get("total_distance_km", 0)
        total_duration_mins = request.get("total_duration_mins", 0)
        property_position = request.get("property_position", "right")

        # Log received data for debugging
        logger.info(f"[TRANSFORM_ACCESS] Request received:")
        logger.debug(f"  Starting point: {starting_point_name}")
        logger.debug(f"  Steps count: {len(steps)}")
        if steps:
            logger.debug(f"  First step sample: {steps[0]}")
        logger.debug(f"  Road conditions count: {len(road_conditions)}")
        logger.debug(f"  Total distance: {total_distance_km} km")
        logger.debug(f"  Total duration: {total_duration_mins} mins")

        if not starting_point_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="starting_point_name is required"
            )

        try:
            # Try AI transformation with comprehensive data
            professional_text = transform_directions_to_professional(
                starting_point_name=starting_point_name,
                total_distance_km=total_distance_km,
                total_duration_mins=total_duration_mins,
                property_position=property_position,
                road_conditions=road_conditions,  # NEW: Simplified format
                road_segments=road_segments,  # OLD: Backward compatibility
                steps=steps  # Google Maps turn-by-turn steps
            )
        except Exception as ai_error:
            logger.warning(f"[WARN] AI transformation failed, using fallback: {ai_error}")
            # Extract navigation entities for enhanced fallback
            navigation_entities = extract_navigation_entities(steps) if steps else None

            # Fallback to enhanced text with navigation entities if available
            professional_text = generate_fallback_access_text(
                starting_point_name=starting_point_name,
                total_distance_km=total_distance_km,
                total_duration_mins=total_duration_mins,
                property_position=property_position,
                navigation_entities=navigation_entities
            )

        return {"professional_text": professional_text}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Access transformation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transforming access directions: {str(e)}"
        )
# Locality Information Endpoints
@app.post("/api/locality/nearby-facilities")
async def get_nearby_facilities_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Fetch nearby facilities using Google Places API
    Request body: {
        latitude: float,
        longitude: float,
        radius_meters?: int (default 5000),
        facility_types?: string[] (optional, defaults to all)
    }
    """
    try:
        from .services.places_service import fetch_nearby_facilities, get_distance_to_major_town, find_nearest_transport

        latitude = request.get("latitude")
        longitude = request.get("longitude")
        radius_meters = request.get("radius_meters", 5000)
        facility_types = request.get("facility_types")

        if not latitude or not longitude:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and longitude are required"
            )

        # Fetch nearby facilities
        facilities = await fetch_nearby_facilities(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            facility_types=facility_types
        )

        # Get distance to major town
        major_town, distance = await get_distance_to_major_town(latitude, longitude)

        # Find nearest transport
        transport = await find_nearest_transport(latitude, longitude)

        return {
            "status": "success",
            "facilities": facilities,
            "major_town": {
                "name": major_town,
                "distance_km": distance
            },
            "transport": transport
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Nearby facilities fetch failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching nearby facilities: {str(e)}"
        )


@app.post("/api/locality/generate-narrative")
async def generate_locality_narrative_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate professional locality description using AI
    Request body: All locality data fields (village, district, facilities, etc.)
    """
    try:
        from .services.locality_narrative import generate_locality_narrative

        # Extract all locality fields from request
        narrative = await generate_locality_narrative(
            property_village=request.get("property_village"),
            property_district=request.get("property_district"),
            divisional_secretariat=request.get("divisional_secretariat"),
            pradeshiya_sabha=request.get("pradeshiya_sabha"),
            distance_to_major_town_km=request.get("distance_to_major_town_km"),
            major_town_name=request.get("major_town_name"),
            nearby_facilities=request.get("nearby_facilities"),
            has_electricity=request.get("has_electricity"),
            water_supply_type=request.get("water_supply_type"),
            telecommunication_types=request.get("telecommunication_types"),
            internet_types=request.get("internet_types"),
            has_public_transport=request.get("has_public_transport"),
            public_transport_routes=request.get("public_transport_routes"),
            public_transport_frequency=request.get("public_transport_frequency"),
            area_type=request.get("area_type"),
            development_level=request.get("development_level"),
            predominant_building_type=request.get("predominant_building_type"),
            is_tourist_area=request.get("is_tourist_area"),
            tourist_attractions_nearby=request.get("tourist_attractions_nearby")
        )

        if not narrative:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate locality narrative"
            )

        return {
            "status": "success",
            "narrative": narrative
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Locality narrative generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating locality narrative: {str(e)}"
        )


@app.post("/api/building/generate-description")
async def generate_building_description_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate professional building description using AI.
    Used during DOCX generation or when user manually requests it.
    """
    try:
        from .services.building_narrative import generate_building_narrative

        description = await generate_building_narrative(
            building_name=request.get("building_name", "Building"),
            building_type=request.get("building_type", "residential"),
            stories=request.get("stories", 1),
            floors=request.get("floors"),
            construction_materials=request.get("construction_materials"),
            utilities_services=request.get("utilities_services"),
            total_floor_area=request.get("total_floor_area"),
            building_age=request.get("building_age"),
            condition=request.get("condition"),
            roof_types=request.get("roof_types"),
            wall_types=request.get("wall_types"),
            floor_types=request.get("floor_types")
        )

        if not description:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate description - check API key"
            )

        return {
            "status": "success",
            "description": description,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Building description error: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Building description generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating building description: {str(e)}"
        )


@app.post("/api/land/generate-description")
async def generate_land_description_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate professional land description using AI.

    Takes land characteristic data and returns an AI-generated professional
    description with length proportional to the amount of data provided.
    """
    try:
        from .services.land_narrative import generate_land_narrative

        description = await generate_land_narrative(
            land_shape=request.get("land_shape"),
            land_type=request.get("land_type"),
            land_level=request.get("land_level"),
            land_level_difference=request.get("land_level_difference"),
            land_frontage_type=request.get("land_frontage_type"),
            land_frontage_width=request.get("land_frontage_width"),
            land_frontage_description=request.get("land_frontage_description"),
            soil_type=request.get("soil_type"),
            water_table_depth=request.get("water_table_depth"),
            flood_risk=request.get("flood_risk"),
            land_condition=request.get("land_condition"),
            elevation_changes=request.get("elevation_changes"),
            drainage_pattern=request.get("drainage_pattern"),
            vegetation_type=request.get("vegetation_type"),
            natural_features=request.get("natural_features")
        )

        if not description:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate land description. Please check ANTHROPIC_API_KEY configuration."
            )

        return {
            "status": "success",
            "description": description,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Land description generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating land description: {str(e)}"
        )


@app.post("/api/admin/migrate-rooms")
async def migrate_rooms_to_building_level(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Migrate all buildings from floor-based to building-level rooms.

    This endpoint:
    1. Finds all reports and properties with buildings
    2. Aggregates rooms from floor-level to building-level
    3. Simplifies floor structure (removes rooms and accommodation_summary)
    4. Calculates building-level accommodation_summary

    Returns count of migrated reports and buildings.
    """
    try:
        from .migrations.migrate_rooms_to_building_level import migrate_property_buildings

        # Get all reports with buildings
        reports = db.query(models.Report).filter(models.Report.buildings.isnot(None)).all()

        # Get all properties with buildings
        properties = db.query(models.Property).filter(models.Property.buildings.isnot(None)).all()

        migrated_reports = 0
        migrated_buildings = 0

        # Migrate reports
        for report in reports:
            if report.buildings:
                original_building_count = len(report.buildings)
                report_data = {'buildings': report.buildings}
                migrated_data = migrate_property_buildings(report_data)
                report.buildings = migrated_data['buildings']
                migrated_reports += 1
                migrated_buildings += original_building_count

        # Migrate properties
        for prop in properties:
            if prop.buildings:
                original_building_count = len(prop.buildings)
                property_data = {'buildings': prop.buildings}
                migrated_data = migrate_property_buildings(property_data)
                prop.buildings = migrated_data['buildings']
                migrated_buildings += original_building_count

        # Commit all changes
        db.commit()

        return {
            "status": "success",
            "message": "Migration completed successfully",
            "reports_processed": migrated_reports,
            "properties_processed": len(properties),
            "total_buildings_migrated": migrated_buildings,
            "migrated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] Migration failed: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Migration traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@app.post("/api/admin/migrate-occupier")
async def migrate_occupier_to_building_level(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Migrate occupier information from property-level to building-level.

    This endpoint:
    1. Finds all reports and properties with property-level occupier data
    2. Copies occupier_name and occupier_relationship to all buildings
    3. Preserves property-level fields for backward compatibility

    Returns count of migrated reports, properties, and buildings.
    """
    try:
        from .migrations.migrate_occupier_to_building_level import migrate_report, migrate_property

        # Get all reports with property-level occupier and buildings
        reports = db.query(models.Report).filter(
            models.Report.occupier_name.isnot(None),
            models.Report.buildings.isnot(None)
        ).all()

        # Get all properties with property-level occupier and buildings
        properties = db.query(models.Property).filter(
            models.Property.occupier_name.isnot(None),
            models.Property.buildings.isnot(None)
        ).all()

        migrated_reports = 0
        migrated_properties = 0
        migrated_buildings = 0

        # Migrate reports
        for report in reports:
            if report.buildings and report.occupier_name:
                report_data = {
                    'occupier_name': report.occupier_name,
                    'occupier_relationship': report.occupier_relationship,
                    'buildings': report.buildings
                }
                migrated_data = migrate_report(report_data)
                report.buildings = migrated_data['buildings']
                migrated_reports += 1
                migrated_buildings += len(report.buildings)

        # Migrate properties
        for prop in properties:
            if prop.buildings and prop.occupier_name:
                property_data = {
                    'occupier_name': prop.occupier_name,
                    'occupier_relationship': prop.occupier_relationship,
                    'buildings': prop.buildings
                }
                migrated_data = migrate_property(property_data)
                prop.buildings = migrated_data['buildings']
                migrated_properties += 1
                migrated_buildings += len(prop.buildings)

        # Commit all changes
        db.commit()

        return {
            "status": "success",
            "message": "Occupier migration completed successfully",
            "reports_processed": migrated_reports,
            "properties_processed": migrated_properties,
            "total_buildings_migrated": migrated_buildings,
            "migrated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] Occupier migration failed: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Migration traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Occupier migration failed: {str(e)}"
        )


@app.post("/api/admin/migrate-certificate-fields")
async def migrate_certificate_fields(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Migrate certificate_survey_plan_ref to plan_number.

    This is a one-time migration that:
    1. Copies certificate_survey_plan_ref to plan_number if plan_number is empty
    2. Copies certificate_survey_plan_date to plan_date if plan_date is empty
    3. Preserves original certificate fields for backward compatibility

    The migration allows consolidation of certificate identification fields,
    enabling a flexible Certificate of Identity system in reports.

    Returns:
        Dict with migration statistics including total reports and migrated count
    """
    try:
        from .migrations.migrate_certificate_to_plan_number import migrate_all_reports

        logger.info("[ADMIN] Starting certificate fields migration")
        result = migrate_all_reports(db)
        logger.info(f"[ADMIN] Migration complete: {result}")

        return {
            "status": "success",
            "message": "Certificate fields migration completed successfully",
            "total_reports": result['total_reports'],
            "migrated_reports": result['migrated_reports'],
            "skipped_reports": result['skipped_reports'],
            "migrated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] Certificate migration failed: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"[ERROR] Migration traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Certificate migration failed: {str(e)}"
        )


# Legacy v0.0 endpoints removed for clean v0.1 implementation
# All functionality moved to authenticated user + report system
# Available endpoints: /api/auth/*, /api/reports/*, /api/profile, /api/autocomplete/*, /api/maps/*, /api/locality/*

