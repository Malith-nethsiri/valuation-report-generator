"""
Authentication router.

Handles user registration, login, logout, token refresh, password reset,
email verification, and Google OAuth endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response, Cookie
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta, datetime
import os
import logging
import secrets

from .. import models, schemas, crud
from ..database import get_db
from ..auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    verify_token,
    security_optional,
    get_password_hash,
    pwd_context,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES
)
from ..services.email_service import EmailService
from ..services.google_oauth_service import GoogleOAuthService
from ..services.login_limiter import LoginLimiter

router = APIRouter()
logger = logging.getLogger(__name__)

IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"


@router.post("/api/auth/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    - **email**: User's email address (must be unique)
    - **password**: Password (minimum 6 characters)
    - **full_name**: User's full name
    - **phone**: Phone number (optional)

    Also sends a verification email (non-blocking).
    """
    from datetime import timezone

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

        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        db_user.email_verification_token = pwd_context.hash(verification_token)
        db_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()

        # Send verification email in background (non-blocking)
        background_tasks.add_task(
            EmailService.send_verification_email,
            db_user.email,
            verification_token,
            db_user.full_name
        )

        # Create access token (short-lived)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email},
            expires_delta=access_token_expires
        )

        # Create refresh token (longer-lived)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token = create_refresh_token(
            data={"sub": db_user.email},
            expires_delta=refresh_token_expires
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": db_user
        }
    except Exception as e:
        logger.error(f"[REGISTRATION_ERROR] Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user. Please try again."
        )


@router.post("/api/auth/login", response_model=schemas.TokenResponse)
async def login_user(
    user_credentials: schemas.UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login user and return access token.

    Security: Sets tokens in HttpOnly cookies for XSS protection.
    Also returns tokens in response body for backwards compatibility
    during migration period.

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

    # Create access token (short-lived)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # Create refresh token (longer-lived)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )

    # Set tokens in HttpOnly cookies (XSS-safe)
    # These cookies are automatically sent with requests
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # JavaScript cannot access
        secure=IS_PRODUCTION,  # HTTPS only in production
        samesite="strict",  # Prevent CSRF
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/api/auth"  # Only sent to auth endpoints
    )

    # Return tokens in body for backwards compatibility
    # Frontend will transition to cookie-based auth over time
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/api/auth/refresh", response_model=schemas.RefreshTokenResponse)
async def refresh_access_token(
    response: Response,
    request_body: Optional[schemas.RefreshTokenRequest] = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """
    Refresh tokens using a valid refresh token (with token rotation).

    Implements refresh token rotation for enhanced security:
    - Old refresh token is blacklisted
    - New access token AND new refresh token are issued
    - Prevents token replay attacks

    Supports both:
    - Cookie-based refresh (preferred, XSS-safe)
    - Body-based refresh (backwards compatibility)

    Returns new access token and refresh token. Also sets HttpOnly cookies.
    """
    # Get refresh token from cookie or request body
    refresh_token = refresh_token_cookie
    if not refresh_token and request_body:
        refresh_token = request_body.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the refresh token
    payload = verify_refresh_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if refresh token has been revoked
    old_jti = payload.get("jti")
    if old_jti:
        blacklisted = db.query(models.TokenBlacklist).filter(
            models.TokenBlacklist.jti == old_jti
        ).first()
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Get the email from the token
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the user still exists and is valid
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # === TOKEN ROTATION: Blacklist the old refresh token ===
    if old_jti:
        old_exp = payload.get("exp")
        if old_exp:
            # Convert Unix timestamp to datetime
            expires_at = datetime.utcfromtimestamp(old_exp)
        else:
            # Fallback: expire in the configured time
            expires_at = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        blacklist_entry = models.TokenBlacklist(
            jti=old_jti,
            user_id=user.id,
            token_type="refresh",
            expires_at=expires_at
        )
        db.add(blacklist_entry)
        db.commit()
        logger.info(f"[TOKEN_ROTATION] Old refresh token blacklisted for user {user.email}")

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # Create new refresh token (rotation)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )

    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # Set new refresh token cookie (rotation)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    logger.info(f"[TOKEN_REFRESH] New access and refresh tokens issued for user {user.email}")

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,  # For body-based clients
        "token_type": "bearer"
    }


@router.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user


# ===== LOGOUT ENDPOINT =====


@router.post("/api/auth/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
):
    """
    Logout and revoke the current access token.

    This adds the token to a blacklist so it cannot be used again,
    even if it hasn't expired yet. This is critical for security
    when a user explicitly logs out or if a token is compromised.

    Supports both cookie auth and header auth.
    Also clears HttpOnly cookies on logout.
    """
    # Get token from cookie or header
    token = None
    if access_token_cookie:
        token = access_token_cookie
    elif credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )

    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    jti = payload.get("jti")
    exp = payload.get("exp")
    user_email = payload.get("sub")
    token_type = payload.get("type", "access")

    # If token has JTI, blacklist it
    if jti and exp:
        from datetime import timezone
        # Get user ID for audit purposes
        user = crud.get_user_by_email(db, email=user_email) if user_email else None

        blacklist_entry = models.TokenBlacklist(
            jti=jti,
            user_id=user.id if user else None,
            token_type=token_type,
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc)
        )
        db.add(blacklist_entry)
        db.commit()

        logger.info(f"[LOGOUT] Token revoked for user: {user_email}")
    else:
        # Old token without JTI - can't blacklist, but log it
        logger.warning(f"[LOGOUT] Token without JTI cannot be revoked for user: {user_email}")

    # Clear HttpOnly cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")

    return {"message": "Successfully logged out"}


