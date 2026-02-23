"""
Ownership enforcement tests.

Verifies that every protected endpoint returns 404 (not 403, to avoid
resource enumeration) when a different authenticated user attempts to
access, modify, or delete a resource they do not own.

Pattern mirrors test_bare_land.py::TestOwnershipValidation.

CRITICAL — auth cookie priority:
    get_current_user() checks the HttpOnly `access_token` cookie BEFORE
    the `Authorization` Bearer header.  The TestClient persists cookies
    across requests, so the LAST successful login call sets the active
    identity for all subsequent requests — regardless of any Bearer token
    passed in headers.

    Correct sequence for each test:
        1. _setup_users(db)   — add both users to DB; no login yet
        2. _as_user1(client)  — login → cookie = user1
        3. _create_*(client)  — resource is owned by user1 ✓
        4. _as_user2(client)  — login → cookie = user2
        5. client.get(...)    — cookie = user2 → 404 expected ✓

Coverage:
- Reports   : GET, PUT, DELETE, duplicate, unauthenticated GET/DELETE
- Properties: GET, PUT, DELETE, status-patch, list isolation
- Vehicles  : GET, PUT, DELETE, duplicate, list isolation, unauthenticated GET
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.auth import get_password_hash


# ── Minimal payloads ──────────────────────────────────────────────────────────

REPORT_PAYLOAD = {
    "report_type": "bare_land",
    "status": "draft",
    "applicant_full_name": "Owner User",
    "applicant_address": "10 Owner Street, Colombo",
    "lot_number": "LOT-OWNER",
    "plan_number": "PLAN-OWNER",
    "property_village": "Kadawatha",
    "property_district": "Gampaha",
    "land_extent_acres": 1,
    "buildings": None,
}

PROPERTY_PAYLOAD = {
    "report_type": "bare_land",
    "status": "draft",
    "applicant_full_name": "Owner User",
    "property_village": "Kadawatha",
    "property_district": "Gampaha",
    "land_extent_acres": 1,
    "buildings": None,
}

VEHICLE_PAYLOAD = {
    "status": "draft",
    "vehicle_type": "car",
    "make": "Toyota",
    "model": "Corolla",
    "year_of_manufacture": 2018,
}

_USER1 = {
    "email": "owner_user@example.com",
    "password": "OwnerPass123!",
    "full_name": "Owner User",
}
_USER2 = {
    "email": "attacker_user@example.com",
    "password": "AttackPass123!",
    "full_name": "Attacker User",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_user(db: Session, email: str, password: str, full_name: str) -> models.User:
    """Create and persist a user directly in the test DB (no HTTP, no cookie)."""
    user = models.User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        email_verified=True,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _setup_users(db: Session) -> None:
    """Add both test users to the DB.  Does NOT log in — cookies stay unset."""
    _add_user(db, **_USER1)
    _add_user(db, **_USER2)


def _as_user1(client: TestClient) -> None:
    """Login as user1, setting the auth cookie on the shared TestClient."""
    resp = client.post(
        "/api/auth/login",
        json={"email": _USER1["email"], "password": _USER1["password"]},
    )
    assert resp.status_code == 200, f"Login as user1 failed: {resp.json()}"


def _as_user2(client: TestClient) -> None:
    """Login as user2, replacing the auth cookie on the shared TestClient."""
    resp = client.post(
        "/api/auth/login",
        json={"email": _USER2["email"], "password": _USER2["password"]},
    )
    assert resp.status_code == 200, f"Login as user2 failed: {resp.json()}"


def _create_report(client: TestClient) -> int:
    """Create a report as the currently-logged-in user (cookie-driven)."""
    resp = client.post("/api/reports", json=REPORT_PAYLOAD)
    assert resp.status_code == 201, f"Report creation failed: {resp.json()}"
    return resp.json()["id"]


def _create_property(client: TestClient) -> int:
    """Create a property as the currently-logged-in user (cookie-driven)."""
    resp = client.post("/api/properties", json=PROPERTY_PAYLOAD)
    assert resp.status_code == 201, f"Property creation failed: {resp.json()}"
    return resp.json()["id"]


def _create_vehicle(client: TestClient) -> int:
    """Create a vehicle as the currently-logged-in user (cookie-driven)."""
    resp = client.post("/api/vehicles", json=VEHICLE_PAYLOAD)
    assert resp.status_code == 201, f"Vehicle creation failed: {resp.json()}"
    return resp.json()["id"]


# ── Report ownership tests ────────────────────────────────────────────────────

class TestReportOwnership:
    """Cross-user access to reports must return 404."""

    def test_get_other_users_report_returns_404(
        self, client: TestClient, db: Session
    ):
        """GET /api/reports/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)                    # cookie = user1
        report_id = _create_report(client)   # report.user_id = user1
        _as_user2(client)                    # cookie = user2
        assert client.get(f"/api/reports/{report_id}").status_code == 404

    def test_update_other_users_report_returns_404(
        self, client: TestClient, db: Session
    ):
        """PUT /api/reports/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        report_id = _create_report(client)
        _as_user2(client)
        assert client.put(
            f"/api/reports/{report_id}",
            json={"applicant_full_name": "Attacker"},
        ).status_code == 404

    def test_delete_other_users_report_returns_404(
        self, client: TestClient, db: Session
    ):
        """DELETE /api/reports/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        report_id = _create_report(client)
        _as_user2(client)
        assert client.delete(f"/api/reports/{report_id}").status_code == 404

    def test_duplicate_other_users_report_returns_404(
        self, client: TestClient, db: Session
    ):
        """POST /api/reports/{id}/duplicate by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        report_id = _create_report(client)
        _as_user2(client)
        assert client.post(f"/api/reports/{report_id}/duplicate").status_code == 404

    def test_owner_can_still_access_own_report(
        self, client: TestClient, db: Session
    ):
        """Owner continues to access their own report after another user's failed attempt."""
        _setup_users(db)
        _as_user1(client)
        report_id = _create_report(client)

        _as_user2(client)
        client.get(f"/api/reports/{report_id}")  # attacker's attempt (404)

        _as_user1(client)                        # switch back to owner
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        assert response.json()["id"] == report_id

    def test_unauthenticated_get_report_returns_401(
        self, client: TestClient, db: Session
    ):
        """GET /api/reports/{id} without any auth returns 401."""
        _setup_users(db)
        _as_user1(client)
        report_id = _create_report(client)

        client.cookies.clear()   # remove auth cookie
        assert client.get(f"/api/reports/{report_id}").status_code == 401

    def test_unauthenticated_delete_report_returns_401(
        self, client: TestClient, db: Session
    ):
        """DELETE /api/reports/{id} without any auth returns 401."""
        _setup_users(db)
        _as_user1(client)
        report_id = _create_report(client)

        client.cookies.clear()
        assert client.delete(f"/api/reports/{report_id}").status_code == 401


