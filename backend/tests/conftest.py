"""
Pytest configuration and fixtures for backend tests.
"""

import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.main import app
from app.database import Base, get_db
from app.auth import get_password_hash, create_access_token
from app import models

# Test database URL (use SQLite for simplicity in tests)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test_database.db"
)


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    # Use SQLite for testing (faster, no external dependencies)
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)

    # Remove SQLite file if exists
    if "sqlite" in TEST_DATABASE_URL:
        db_file = TEST_DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_file):
            os.remove(db_file)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a new session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> models.User:
    """Create a test user."""
    user = models.User(
        email="testuser@example.com",
        password_hash=get_password_hash("TestPass123!"),
        full_name="Test User",
        phone="1234567890"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: models.User) -> str:
    """Create an access token for the test user."""
    from datetime import timedelta
    return create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """Create authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def test_report(db_session: Session, test_user: models.User) -> models.Report:
    """Create a test report."""
    report = models.Report(
        user_id=test_user.id,
        report_type="residential_property",
        status="draft",
        applicant_full_name="Test Applicant",
        property_district="Colombo",
        property_province="Western"
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


@pytest.fixture
def other_user(db_session: Session) -> models.User:
    """Create another test user (for access control tests)."""
    user = models.User(
        email="otheruser@example.com",
        password_hash=get_password_hash("OtherPass123!"),
        full_name="Other User",
        phone="0987654321"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user_report(db_session: Session, other_user: models.User) -> models.Report:
    """Create a report belonging to another user."""
    report = models.Report(
        user_id=other_user.id,
        report_type="residential_property",
        status="draft",
        applicant_full_name="Other Applicant",
        property_district="Galle",
        property_province="Southern"
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report
