"""
field_categories.py
-------------------
Authoritative mapping of every PropertyDataMixin / Report / Property field
to its data-collection category.

Categories
----------
paper_client   — From documents the CLIENT provides
                 (survey plan, title deed, applicant info, future: email attachments)
paper_official — From GOVERNMENT / AUTHORITY records
                 (gazette, building-plan approval, local-authority registers)
inspection     — From physical ON-SITE observation and measurement
                 (land characteristics, buildings, photos, locality assessment)
computed       — SYSTEM / AI / API generated; not directly entered by a user
                 (AI narratives, extent conversions, Google Maps data, auto-filled
                 certification fields)
valuation      — Professional VALUATION JUDGMENT
                 (comparable properties, rate per perch, final market value, invoice)

Workflow order (Stage 1 → 4):
  paper_client / paper_official  →  inspection  →  computed  →  valuation

Design note
-----------
These categories are intentionally designed so that a future email-parsing AI agent
can populate paper_client fields automatically (client emails documents → agent
extracts data → pre-fills fields via API).  The `field_sources` JSON on each
report/property row stores the per-field source + category + timestamp metadata.
"""

from __future__ import annotations

from typing import Literal

FieldCategory = Literal[
    "paper_client",
    "paper_official",
    "inspection",
    "computed",
    "valuation",
]