# ===== PASSWORD RESET ENDPOINTS =====


@router.post("/api/auth/forgot-password", response_model=schemas.PasswordResetResponse)
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.

    Sends a reset link to the provided email if it exists in the system.
    Always returns success to prevent email enumeration.

    Security: Token is hashed before storage (like a password) so database
    breach cannot be used to reset arbitrary accounts.
    """
    # Find user by email
    user = crud.get_user_by_email(db, email=request.email)

    if user:
        # Generate reset token (sent to user via email)
        reset_token = secrets.token_urlsafe(32)

        # Hash the token before storing (security: treat like a password)
        hashed_token = pwd_context.hash(reset_token)

        # Set token expiration (1 hour from now)
        from datetime import timezone
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        # Save HASHED token to database
        user.password_reset_token = hashed_token
        user.password_reset_expires = expiration
        db.commit()

        # Send PLAINTEXT token to user via email
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


@router.post("/api/auth/reset-password", response_model=schemas.PasswordResetResponse)
async def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using the token from the email.

    Security: Token is verified against stored hash (not compared directly).
    This requires email in request since we can't query by hashed token.
    """
    from datetime import timezone

    # Find user by email (can't query by hashed token)
    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        # Don't reveal whether email exists
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if user has a reset token
    if not user.password_reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token is expired
    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(timezone.utc):
        # Clear the expired token
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    # Verify the provided token against the stored hash
    if not pwd_context.verify(request.token, user.password_reset_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
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


# ===== EMAIL VERIFICATION ENDPOINTS =====


@router.post("/api/auth/send-verification", response_model=schemas.EmailVerificationResponse)
async def send_verification_email(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send or resend email verification link.

    Requires authentication. Generates a new verification token and sends
    an email with the verification link. Token expires in 24 hours.
    """
    from datetime import timezone

    # Check if already verified
    if current_user.email_verified:
        return schemas.EmailVerificationResponse(
            success=True,
            message="Your email is already verified.",
            email_verified=True
        )

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    # Store hashed token (same pattern as password reset)
    current_user.email_verification_token = pwd_context.hash(verification_token)
    current_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    # Send verification email in background
    background_tasks.add_task(
        EmailService.send_verification_email,
        current_user.email,
        verification_token,
        current_user.full_name
    )

    logger.info(f"Verification email sent to: {current_user.email}")

    return schemas.EmailVerificationResponse(
        success=True,
        message="Verification email sent. Please check your inbox.",
        email_verified=False
    )


@router.post("/api/auth/verify-email", response_model=schemas.EmailVerificationResponse)
async def verify_email(
    request: schemas.VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address using token from verification email.

    This endpoint does not require authentication so users can verify
    from a different device or after session expiry.
    """
    from datetime import timezone

    # Find user by email
    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )

    # Check if already verified
    if user.email_verified:
        return schemas.EmailVerificationResponse(
            success=True,
            message="Your email is already verified.",
            email_verified=True
        )

    # Check if user has a verification token
    if not user.email_verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification pending. Please request a new verification email."
        )

    # Check if token is expired
    if user.email_verification_expires is None or user.email_verification_expires < datetime.now(timezone.utc):
        # Clear the expired token
        user.email_verification_token = None
        user.email_verification_expires = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one."
        )

    # Verify the provided token against the stored hash
    if not pwd_context.verify(request.token, user.email_verification_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )

    # Mark email as verified and clear token
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.commit()

    logger.info(f"Email verified for user: {user.email}")

    return schemas.EmailVerificationResponse(
        success=True,
        message="Your email has been verified successfully!",
        email_verified=True
    )


# ===== GOOGLE OAUTH ENDPOINTS =====


@router.get("/api/auth/google/authorize", response_model=schemas.GoogleAuthUrlResponse)
async def google_authorize():
    """
    Get Google OAuth authorization URL.

    Returns the URL to redirect the user to for Google consent screen.
    The state parameter should be verified in the callback.
    """
    if not GoogleOAuthService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)

    try:
        authorization_url = GoogleOAuthService.get_authorization_url(state)
        return schemas.GoogleAuthUrlResponse(
            authorization_url=authorization_url,
            state=state
        )
    except Exception as e:
        logger.error(f"Failed to generate Google auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Google authentication"
        )


@router.post("/api/auth/google/callback", response_model=schemas.TokenResponse)
async def google_callback(
    request: schemas.GoogleCallbackRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.

    Exchanges the authorization code for tokens, fetches user info,
    and creates or links the user account. Returns JWT tokens.
    """
    if not GoogleOAuthService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    try:
        # Exchange code for tokens and get user info
        _, user_info = GoogleOAuthService.get_token_and_user_info(request.code)

        # Create or link user account
        user, is_new = GoogleOAuthService.create_or_link_user(
            db=db,
            user_info=user_info,
            models_module=models,
            crud_module=crud
        )

        # Create access token (short-lived)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )

        # Create refresh token (longer-lived)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token = create_refresh_token(
            data={"sub": user.email},
            expires_delta=refresh_token_expires
        )

        # Set HttpOnly cookies (same as regular login)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=os.getenv("ENV", "development") == "production",
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=os.getenv("ENV", "development") == "production",
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )

        logger.info(f"Google OAuth login successful for: {user.email} (new={is_new})")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    except ValueError as e:
        logger.error(f"Google OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error in Google OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again."
        )
