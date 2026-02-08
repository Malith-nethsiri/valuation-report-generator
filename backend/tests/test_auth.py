"""
Authentication endpoint tests.

Tests cover:
- Registration (success, duplicate, weak password)
- Login (success, wrong password, nonexistent)
- Token refresh (success, revoked token)
- Logout (success, cookie clearing)
- Password reset (forgot, reset, expired token)
- Email verification (send, verify)
- Google OAuth (callback, user creation)
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.auth import get_password_hash, pwd_context, create_access_token, create_refresh_token


class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, client: TestClient, db: Session):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "full_name": "New User",
                "phone": "9876543210"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"

        # Verify user was created in database
        user = db.query(models.User).filter(
            models.User.email == "newuser@example.com"
        ).first()
        assert user is not None
        assert user.email_verified is False  # New users are not verified

    def test_register_duplicate_email(self, client: TestClient, test_user: models.User):
        """Test registration with already registered email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "password": "StrongPass123!",
                "full_name": "Duplicate User"
            }
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_register_weak_password_no_uppercase(self, client: TestClient):
        """Test registration with password missing uppercase."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "weakpass123!",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422
        assert "uppercase" in response.json()["detail"][0]["msg"].lower()

    def test_register_weak_password_no_special(self, client: TestClient):
        """Test registration with password missing special character."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "WeakPass123",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422
        assert "special" in response.json()["detail"][0]["msg"].lower()

    def test_register_weak_password_too_short(self, client: TestClient):
        """Test registration with password too short."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "Sh0rt!",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422
        assert "8 characters" in response.json()["detail"][0]["msg"]


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client: TestClient, test_user: models.User, test_user_data: dict):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user_data["email"]

    def test_login_wrong_password(self, client: TestClient, test_user: models.User, test_user_data: dict):
        """Test login with incorrect password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_success(self, client: TestClient, test_user: models.User, test_user_data: dict):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, client: TestClient, auth_headers: dict, db: Session):
        """Test successful logout."""
        response = client.post(
            "/api/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify token is blacklisted
        blacklist_count = db.query(models.TokenBlacklist).count()
        assert blacklist_count > 0


class TestPasswordReset:
    """Tests for password reset flow."""

    def test_forgot_password_success(self, client: TestClient, test_user: models.User, db: Session):
        """Test forgot password request."""
        with patch("app.services.email_service.EmailService.send_password_reset_email") as mock_email:
            mock_email.return_value = True

            response = client.post(
                "/api/auth/forgot-password",
                json={"email": test_user.email}
            )

            assert response.status_code == 200
            assert response.json()["success"] is True

            # Verify reset token was generated
            db.refresh(test_user)
            assert test_user.password_reset_token is not None
            assert test_user.password_reset_expires is not None

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test forgot password with nonexistent email (should not reveal)."""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nobody@example.com"}
        )

        # Should return success to not reveal if email exists
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_reset_password_success(self, client: TestClient, test_user: models.User, db: Session):
        """Test password reset with valid token."""
        import secrets

        # Generate and store reset token
        reset_token = secrets.token_urlsafe(32)
        test_user.password_reset_token = pwd_context.hash(reset_token)
        test_user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()

        response = client.post(
            "/api/auth/reset-password",
            json={
                "email": test_user.email,
                "token": reset_token,
                "new_password": "NewStrongPass123!"
            }
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify password was changed
        db.refresh(test_user)
        assert pwd_context.verify("NewStrongPass123!", test_user.password_hash)
        assert test_user.password_reset_token is None

    def test_reset_password_expired_token(self, client: TestClient, test_user: models.User, db: Session):
        """Test password reset with expired token."""
        import secrets

        # Generate and store expired reset token
        reset_token = secrets.token_urlsafe(32)
        test_user.password_reset_token = pwd_context.hash(reset_token)
        test_user.password_reset_expires = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        db.commit()

        response = client.post(
            "/api/auth/reset-password",
            json={
                "email": test_user.email,
                "token": reset_token,
                "new_password": "NewStrongPass123!"
            }
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


class TestEmailVerification:
    """Tests for email verification flow."""

    def test_send_verification_email(self, client: TestClient, db: Session, auth_headers: dict, test_user: models.User):
        """Test sending verification email."""
        # Mark user as unverified
        test_user.email_verified = False
        db.commit()

        with patch("app.services.email_service.EmailService.send_verification_email") as mock_email:
            mock_email.return_value = True

            response = client.post(
                "/api/auth/send-verification",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["email_verified"] is False

    def test_send_verification_already_verified(self, client: TestClient, auth_headers: dict, test_user: models.User):
        """Test sending verification to already verified user."""
        # test_user fixture already has email_verified=True

        response = client.post(
            "/api/auth/send-verification",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email_verified"] is True
        assert "already verified" in data["message"].lower()

    def test_verify_email_success(self, client: TestClient, db: Session, test_user: models.User):
        """Test successful email verification."""
        import secrets

        # Generate and store verification token
        token = secrets.token_urlsafe(32)
        test_user.email_verified = False
        test_user.email_verification_token = pwd_context.hash(token)
        test_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()

        response = client.post(
            "/api/auth/verify-email",
            json={
                "email": test_user.email,
                "token": token
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["email_verified"] is True

        # Verify in database
        db.refresh(test_user)
        assert test_user.email_verified is True
        assert test_user.email_verification_token is None

    def test_verify_email_expired_token(self, client: TestClient, db: Session, test_user: models.User):
        """Test email verification with expired token."""
        import secrets

        # Generate and store expired token
        token = secrets.token_urlsafe(32)
        test_user.email_verified = False
        test_user.email_verification_token = pwd_context.hash(token)
        test_user.email_verification_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()

        response = client.post(
            "/api/auth/verify-email",
            json={
                "email": test_user.email,
                "token": token
            }
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


class TestGoogleOAuth:
    """Tests for Google OAuth flow."""

    def test_google_authorize_not_configured(self, client: TestClient):
        """Test Google auth when not configured."""
        with patch("app.services.google_oauth_service.GoogleOAuthService.is_configured") as mock:
            mock.return_value = False

            response = client.get("/api/auth/google/authorize")

            assert response.status_code == 503

    def test_google_authorize_success(self, client: TestClient):
        """Test getting Google authorization URL."""
        with patch("app.services.google_oauth_service.GoogleOAuthService.is_configured") as mock_config:
            mock_config.return_value = True

            with patch("app.services.google_oauth_service.GoogleOAuthService.get_authorization_url") as mock_url:
                mock_url.return_value = "https://accounts.google.com/o/oauth2/auth?client_id=..."

                response = client.get("/api/auth/google/authorize")

                assert response.status_code == 200
                data = response.json()
                assert "authorization_url" in data
                assert "state" in data
                assert data["authorization_url"].startswith("https://accounts.google.com")

    def test_google_callback_new_user(self, client: TestClient, db: Session):
        """Test Google callback creating new user."""
        with patch("app.services.google_oauth_service.GoogleOAuthService.is_configured") as mock_config:
            mock_config.return_value = True

            with patch("app.services.google_oauth_service.GoogleOAuthService.get_token_and_user_info") as mock_token:
                mock_token.return_value = (
                    {"access_token": "mock_google_token"},
                    {
                        "sub": "google_12345",
                        "email": "newgoogleuser@gmail.com",
                        "name": "New Google User"
                    }
                )

                with patch("app.services.google_oauth_service.GoogleOAuthService.create_or_link_user") as mock_create:
                    new_user = models.User(
                        id=999,
                        email="newgoogleuser@gmail.com",
                        password_hash="",
                        full_name="New Google User",
                        google_id="google_12345",
                        oauth_provider="google",
                        email_verified=True,
                        role="user"
                    )
                    mock_create.return_value = (new_user, True)

                    response = client.post(
                        "/api/auth/google/callback",
                        json={
                            "code": "auth_code_123",
                            "state": "state_token_123"
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "access_token" in data
                    assert data["user"]["email"] == "newgoogleuser@gmail.com"


class TestGetCurrentUser:
    """Tests for getting current user endpoint."""

    def test_get_current_user_authenticated(self, client: TestClient, auth_headers: dict, test_user: models.User):
        """Test getting current user when authenticated."""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user when not authenticated."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401
