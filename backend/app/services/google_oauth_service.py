"""
Google OAuth service for "Sign in with Google" functionality.

Handles:
- OAuth authorization URL generation
- Token exchange with Google
- User info retrieval
- User account creation/linking
"""

import os
import logging
from typing import Optional, Tuple
from authlib.integrations.requests_client import OAuth2Session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Configuration from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# Google OAuth endpoints
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""

    @staticmethod
    def is_configured() -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: CSRF protection state token

        Returns:
            Authorization URL to redirect user to
        """
        if not GoogleOAuthService.is_configured():
            raise ValueError("Google OAuth not configured")

        client = OAuth2Session(
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            redirect_uri=GOOGLE_REDIRECT_URI,
            scope="openid email profile"
        )

        uri, _ = client.create_authorization_url(
            GOOGLE_AUTHORIZATION_URL,
            state=state,
            access_type="offline",
            prompt="select_account"
        )

        return uri

    @staticmethod
    def get_token_and_user_info(code: str) -> Tuple[dict, dict]:
        """
        Exchange authorization code for tokens and fetch user info.

        Args:
            code: Authorization code from Google callback

        Returns:
            Tuple of (token_data, user_info)

        Raises:
            ValueError: If token exchange or user info fetch fails
        """
        if not GoogleOAuthService.is_configured():
            raise ValueError("Google OAuth not configured")

        client = OAuth2Session(
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            redirect_uri=GOOGLE_REDIRECT_URI
        )

        try:
            # Exchange code for tokens
            token = client.fetch_token(
                GOOGLE_TOKEN_URL,
                code=code,
                grant_type="authorization_code"
            )

            # Fetch user info
            client.token = token
            response = client.get(GOOGLE_USERINFO_URL)
            response.raise_for_status()
            user_info = response.json()

            return token, user_info

        except Exception as e:
            logger.error(f"Google OAuth token exchange failed: {e}")
            raise ValueError(f"Failed to authenticate with Google: {str(e)}")

    @staticmethod
    def create_or_link_user(
        db: Session,
        user_info: dict,
        models_module,
        crud_module
    ) -> Tuple["models_module.User", bool]:
        """
        Create a new user or link existing user to Google account.

        Args:
            db: Database session
            user_info: User info from Google
            models_module: Models module reference
            crud_module: CRUD module reference

        Returns:
            Tuple of (user, is_new_user)
        """
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture")

        if not google_id or not email:
            raise ValueError("Invalid user info from Google")

        # Check if user exists by Google ID
        existing_user = db.query(models_module.User).filter(
            models_module.User.google_id == google_id
        ).first()

        if existing_user:
            logger.info(f"Existing Google user logged in: {email}")
            return existing_user, False

        # Check if user exists by email (link accounts)
        existing_by_email = crud_module.get_user_by_email(db, email=email)

        if existing_by_email:
            # Link Google account to existing user
            existing_by_email.google_id = google_id
            existing_by_email.oauth_provider = "google"
            existing_by_email.email_verified = True  # Google emails are verified
            db.commit()
            logger.info(f"Linked Google account to existing user: {email}")
            return existing_by_email, False

        # Create new user
        new_user = models_module.User(
            email=email,
            full_name=name,
            password_hash="",  # OAuth users don't have password
            google_id=google_id,
            oauth_provider="google",
            email_verified=True,  # Google emails are pre-verified
            role="user"
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"Created new user via Google OAuth: {email}")
        return new_user, True


# Export
__all__ = ['GoogleOAuthService']
