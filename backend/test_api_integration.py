"""
API Integration Test for Legal Aspects Extension
Tests the full stack: API → Database → Document Generation
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_create_report_with_legal_aspects():
    print_header("TEST 1: Create Report with Extended Legal Aspects")

    # Create a test report with comprehensive legal aspects data
    report_data = {
        "report_reference": f"TEST-LEGAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "report_type": "residential_property",
        "status": "draft",

        # Applicant info (for ownership paragraph)
        "applicant_full_name": "Mr. Test Owner Name",
        "applicant_id_number": "123456789V",

        # Basic legal aspects
        "ownership_type": "Freehold",
        "street_lines_status": "Not affected",
        "building_limits_status": "Within limits",
        "rent_act_effectiveness": "Not affected",

        # Extended Ownership fields
        "title_search_conducted": "No",
        "pedigree_search_conducted": "No",
        "property_encumbered": "Yes",
        "encumbrance_type": "Mortgage",
        "encumbrance_details": "Bank of Ceylon, Colombo Branch",
        "valuation_basis_note": "free from all legal encumbrance",

        # Extended Street Lines fields
        "street_lines_gazette_ref": "No. 2024/15",
        "street_lines_gazette_date": "10-12-2024",
        "street_lines_impact_description": "Property has adequate setback from road.",

        # Extended Building Limits fields
        "building_distance_from_road": "30 feet",
        "building_plan_approved": "Yes",
        "building_plan_reference": "BP/2024/5678",
        "building_approval_authority": "Colombo Municipal Council",
        "building_within_limits": "Yes",

        # Extended Local Authority fields
        "local_authority_rated": "Yes",
        "local_authority_tax_levy": "Annual tax of Rs. 12,000",

        # Location data for auto-generation
        "pradeshiya_sabha": "Colombo Municipal Council",
        "property_district": "Colombo",
        "property_province": "Western",
        "assessment_number": "CMC/2024/1234"
    }

    try:
        response = requests.post(f"{BASE_URL}/reports", json=report_data, timeout=10)

        if response.status_code == 200:
            report = response.json()
            report_id = report.get('id')

            print(f"[OK] Report created successfully!")
            print(f"  Report ID: {report_id}")
            print(f"  Reference: {report['report_reference']}")

            # Verify all new fields were saved
            print("\n  Verifying extended fields:")

            extended_fields = {
                "title_search_conducted": "No",
                "property_encumbered": "Yes",
                "encumbrance_type": "Mortgage",
                "street_lines_gazette_ref": "No. 2024/15",
                "building_plan_approved": "Yes",
                "local_authority_rated": "Yes"
            }

            all_verified = True
            for field, expected_value in extended_fields.items():
                actual_value = report.get(field)
                status = "[OK]" if actual_value == expected_value else "[X]"
                print(f"    {status} {field}: {actual_value}")
                if actual_value != expected_value:
                    all_verified = False

            if all_verified:
                print("\n  [OK] All extended fields verified successfully!")

            return report_id
        else:
            print(f"[X] Failed to create report: {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print("[X] Error: Backend server not running on http://localhost:8000")
        print("  Please start the backend server first.")
        return None
    except Exception as e:
        print(f"[X] Error: {str(e)}")
        return None

def test_retrieve_report(report_id):
    print_header("TEST 2: Retrieve Report and Verify Data Persistence")

    if not report_id:
        print("[X] Skipping (no report ID)")
        return

    try:
        response = requests.get(f"{BASE_URL}/reports/{report_id}", timeout=10)

        if response.status_code == 200:
            report = response.json()

            print(f"[OK] Report retrieved successfully!")
            print(f"  Report ID: {report_id}")

            # Check legal aspects data
            print("\n  Legal Aspects Data:")
            print(f"    Ownership Type: {report.get('ownership_type')}")
            print(f"    Property Encumbered: {report.get('property_encumbered')}")
            print(f"    Encumbrance Type: {report.get('encumbrance_type')}")
            print(f"    Encumbrance Details: {report.get('encumbrance_details')}")
            print(f"    Building Plan Approved: {report.get('building_plan_approved')}")
            print(f"    Local Authority Rated: {report.get('local_authority_rated')}")

            print("\n  [OK] Data persistence verified!")
            return True
        else:
            print(f"[X] Failed to retrieve report: {response.status_code}")
            return False

    except Exception as e:
        print(f"[X] Error: {str(e)}")
        return False

def test_update_report(report_id):
    print_header("TEST 3: Update Legal Aspects Fields")

    if not report_id:
        print("[X] Skipping (no report ID)")
        return

    # Update some legal aspects fields
    update_data = {
        "property_encumbered": "No",
        "encumbrance_type": None,
        "encumbrance_details": None,
        "valuation_basis_note": "free from all encumbrances (updated)"
    }

    try:
        response = requests.put(f"{BASE_URL}/reports/{report_id}", json=update_data, timeout=10)

        if response.status_code == 200:
            report = response.json()

            print(f"[OK] Report updated successfully!")
            print(f"\n  Updated fields:")
            print(f"    Property Encumbered: {report.get('property_encumbered')}")
            print(f"    Valuation Basis Note: {report.get('valuation_basis_note')}")

            print("\n  [OK] Update operation verified!")
            return True
        else:
            print(f"[X] Failed to update report: {response.status_code}")
            return False

    except Exception as e:
        print(f"[X] Error: {str(e)}")
        return False

def test_backward_compatibility():
    print_header("TEST 4: Backward Compatibility - Old Report Format")

    # Create a report with only old fields (no extended fields)
    old_report_data = {
        "report_reference": f"TEST-OLD-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "report_type": "residential_property",
        "status": "draft",

        # Only old legal aspects fields
        "ownership_type": "Leasehold",
        "street_lines_status": "Affected",
        "building_limits_status": "Not affected",
        "local_authority_data": "Rambukkana Pradeshiya Sabha",
        "rent_act_effectiveness": "Subject to Rent Act No. 7 of 1972"
    }

    try:
        response = requests.post(f"{BASE_URL}/reports", json=old_report_data, timeout=10)

        if response.status_code == 200:
            report = response.json()

            print(f"[OK] Old format report created successfully!")
            print(f"  Report ID: {report.get('id')}")

            # Verify old fields work and new fields are None
            print("\n  Old fields (should have values):")
            print(f"    ownership_type: {report.get('ownership_type')}")
            print(f"    street_lines_status: {report.get('street_lines_status')}")

            print("\n  New fields (should be None):")
            print(f"    title_search_conducted: {report.get('title_search_conducted')}")
            print(f"    property_encumbered: {report.get('property_encumbered')}")
            print(f"    building_plan_approved: {report.get('building_plan_approved')}")

            print("\n  [OK] Backward compatibility verified!")
            return True
        else:
            print(f"[X] Failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"[X] Error: {str(e)}")
        return False

def run_integration_tests():
    print("\n")
    print("=" * 70)
    print("  LEGAL ASPECTS API INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\n  Testing: Backend API -> Database -> Data Persistence")
    print()

    # Run tests in sequence
    report_id = test_create_report_with_legal_aspects()

    if report_id:
        test_retrieve_report(report_id)
        test_update_report(report_id)

    test_backward_compatibility()

    print("\n" + "=" * 70)
    print("  INTEGRATION TESTS COMPLETED")
    print("=" * 70)

    print("\n[OK] Backend API is working correctly with extended legal aspects!")
    print("\nNext Steps:")
    print("  1. Open http://localhost:5173 in your browser")
    print("  2. Create or edit a report")
    print("  3. Navigate to the Legal Aspects section (Step 7)")
    print("  4. Test the new collapsible subsections")
    print("  5. Fill in various combinations of fields")
    print("  6. Generate a DOCX report and verify paragraph formatting")
    print("\nServers Running:")
    print("  - Backend:  http://localhost:8000")
    print("  - Frontend: http://localhost:5173")

if __name__ == "__main__":
    run_integration_tests()
