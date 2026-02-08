"""
Bare land report CRUD and narrative tests.

Tests cover:
- Create bare land report (POST, verify buildings=null, status=draft)
- Update bare land report (PUT with modified land fields)
- Submit bare land report (PUT with status=completed)
- Get bare land report (GET by ID)
- Delete bare land report (DELETE)
- Ownership validation (access to another user's report → 403/404)
- Narrative generation (generate_land_narrative with mock Claude client)
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models


# ── Sample bare land payload ──────────────────────────────────────────

BARE_LAND_PAYLOAD = {
    "report_type": "bare_land",
    "status": "draft",
    "applicant_full_name": "John Doe",
    "applicant_address": "123 Test Street, Colombo",
    "lot_number": "LOT-001",
    "plan_number": "PLAN-001",
    "property_village": "Kadawatha",
    "property_district": "Gampaha",
    "land_extent_acres": 0.5,
    "land_shape": "rectangular",
    "land_frontage_ft": 60.0,
    "land_depth_ft": 120.0,
    "land_level": "flat",
    "buildings": None,
    "occupier_name": None,
    "occupier_relationship": None,
    "valuation_buildings_data": None,
    "valuation_total_buildings_value": None,
    "property_photos": [],
}


class TestCreateBareLandReport:
    """Tests for creating bare land reports."""

    def test_create_bare_land_report_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """POST /api/reports with report_type=bare_land creates a draft report."""
        response = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "bare_land"
        assert data["status"] == "draft"
        assert data["buildings"] is None
        assert data["applicant_full_name"] == "John Doe"
        assert data["lot_number"] == "LOT-001"

    def test_create_bare_land_buildings_null(
        self, client: TestClient, auth_headers: dict
    ):
        """Bare land reports must have buildings=null."""
        response = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["buildings"] is None
        assert data["occupier_name"] is None
        assert data["valuation_buildings_data"] is None
        assert data["valuation_total_buildings_value"] is None

    def test_create_bare_land_unauthenticated(self, client: TestClient):
        """Unauthenticated request to create report should fail."""
        response = client.post("/api/reports", json=BARE_LAND_PAYLOAD)
        assert response.status_code == 401


class TestGetBareLandReport:
    """Tests for retrieving bare land reports."""

    def test_get_bare_land_report(
        self, client: TestClient, auth_headers: dict
    ):
        """GET /api/reports/{id} returns the bare land report."""
        # Create first
        create_resp = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=auth_headers,
        )
        report_id = create_resp.json()["id"]

        # Retrieve
        response = client.get(
            f"/api/reports/{report_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["report_type"] == "bare_land"
        assert data["land_extent_acres"] == 0.5

    def test_get_nonexistent_report(
        self, client: TestClient, auth_headers: dict
    ):
        """GET /api/reports/99999 should return 404."""
        response = client.get(
            "/api/reports/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateBareLandReport:
    """Tests for updating bare land reports."""

    def test_update_bare_land_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """PUT /api/reports/{id} updates land fields."""
        create_resp = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=auth_headers,
        )
        report_id = create_resp.json()["id"]

        update_payload = {
            "land_extent_acres": 1.25,
            "land_shape": "irregular",
            "land_frontage_ft": 80.0,
        }

        response = client.put(
            f"/api/reports/{report_id}",
            json=update_payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["land_extent_acres"] == 1.25
        assert data["land_shape"] == "irregular"
        assert data["land_frontage_ft"] == 80.0

    def test_submit_bare_land_report(
        self, client: TestClient, auth_headers: dict
    ):
        """PUT with status=completed marks report as submitted."""
        create_resp = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=auth_headers,
        )
        report_id = create_resp.json()["id"]

        response = client.put(
            f"/api/reports/{report_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"


class TestDeleteBareLandReport:
    """Tests for deleting bare land reports."""

    def test_delete_bare_land_report(
        self, client: TestClient, auth_headers: dict
    ):
        """DELETE /api/reports/{id} removes the report."""
        create_resp = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=auth_headers,
        )
        report_id = create_resp.json()["id"]

        response = client.delete(
            f"/api/reports/{report_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify gone
        get_resp = client.get(
            f"/api/reports/{report_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404


class TestOwnershipValidation:
    """Tests for report ownership enforcement."""

    def test_access_other_users_report(
        self, client: TestClient, db: Session, test_user: models.User, test_user_data: dict
    ):
        """Accessing another user's report should fail."""
        from app.auth import get_password_hash

        # Create a second user
        other_user = models.User(
            email="other@example.com",
            password_hash=get_password_hash("OtherPass123!"),
            full_name="Other User",
            email_verified=True,
            role="user",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Login as first user and create a report
        login_resp = client.post(
            "/api/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )
        headers_user1 = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        create_resp = client.post(
            "/api/reports",
            json=BARE_LAND_PAYLOAD,
            headers=headers_user1,
        )
        report_id = create_resp.json()["id"]

        # Login as second user
        login_resp2 = client.post(
            "/api/auth/login",
            json={"email": "other@example.com", "password": "OtherPass123!"},
        )
        headers_user2 = {"Authorization": f"Bearer {login_resp2.json()['access_token']}"}

        # Second user tries to access the first user's report
        response = client.get(
            f"/api/reports/{report_id}",
            headers=headers_user2,
        )
        assert response.status_code in (403, 404)


class TestLandNarrative:
    """Tests for land narrative generation."""

    @pytest.mark.asyncio
    async def test_generate_land_narrative_calls_client(self):
        """generate_land_narrative should build prompt and call Anthropic."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="The subject land is a rectangular plot...")]

        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(return_value=mock_message)

        with patch(
            "app.services.land_narrative.get_anthropic_client",
            return_value=mock_client,
        ), patch(
            "app.services.land_narrative.is_anthropic_configured",
            return_value=True,
        ):
            from app.services.land_narrative import generate_land_narrative

            result = await generate_land_narrative(
                land_extent="0.5 acres",
                land_shape="rectangular",
                land_level="flat",
                soil_type="loamy",
                frontage_road="Kadawatha Road",
                property_village="Kadawatha",
                property_district="Gampaha",
            )

            assert result is not None
            assert "rectangular" in result.lower() or "plot" in result.lower() or "land" in result.lower()
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_land_narrative_not_configured(self):
        """Returns None when Anthropic is not configured."""
        with patch(
            "app.services.land_narrative.is_anthropic_configured",
            return_value=False,
        ):
            from app.services.land_narrative import generate_land_narrative

            result = await generate_land_narrative(
                land_extent="0.5 acres",
                land_shape="rectangular",
            )

            assert result is None
