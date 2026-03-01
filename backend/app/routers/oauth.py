"""
Google OAuth endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import logging
import secrets

from .. import models, schemas, crud
from ..database import get_db
from ..auth import (
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)
from ..services.google_oauth_service import GoogleOAuthService

router = APIRouter()
logger = logging.getLogger(__name__)

IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"


@router.get("/api/auth/google/authorize", response_model=schemas.GoogleAuthUrlResponse)
async def google_authorize():
    """
    Get Google OAuth authorization URL.

    Returns the URL to redirect the user to for Google consent screen.
    The state parameter is stored in Redis and verified in the callback
    to prevent OAuth CSRF attacks.
    """
    if not GoogleOAuthService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    state = secrets.token_urlsafe(32)

    try:
        from ..services.redis_client import get_redis_client
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.setex(f"oauth_state:{state}", 600, "1")
    except Exception as redis_err:
        logger.warning(f"[OAUTH] Could not store state in Redis: {redis_err}")

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

    Validates the state parameter against the Redis-stored value to prevent
    OAuth CSRF attacks, then exchanges the authorization code for tokens,
    fetches user info, and creates or links the user account. Returns JWT tokens.
    """
    if not GoogleOAuthService.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    try:
        from ..services.redis_client import get_redis_client
        redis_client = await get_redis_client()
        if redis_client:
            redis_key = f"oauth_state:{request.state}"
            valid = await redis_client.getdel(redis_key)
            if not valid:
                logger.warning("[OAUTH] Invalid or expired state parameter rejected")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired OAuth state. Please try signing in again."
                )
        else:
            logger.warning("[OAUTH] Redis unavailable — skipping state validation")
    except HTTPException:
        raise
    except Exception as redis_err:
        logger.warning(f"[OAUTH] Could not validate state in Redis: {redis_err}")

    try:
        _, user_info = GoogleOAuthService.get_token_and_user_info(request.code)

        user, is_new = GoogleOAuthService.create_or_link_user(
            db=db,
            user_info=user_info,
            models_module=models,
            crud_module=crud
        )

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
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=IS_PRODUCTION,
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
