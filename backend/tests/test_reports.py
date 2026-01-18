"""
Tests for report CRUD endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models


class TestCreateReport:
    """Tests for report creation."""

    def test_create_report(self, client: TestClient, auth_headers: dict):
        """Test successful report creation."""
        response = client.post(
            "/api/reports",
            json={
                "report_type": "residential_property",
                "applicant_full_name": "Test Applicant",
                "property_district": "Colombo",
                "property_province": "Western"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "residential_property"
        assert data["applicant_full_name"] == "Test Applicant"
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_report_unauthenticated(self, client: TestClient):
        """Test report creation without authentication fails."""
        response = client.post(
            "/api/reports",
            json={
                "report_type": "residential_property",
                "applicant_full_name": "Test Applicant"
            }
        )

        assert response.status_code == 401


class TestListReports:
    """Tests for listing reports."""

    def test_list_reports(
        self,
        client: TestClient,
        auth_headers: dict,
        test_report: models.Report
    ):
        """Test listing user's reports."""
        response = client.get("/api/reports", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our test report
        report_ids = [r["id"] for r in data]
        assert test_report.id in report_ids

    def test_list_reports_excludes_other_users(
        self,
        client: TestClient,
        auth_headers: dict,
        other_user_report: models.Report
    ):
        """Test that list doesn't include other users' reports."""
        response = client.get("/api/reports", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        report_ids = [r["id"] for r in data]
        assert other_user_report.id not in report_ids


class TestGetReport:
    """Tests for getting a single report."""

    def test_get_report(
        self,
        client: TestClient,
        auth_headers: dict,
        test_report: models.Report
    ):
        """Test getting a specific report."""
        response = client.get(
            f"/api/reports/{test_report.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_report.id
        assert data["applicant_full_name"] == test_report.applicant_full_name

    def test_get_nonexistent_report(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting a non-existent report returns 404."""
        response = client.get("/api/reports/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_get_other_users_report(
        self,
        client: TestClient,
        auth_headers: dict,
        other_user_report: models.Report
    ):
        """Test accessing another user's report fails."""
        response = client.get(
            f"/api/reports/{other_user_report.id}",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateReport:
    """Tests for updating reports."""

    def test_update_report(
        self,
        client: TestClient,
        auth_headers: dict,
        test_report: models.Report
    ):
        """Test updating a report."""
        response = client.put(
            f"/api/reports/{test_report.id}",
            json={
                "applicant_full_name": "Updated Name",
                "property_district": "Gampaha"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["applicant_full_name"] == "Updated Name"
        assert data["property_district"] == "Gampaha"

    def test_update_nonexistent_report(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test updating a non-existent report returns 404."""
        response = client.put(
            "/api/reports/99999",
            json={"applicant_full_name": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_other_users_report(
        self,
        client: TestClient,
        auth_headers: dict,
        other_user_report: models.Report
    ):
        """Test updating another user's report fails."""
        response = client.put(
            f"/api/reports/{other_user_report.id}",
            json={"applicant_full_name": "Hacked Name"},
            headers=auth_headers
        )

        assert response.status_code == 404


class TestDeleteReport:
    """Tests for deleting reports."""

    def test_delete_report(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_user: models.User
    ):
        """Test deleting a report."""
        # Create a report to delete
        report = models.Report(
            user_id=test_user.id,
            report_type="bare_land",
            status="draft"
        )
        db_session.add(report)
        db_session.commit()
        report_id = report.id

        # Delete it
        response = client.delete(
            f"/api/reports/{report_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/reports/{report_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_report(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting a non-existent report returns 404."""
        response = client.delete("/api/reports/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_other_users_report(
        self,
        client: TestClient,
        auth_headers: dict,
        other_user_report: models.Report
    ):
        """Test deleting another user's report fails."""
        response = client.delete(
            f"/api/reports/{other_user_report.id}",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestReportAccessControl:
    """Tests for report access control."""

    def test_user_can_only_access_own_reports(
        self,
        client: TestClient,
        test_user: models.User,
        other_user: models.User,
        test_report: models.Report,
        other_user_report: models.Report,
        auth_headers: dict
    ):
        """Comprehensive test that users can only access their own reports."""
        # Can access own report
        response = client.get(
            f"/api/reports/{test_report.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Cannot access other user's report
        response = client.get(
            f"/api/reports/{other_user_report.id}",
            headers=auth_headers
        )
        assert response.status_code == 404

        # Cannot update other user's report
        response = client.put(
            f"/api/reports/{other_user_report.id}",
            json={"applicant_full_name": "Hacked"},
            headers=auth_headers
        )
        assert response.status_code == 404

        # Cannot delete other user's report
        response = client.delete(
            f"/api/reports/{other_user_report.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