# ── Property ownership tests ──────────────────────────────────────────────────

class TestPropertyOwnership:
    """Cross-user access to properties must return 404."""

    def test_get_other_users_property_returns_404(
        self, client: TestClient, db: Session
    ):
        """GET /api/properties/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        property_id = _create_property(client)
        _as_user2(client)
        assert client.get(f"/api/properties/{property_id}").status_code == 404

    def test_update_other_users_property_returns_404(
        self, client: TestClient, db: Session
    ):
        """PUT /api/properties/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        property_id = _create_property(client)
        _as_user2(client)
        assert client.put(
            f"/api/properties/{property_id}",
            json={"applicant_full_name": "Attacker"},
        ).status_code == 404

    def test_delete_other_users_property_returns_404(
        self, client: TestClient, db: Session
    ):
        """DELETE /api/properties/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        property_id = _create_property(client)
        _as_user2(client)
        assert client.delete(f"/api/properties/{property_id}").status_code == 404

    def test_patch_status_other_users_property_returns_404(
        self, client: TestClient, db: Session
    ):
        """PATCH /api/properties/{id}/status by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        property_id = _create_property(client)
        _as_user2(client)
        assert client.patch(
            f"/api/properties/{property_id}/status",
            json={"status": "completed"},
        ).status_code == 404

    def test_list_properties_only_shows_own(
        self, client: TestClient, db: Session
    ):
        """GET /api/properties returns only properties owned by the requesting user."""
        _setup_users(db)
        _as_user1(client)
        _create_property(client)   # user1 creates one property

        _as_user2(client)          # switch to user2 (cookie = user2)
        response = client.get("/api/properties")
        assert response.status_code == 200
        assert response.json() == []


# ── Vehicle ownership tests ───────────────────────────────────────────────────

class TestVehicleOwnership:
    """Cross-user access to vehicles must return 404."""

    def test_get_other_users_vehicle_returns_404(
        self, client: TestClient, db: Session
    ):
        """GET /api/vehicles/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        vehicle_id = _create_vehicle(client)
        _as_user2(client)
        assert client.get(f"/api/vehicles/{vehicle_id}").status_code == 404

    def test_update_other_users_vehicle_returns_404(
        self, client: TestClient, db: Session
    ):
        """PUT /api/vehicles/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        vehicle_id = _create_vehicle(client)
        _as_user2(client)
        assert client.put(
            f"/api/vehicles/{vehicle_id}",
            json={"make": "Attacker"},
        ).status_code == 404

    def test_delete_other_users_vehicle_returns_404(
        self, client: TestClient, db: Session
    ):
        """DELETE /api/vehicles/{id} by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        vehicle_id = _create_vehicle(client)
        _as_user2(client)
        assert client.delete(f"/api/vehicles/{vehicle_id}").status_code == 404

    def test_duplicate_other_users_vehicle_returns_404(
        self, client: TestClient, db: Session
    ):
        """POST /api/vehicles/{id}/duplicate by non-owner returns 404."""
        _setup_users(db)
        _as_user1(client)
        vehicle_id = _create_vehicle(client)
        _as_user2(client)
        assert client.post(f"/api/vehicles/{vehicle_id}/duplicate").status_code == 404

    def test_list_vehicles_only_shows_own(
        self, client: TestClient, db: Session
    ):
        """GET /api/vehicles returns only vehicles owned by the requesting user."""
        _setup_users(db)
        _as_user1(client)
        _create_vehicle(client)    # user1 creates one vehicle

        _as_user2(client)          # switch to user2 (cookie = user2)
        response = client.get("/api/vehicles")
        assert response.status_code == 200
        assert response.json() == []

    def test_unauthenticated_get_vehicle_returns_401(
        self, client: TestClient, db: Session
    ):
        """GET /api/vehicles/{id} without any auth returns 401."""
        _setup_users(db)
        _as_user1(client)
        vehicle_id = _create_vehicle(client)

        client.cookies.clear()
        assert client.get(f"/api/vehicles/{vehicle_id}").status_code == 401
