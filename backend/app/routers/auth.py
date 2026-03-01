"""
Core authentication router.

Handles user registration, login, logout, token refresh, and current-user info.
Password reset lives in password.py. Google OAuth lives in oauth.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response, Cookie
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta, datetime, timezone
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
    existing_user = crud.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        db_user = crud.create_user(db, user_data)

        verification_token = secrets.token_urlsafe(32)
        db_user.email_verification_token = pwd_context.hash(verification_token)
        db_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()

        background_tasks.add_task(
            EmailService.send_verification_email,
            db_user.email,
            verification_token,
            db_user.full_name
        )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email},
            expires_delta=access_token_expires
        )

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
    """
    client_ip = request.client.host if request.client else "unknown"

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

    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
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
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await LoginLimiter.clear_attempts(client_ip, user_credentials.email)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
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
        path="/api/auth"
    )

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

    Supports both cookie-based and body-based refresh.
    """
    refresh_token = refresh_token_cookie
    if not refresh_token and request_body:
        refresh_token = request_body.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_refresh_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

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

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if old_jti:
        old_exp = payload.get("exp")
        if old_exp:
            expires_at = datetime.utcfromtimestamp(old_exp)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        blacklist_entry = models.TokenBlacklist(
            jti=old_jti,
            user_id=user.id,
            token_type="refresh",
            expires_at=expires_at
        )
        db.add(blacklist_entry)
        db.commit()
        logger.info(f"[TOKEN_ROTATION] Old refresh token blacklisted for user {user.email}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
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
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user


@router.post("/api/auth/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
):
    """
    Logout and revoke the current access token.

    Adds the token to a blacklist so it cannot be used again.
    Supports both cookie auth and header auth. Also clears HttpOnly cookies.
    """
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

    if jti and exp:
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
        logger.warning(f"[LOGOUT] Token without JTI cannot be revoked for user: {user_email}")

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")

    return {"message": "Successfully logged out"}
