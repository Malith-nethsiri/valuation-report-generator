"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models


class TestRegister:
    """Tests for user registration."""

    def test_register_success(self, client: TestClient, db_session: Session):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"

    def test_register_duplicate_email(
        self, client: TestClient, test_user: models.User
    ):
        """Test registration with existing email fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
                "full_name": "Duplicate User"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password fails."""
        # Too short
        response = client.post(
            "/api/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "short",
                "full_name": "Weak Pass User"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Invalid Email User"
            }
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    def test_login_success(self, client: TestClient, test_user: models.User):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email

    def test_login_invalid_email(self, client: TestClient):
        """Test login with non-existent email fails."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_password(
        self, client: TestClient, test_user: models.User
    ):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Tests for getting current user."""

    def test_get_current_user(
        self, client: TestClient, test_user: models.User, auth_headers: dict
    ):
        """Test getting current authenticated user."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["id"] == test_user.id

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token fails."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401


class TestTokenExpiration:
    """Tests for token behavior."""

    def test_expired_token(self, client: TestClient, test_user: models.User):
        """Test that expired tokens are rejected."""
        from app.auth import create_access_token
        from datetime import timedelta

        # Create a token that's already expired
        expired_token = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
