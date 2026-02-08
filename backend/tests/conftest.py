"""
Test fixtures for backend authentication tests.

Provides:
- Test database setup/teardown
- FastAPI test client
- Test user creation utilities
- Mock services for email and OAuth
"""

import pytest
from typing import Generator, Dict, Any
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app import models, crud
from app.auth import get_password_hash


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with the test database."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """Standard test user data."""
    return {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "phone": "1234567890"
    }


@pytest.fixture
def test_user(db: Session, test_user_data: Dict[str, Any]) -> models.User:
    """Create a test user in the database."""
    user = models.User(
        email=test_user_data["email"],
        password_hash=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        phone=test_user_data["phone"],
        email_verified=True,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db: Session) -> models.User:
    """Create a test admin user in the database."""
    admin = models.User(
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        email_verified=True,
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(client: TestClient, test_user: models.User, test_user_data: Dict[str, Any]) -> Dict[str, str]:
    """Get authentication headers for a logged-in user."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, test_admin: models.User) -> Dict[str, str]:
    """Get authentication headers for a logged-in admin."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPass123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_email_service():
    """Mock the email service to prevent actual email sending."""
    with patch("app.services.email_service.EmailService") as mock:
        mock.is_configured.return_value = True
        mock.send_email.return_value = True
        mock.send_password_reset_email.return_value = True
        mock.send_verification_email.return_value = True
        mock.send_welcome_email.return_value = True
        yield mock


@pytest.fixture
def mock_google_oauth():
    """Mock Google OAuth service for testing."""
    with patch("app.services.google_oauth_service.GoogleOAuthService") as mock:
        mock.is_configured.return_value = True
        mock.get_authorization_url.return_value = "https://accounts.google.com/o/oauth2/auth?..."
        mock.get_token_and_user_info.return_value = (
            {"access_token": "mock_token"},
            {
                "sub": "google_user_123",
                "email": "googleuser@gmail.com",
                "name": "Google User",
                "picture": "https://example.com/photo.jpg"
            }
        )
        yield mock