# ---------------------------------------------------------------------------
# Authoritative field → category mapping
# ---------------------------------------------------------------------------
FIELD_CATEGORIES: dict[str, FieldCategory] = {

    # ========================================================================
    # [P:C] PAPER-BASED — CLIENT DOCUMENTS
    # Data that comes from documents the client provides (in person, digitally,
    # or via email). Future email-agent will auto-populate these fields.
    # ========================================================================

    # Report context / applicant information
    "applicant_title": "paper_client",
    "applicant_full_name": "paper_client",
    "applicant_id_type": "paper_client",
    "applicant_id_number": "paper_client",
    "applicant_address_line1": "paper_client",
    "applicant_address_line2": "paper_client",
    "applicant_district": "paper_client",
    "applicant_province": "paper_client",
    "applicant_country": "paper_client",
    "applicant_contact_number": "paper_client",
    "request_type": "paper_client",
    "valuation_type": "paper_client",
    "valuation_purpose": "paper_client",
    "property_type_valued": "paper_client",
    "submission_organization": "paper_client",
    "submission_address": "paper_client",
    "submission_recipient_position": "paper_client",
    "has_additional_owner": "paper_client",
    "additional_owner_names": "paper_client",
    "has_special_note": "paper_client",
    "special_note_text": "paper_client",
    "report_reference": "paper_client",
    "report_date": "paper_client",

    # Survey plan / identification
    "property_identification_type": "paper_client",
    "lot_number": "paper_client",
    "plan_number": "paper_client",
    "plan_date": "paper_client",
    "licensed_surveyor_name": "paper_client",
    "survey_plan_scale": "paper_client",
    "plan_reference_notes": "paper_client",

    # Land extent — authoritative source is the licensed surveyor's plan
    "land_extent_acres": "paper_client",
    "land_extent_roods": "paper_client",
    "land_extent_perches": "paper_client",
    "land_traditional_name": "paper_client",
    "lots_data": "paper_client",

    # Deed information
    "has_deed_info": "paper_client",
    "deeds": "paper_client",

    # Legal boundary definition — from survey plan (what the plan says)
    "boundaries": "paper_client",

    # Property village as stated on the plan / submitted by client
    "property_village": "paper_client",

    # ========================================================================
    # [P:O] PAPER-BASED — OFFICIAL GOVERNMENT / AUTHORITY RECORDS
    # Data obtained from gazette publications, municipal registers, local
    # authority offices, rates assessment notices, etc.
    # ========================================================================

    # Assessment / authority records
    "assessment_number": "paper_official",
    "property_number": "paper_official",
    "is_municipal_limit": "paper_official",

    # Administrative divisions (from official administrative division records)
    "property_divisional_secretariat": "paper_official",
    "property_district": "paper_official",
    "property_province": "paper_official",
    "grama_niladari_division": "paper_official",
    "hathpaththuwa": "paper_official",
    "korale": "paper_official",
    "pradeshiya_sabha": "paper_official",
    "ward_number": "paper_official",

    # Legal aspects — all sourced from official records
    "ownership_type": "paper_official",
    "street_lines_status": "paper_official",
    "street_lines_gazette_ref": "paper_official",
    "street_lines_gazette_date": "paper_official",
    "street_lines_impact_description": "paper_official",
    "building_limits_status": "paper_official",
    "local_authority_data": "paper_official",
    "rent_act_effectiveness": "paper_official",
    "title_search_conducted": "paper_official",
    "pedigree_search_conducted": "paper_official",
    "valuation_basis_note": "paper_official",
    "property_encumbered": "paper_official",
    "encumbrance_type": "paper_official",
    "encumbrance_details": "paper_official",
    "building_distance_from_road": "paper_official",
    "building_plan_approved": "paper_official",
    "building_plan_reference": "paper_official",
    "building_approval_authority": "paper_official",
    "building_within_limits": "paper_official",
    "local_authority_rated": "paper_official",
    "local_authority_tax_levy": "paper_official",

    # ========================================================================
    # [I] INSPECTION-BASED
    # Data collected physically during the on-site inspection visit.
    # Includes all observations, measurements, condition assessments, and
    # real-time field inputs.
    # ========================================================================

    # Inspection metadata
    "inspection_date": "inspection",

    # Physical direction / access (observed on-site)
    "location_direction": "inspection",
    "access_starting_point_name": "inspection",
    "access_road_type": "inspection",
    "property_road_position": "inspection",
    "access_road_conditions": "inspection",
    "access_entry_mode": "inspection",

    # Physical boundary state — what actually exists on-site (not what plan says)
    "physical_boundaries_types": "inspection",
    "physical_boundaries_description": "inspection",
    "boundary_types_per_direction": "inspection",
    "entrance_type": "inspection",

    # Land physical characteristics — observed and measured on-site
    "land_shape": "inspection",
    "land_type": "inspection",
    "land_frontage_type": "inspection",
    "land_frontage_width": "inspection",
    "land_frontage_description": "inspection",
    "land_level": "inspection",
    "land_level_difference": "inspection",
    "soil_type": "inspection",
    "water_table_depth": "inspection",
    "flood_risk": "inspection",
    "inundation_risk": "inspection",
    "earth_slip_risk": "inspection",
    "land_condition": "inspection",
    "land_condition_description": "inspection",
    "elevation_changes": "inspection",
    "drainage_pattern": "inspection",
    "vegetation_type": "inspection",
    "natural_features": "inspection",

    # Buildings — entire nested structure observed on-site
    "buildings": "inspection",
    "occupier_name": "inspection",
    "occupier_relationship": "inspection",

    # Property photographs — taken during the site visit
    "property_photos": "inspection",

    # Locality — ALL physically observed / assessed on-site during the visit
    "distance_to_major_town_km": "inspection",
    "major_town_name": "inspection",
    "water_supply_type": "inspection",
    "telecommunication_types": "inspection",
    "internet_types": "inspection",
    "has_public_transport": "inspection",
    "public_transport_routes": "inspection",
    "public_transport_frequency": "inspection",
    "nearest_bus_stop_distance_km": "inspection",
    "nearest_bus_stop_name": "inspection",
    "nearest_railway_station": "inspection",
    "nearest_railway_distance_km": "inspection",
    "area_type": "inspection",
    "development_level": "inspection",
    "predominant_building_type": "inspection",
    "is_tourist_area": "inspection",
    "tourist_attractions_nearby": "inspection",
    "has_electricity": "inspection",
    "has_multiple_lots": "inspection",

    # ========================================================================
    # [CD] COMPUTED / DERIVED
    # Fields generated by the system, AI, or external APIs.
    # Not directly entered by the user — derived from other inputs.
    # ========================================================================

    # AI-generated narrative texts (Claude)
    "land_description_text": "computed",
    "building_description_text": "computed",   # nested in buildings[]
    "locality_description_text": "computed",

    # Extent conversions (extent_calculator.py)
    "land_extent_hectares": "computed",
    "land_extent_square_meters": "computed",
    "land_extent_formatted": "computed",

    # Google Maps / Places API
    "property_latitude": "computed",
    "property_longitude": "computed",
    "access_starting_point_latitude": "computed",
    "access_starting_point_longitude": "computed",
    "access_route_data": "computed",
    "access_directions_text": "computed",
    "access_distance_km": "computed",
    "access_duration_minutes": "computed",
    "location_map_image_data": "computed",
    "access_road_classes_detected": "computed",
    "nearby_facilities": "computed",

    # Auto-generated summary / display texts
    "boundaries_summary_text": "computed",

    # Certification — auto-populated from User profile on report creation
    "certification_text": "computed",
    "certificate_identity_confirmed": "computed",
    "certification_valuer_name": "computed",
    "certification_valuer_designation": "computed",
    "certification_date": "computed",

    # System / metadata fields
    "field_sources": "computed",
    "uploaded_documents": "computed",
    "property_identification_documents": "computed",
    "report_type": "computed",
    "status": "computed",
    "is_multi_property": "computed",
    "property_count": "computed",
    "use_applicant_address_as_property": "computed",
    "invoice_data": "computed",           # totals computed; individual items are user-set

    # ========================================================================
    # [VJ] VALUATION JUDGMENT
    # Professional market analysis — the valuer's expert opinion on value.
    # Neither paper-document input nor on-site observation, but professional
    # analysis performed after inspection.
    # ========================================================================

    "comparable_properties": "valuation",
    "land_market_analysis": "valuation",
    "valuation_land_extent": "valuation",
    "valuation_rate_per_perch": "valuation",
    "valuation_total_land_value": "valuation",
    "valuation_buildings_data": "valuation",
    "valuation_total_buildings_value": "valuation",
    "valuation_addons": "valuation",
    "valuation_total_addons_value": "valuation",
    "valuation_market_value": "valuation",
    "valuation_forced_sale_percentage": "valuation",
    "valuation_forced_sale_value": "valuation",
    "valuation_insurance_value": "valuation",
    "valuation_manual_overrides": "valuation",
    "total_valuation_amount": "valuation",
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_field_category(field_name: str) -> FieldCategory | None:
    """Return the category for *field_name*, or ``None`` if not registered."""
    return FIELD_CATEGORIES.get(field_name)


def get_fields_by_category(category: FieldCategory) -> list[str]:
    """Return all field names that belong to *category*."""
    return [f for f, c in FIELD_CATEGORIES.items() if c == category]


def get_field_source(field_sources: dict, field_name: str) -> str | None:
    """
    Read the ``source`` value from a ``field_sources`` dict entry.

    Handles BOTH the old string format and the new dict format so that
    callers do not need to know which format a given report was saved with.

    Old format:  field_sources["lot_number"] == "ocr"
    New format:  field_sources["lot_number"] == {"source": "ocr", "category": ..., ...}
    """
    val = field_sources.get(field_name)
    if val is None:
        return None
    if isinstance(val, str):
        return val          # legacy format
    if isinstance(val, dict):
        return val.get("source")
    return None


def build_field_source_entry(
    source: str,
    field_name: str,
    confidence: float | None = None,
    timestamp: str | None = None,
) -> dict:
    """
    Build a standardised ``field_sources`` entry for a single field.

    Parameters
    ----------
    source:
        How the value was obtained: ``'ocr'`` | ``'manual'`` | ``'api'`` | ``'computed'``
    field_name:
        The model field name — used to look up the data category automatically.
    confidence:
        0.0–1.0 confidence score; include only for ``'ocr'`` and ``'computed'`` sources.
    timestamp:
        ISO 8601 string.  Defaults to the current UTC time if omitted.

    Returns
    -------
    dict
        Ready to store as ``field_sources[field_name]``.
    """
    from datetime import datetime, timezone

    entry: dict = {
        "source": source,
        "category": get_field_category(field_name) or "computed",
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
    if confidence is not None:
        entry["confidence"] = confidence
    return entry
