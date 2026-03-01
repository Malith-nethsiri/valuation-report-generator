"""
Password reset and email verification endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import logging
import secrets

from .. import models, schemas, crud
from ..database import get_db
from ..auth import get_current_user, pwd_context, get_password_hash
from ..services.email_service import EmailService

router = APIRouter()
logger = logging.getLogger(__name__)


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
    user = crud.get_user_by_email(db, email=request.email)

    if user:
        reset_token = secrets.token_urlsafe(32)
        hashed_token = pwd_context.hash(reset_token)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        user.password_reset_token = hashed_token
        user.password_reset_expires = expiration
        db.commit()

        email_sent = EmailService.send_password_reset_email(user.email, reset_token)
        if not email_sent:
            logger.warning(f"Failed to send password reset email to {user.email}")
    else:
        logger.info(f"Password reset requested for non-existent email: {request.email}")

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
    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if not user.password_reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(timezone.utc):
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    if not pwd_context.verify(request.token, user.password_reset_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user.password_hash = get_password_hash(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    logger.info(f"Password reset successful for user: {user.email}")

    return schemas.PasswordResetResponse(
        success=True,
        message="Your password has been reset successfully. You can now log in with your new password."
    )


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
    if current_user.email_verified:
        return schemas.EmailVerificationResponse(
            success=True,
            message="Your email is already verified.",
            email_verified=True
        )

    verification_token = secrets.token_urlsafe(32)
    current_user.email_verification_token = pwd_context.hash(verification_token)
    current_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

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
    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )

    if user.email_verified:
        return schemas.EmailVerificationResponse(
            success=True,
            message="Your email is already verified.",
            email_verified=True
        )

    if not user.email_verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification pending. Please request a new verification email."
        )

    if user.email_verification_expires is None or user.email_verification_expires < datetime.now(timezone.utc):
        user.email_verification_token = None
        user.email_verification_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one."
        )

    if not pwd_context.verify(request.token, user.email_verification_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )

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
