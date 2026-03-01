from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict

from .validators import (
    sanitize_dangerous_characters,
    validate_sri_lankan_nic,
    validate_passport,
    validate_date_format,
    normalize_date_format,
    validate_id_number,
)
from .building_schemas import Building, BuildingPhoto, RoadCondition, DeedInfo
from .invoice_schemas import InvoiceData
from ..utils.json_validators import (
    validate_boundaries,
    validate_buildings,
    validate_comparable_properties,
    validate_deeds,
    validate_nearby_facilities,
    validate_property_photos,
    validate_access_road_conditions,
)


# =============================================================================
# FIELD-GROUP SCHEMAS
# Each class maps to a data category in the four-stage valuation workflow.
# See backend/app/utils/field_categories.py for the authoritative field→category map.
#
# Workflow: [P:C]/[P:O] Paper-Based → [I] Inspection → [CD] Computed → [VJ] Valuation Judgment
# =============================================================================


class IdentificationFields(BaseModel):
    """
    Property identification and plan details.
    Category: [P:C] Paper-Based / Client Documents
    All fields come from the licensed surveyor's plan, deed, or certificate of sale.
    Exceptions: uploaded_documents and field_sources are [CD] Computed (system metadata).
    """
    # [P:C] Survey plan fields
    lot_number: Optional[str] = Field(None, max_length=200)
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_date: Optional[str] = Field(None, max_length=50)
    licensed_surveyor_name: Optional[str] = Field(None, max_length=255)
    property_identification_type: Optional[str] = Field(None, max_length=50)
    property_identification_documents: Optional[dict] = Field(None)  # [CD] file metadata
    has_deed_info: Optional[str] = Field(None, max_length=10)
    deeds: Optional[List[DeedInfo]] = Field(None)              # [P:C] deed documents
    has_multiple_lots: Optional[bool] = Field(None)
    lots_data: Optional[List[dict]] = Field(None)
    uploaded_documents: Optional[List[dict]] = Field(None)     # [CD] system tracking
    field_sources: Optional[dict] = Field(None)                # [CD] per-field source tracking
    survey_plan_scale: Optional[str] = Field(None, max_length=50)
    plan_reference_notes: Optional[str] = Field(None)
    land_traditional_name: Optional[str] = Field(None, max_length=300)


class ApplicantFields(BaseModel):
    """
    Applicant and request information.
    Category: [P:C] Paper-Based / Client Documents
    All fields come from the client-provided request letter, application form, or email.
    """
    applicant_title: Optional[str] = Field(None, max_length=20)
    applicant_full_name: Optional[str] = Field(None, max_length=500)
    applicant_id_type: Optional[str] = Field(None, max_length=50)
    applicant_id_number: Optional[str] = Field(None, max_length=100)
    applicant_address_line1: Optional[str] = Field(None, max_length=500)
    applicant_address_line2: Optional[str] = Field(None, max_length=500)
    applicant_district: Optional[str] = Field(None, max_length=100)
    applicant_province: Optional[str] = Field(None, max_length=100)
    applicant_country: Optional[str] = Field(default="Sri Lanka", max_length=100)
    applicant_contact_number: Optional[str] = Field(None, max_length=50)
    request_type: Optional[str] = Field(None, max_length=50)
    has_additional_owner: Optional[str] = Field(None, max_length=10)
    additional_owner_names: Optional[str] = Field(None)
    submission_organization: Optional[str] = Field(None)
    submission_address: Optional[str] = Field(None)
    submission_recipient_position: Optional[str] = Field(None, max_length=200)


class LocationFields(BaseModel):
    """
    Property location, access, and GPS fields.
    Mixed categories:
      [P:O] Official Records: assessment_number, property_number, admin divisions,
             is_municipal_limit
      [I]   Inspection-Based: location_direction, access_starting_point_name,
             access_road_type, property_road_position, access_road_conditions,
             access_entry_mode
      [CD]  Computed: property_lat/lng, access coordinates, route data, distances,
             map image, access_road_classes_detected, use_applicant_address_as_property
    """
    use_applicant_address_as_property: Optional[bool] = Field(None)    # [CD]
    assessment_number: Optional[str] = Field(None, max_length=100)     # [P:O]
    property_village: Optional[str] = Field(None, max_length=200)      # [P:C]
    property_divisional_secretariat: Optional[str] = Field(None, max_length=200)  # [P:O]
    property_district: Optional[str] = Field(None, max_length=100)     # [P:O]
    property_province: Optional[str] = Field(None, max_length=100)     # [P:O]
    property_latitude: Optional[float] = Field(None)                   # [CD] Google Maps
    property_longitude: Optional[float] = Field(None)                  # [CD] Google Maps
    property_number: Optional[str] = Field(None, max_length=50)        # [P:O]
    grama_niladari_division: Optional[str] = Field(None, max_length=200)  # [P:O]
    hathpaththuwa: Optional[str] = Field(None, max_length=300)         # [P:O]
    korale: Optional[str] = Field(None, max_length=300)                # [P:O]
    pradeshiya_sabha: Optional[str] = Field(None, max_length=200)      # [P:O]
    ward_number: Optional[str] = Field(None, max_length=20)            # [P:O]
    is_municipal_limit: Optional[bool] = Field(None)                   # [P:O]
    location_direction: Optional[str] = Field(None, max_length=50)     # [I]
    access_starting_point_name: Optional[str] = Field(None)            # [I]
    access_starting_point_latitude: Optional[float] = Field(None)      # [CD]
    access_starting_point_longitude: Optional[float] = Field(None)     # [CD]
    access_route_data: Optional[dict] = Field(None)                    # [CD] Google Maps
    access_directions_text: Optional[str] = Field(None)                # [CD] Google Directions
    access_distance_km: Optional[float] = Field(None)                  # [CD] Google Maps
    access_duration_minutes: Optional[int] = Field(None)               # [CD] Google Maps
    access_road_type: Optional[str] = Field(None, max_length=200)      # [I]
    property_road_position: Optional[str] = Field(None, max_length=100)  # [I]
    location_map_image_data: Optional[str] = Field(None)               # [CD] Google Maps Static
    access_road_conditions: Optional[List[RoadCondition]] = Field(None)  # [I]
    access_entry_mode: Optional[str] = Field('simple', max_length=20)  # [I]
    access_road_classes_detected: Optional[dict] = Field(None)         # [CD]


class LandFields(BaseModel):
    """
    Land extent, boundaries, and physical characteristics.
    Mixed categories:
      [P:C] Client Documents: land_extent_acres/roods/perches (from survey plan),
             boundaries (legal boundary from survey plan)
      [I]   Inspection-Based: physical_boundaries_types/description, entrance_type,
             boundary_types_per_direction, land_shape, land_type, land_level,
             soil_type, flood_risk, etc. (all physically observed on-site)
      [CD]  Computed: land_extent_hectares/sq_meters/formatted (extent_calculator),
             boundaries_summary_text (auto-generated), land_description_text (AI)
    """
    # [P:C] Land extent from survey plan
    land_extent_acres: Optional[float] = Field(None, ge=0, le=99999.99)
    land_extent_roods: Optional[int] = Field(None, ge=0, le=3)
    land_extent_perches: Optional[float] = Field(None, ge=0, lt=40)
    # [CD] Auto-calculated conversions
    land_extent_hectares: Optional[float] = Field(None, ge=0)
    land_extent_square_meters: Optional[float] = Field(None, ge=0)
    land_extent_formatted: Optional[str] = Field(None, max_length=50)
    # [P:C] Legal boundary from survey plan
    boundaries: Optional[dict] = Field(None)
    # [I] Physical boundary state — what actually exists on-site
    physical_boundaries_types: Optional[List[str]] = Field(None)
    physical_boundaries_description: Optional[str] = Field(None)
    boundary_types_per_direction: Optional[dict] = Field(None)
    entrance_type: Optional[str] = Field(None, max_length=100)
    # [CD] Auto-generated summary
    boundaries_summary_text: Optional[str] = Field(None)
    # [I] Land physical characteristics — all observed on-site
    land_shape: Optional[str] = Field(None, max_length=50)
    land_type: Optional[str] = Field(None, max_length=50)
    land_frontage_type: Optional[str] = Field(None, max_length=100)
    land_frontage_width: Optional[float] = Field(None)
    land_frontage_description: Optional[str] = Field(None)
    land_level: Optional[str] = Field(None, max_length=50)
    land_level_difference: Optional[float] = Field(None)
    soil_type: Optional[str] = Field(None, max_length=50)
    water_table_depth: Optional[float] = Field(None)
    flood_risk: Optional[str] = Field(None, max_length=50)
    inundation_risk: Optional[str] = Field(None, max_length=50)
    earth_slip_risk: Optional[str] = Field(None, max_length=50)
    land_condition: Optional[str] = Field(None, max_length=50)
    land_condition_description: Optional[str] = Field(None)
    # [CD] AI-generated from inspection data
    land_description_text: Optional[str] = Field(None)
    ongoing_construction_notes: Optional[str] = Field(None)  # [I]
    # [I] Topographical features — observed on-site
    elevation_changes: Optional[str] = Field(None, max_length=50)
    drainage_pattern: Optional[str] = Field(None, max_length=50)
    vegetation_type: Optional[str] = Field(None, max_length=50)
    natural_features: Optional[str] = Field(None)


class BuildingFields(BaseModel):
    """
    Building details and occupier information.
    Category: [I] Inspection-Based
    All fields physically observed and recorded during the on-site inspection.
    property_photos are taken during the site visit (also [I]).
    building_description_text (nested in buildings[]) is [CD] AI-generated.
    """
    buildings: Optional[List[Building]] = Field(None)          # [I] All sub-fields observed on-site
    occupier_name: Optional[str] = Field(None, max_length=300)
    occupier_relationship: Optional[str] = Field(None, max_length=50)
    property_photos: Optional[List[BuildingPhoto]] = Field(None, max_items=20)  # [I] taken on-site


class LocalityFields(BaseModel):
    """
    Locality and infrastructure information.
    Category: [I] Inspection-Based (all physically observed/assessed on-site)
    Exception: nearby_facilities is [CD] Computed (Google Places API auto-fetch).
               locality_description_text is [CD] Computed (AI-generated from inspection data).
    """
    distance_to_major_town_km: Optional[float] = Field(None)   # [I]
    major_town_name: Optional[str] = Field(None, max_length=200)  # [I]
    nearby_facilities: Optional[List[dict]] = Field(None)       # [CD] Google Places API
    has_electricity: Optional[bool] = Field(None)               # [I]
    water_supply_type: Optional[List[str]] = Field(None)        # [I]
    telecommunication_types: Optional[List[str]] = Field(None)  # [I]
    internet_types: Optional[List[str]] = Field(None)           # [I]
    has_public_transport: Optional[bool] = Field(None)          # [I]
    public_transport_routes: Optional[str] = Field(None)        # [I]
    public_transport_frequency: Optional[str] = Field(None, max_length=200)  # [I]
    nearest_bus_stop_distance_km: Optional[float] = Field(None)  # [I]
    nearest_bus_stop_name: Optional[str] = Field(None, max_length=200)  # [I]
    nearest_railway_station: Optional[str] = Field(None, max_length=200)  # [I]
    nearest_railway_distance_km: Optional[float] = Field(None)  # [I]
    area_type: Optional[str] = Field(None, max_length=50)       # [I]
    development_level: Optional[str] = Field(None, max_length=50)  # [I]
    predominant_building_type: Optional[List[str]] = Field(None)  # [I]
    is_tourist_area: Optional[bool] = Field(None)               # [I]
    tourist_attractions_nearby: Optional[str] = Field(None)     # [I]
    locality_description_text: Optional[str] = Field(None)      # [CD] AI-generated


class LegalFields(BaseModel):
    """
    Legal aspects and title information.
    Category: [P:O] Paper-Based / Official Records
    All fields are sourced from gazette publications, municipal registers,
    local-authority offices, and official approval documents.
    """
    ownership_type: Optional[str] = Field(None, max_length=200)      # [P:O]
    street_lines_status: Optional[str] = Field(None, max_length=200) # [P:O]
    building_limits_status: Optional[str] = Field(None, max_length=200)  # [P:O]
    local_authority_data: Optional[str] = Field(None)                # [P:O]
    rent_act_effectiveness: Optional[str] = Field(None, max_length=200)  # [P:O]
    title_search_conducted: Optional[str] = Field(None, max_length=3)    # [P:O]
    pedigree_search_conducted: Optional[str] = Field(None, max_length=3) # [P:O]
    valuation_basis_note: Optional[str] = Field(None)                # [P:O]
    property_encumbered: Optional[str] = Field(None, max_length=3)   # [P:O]
    encumbrance_type: Optional[str] = Field(None, max_length=100)    # [P:O]
    encumbrance_details: Optional[str] = Field(None)                 # [P:O]
    street_lines_gazette_ref: Optional[str] = Field(None, max_length=100)  # [P:O]
    street_lines_gazette_date: Optional[str] = Field(None, max_length=20)  # [P:O]
    street_lines_impact_description: Optional[str] = Field(None)     # [P:O]
    building_distance_from_road: Optional[str] = Field(None, max_length=50)  # [P:O]
    building_plan_approved: Optional[str] = Field(None, max_length=20)   # [P:O]
    building_plan_reference: Optional[str] = Field(None, max_length=200) # [P:O]
    building_approval_authority: Optional[str] = Field(None, max_length=200)  # [P:O]
    building_within_limits: Optional[str] = Field(None, max_length=3)   # [P:O]
    local_authority_rated: Optional[str] = Field(None, max_length=3)    # [P:O]
    local_authority_tax_levy: Optional[str] = Field(None)               # [P:O]


class ValuationFields(BaseModel):
    """
    Valuation calculations and comparable properties.
    Category: [VJ] Valuation Judgment
    All fields represent the professional valuer's market analysis and opinion of value.
    This is Stage 4 of the workflow — performed after paper review and on-site inspection.
    """
    comparable_properties: Optional[List[dict]] = Field(None)         # [VJ]
    land_market_analysis: Optional[str] = Field(None)                 # [VJ]
    valuation_land_extent: Optional[float] = Field(None, ge=0)        # [VJ]
    valuation_rate_per_perch: Optional[float] = Field(None, ge=0)     # [VJ]
    valuation_total_land_value: Optional[float] = Field(None, ge=0)   # [VJ]
    valuation_buildings_data: Optional[List[dict]] = Field(None)      # [VJ]
    valuation_total_buildings_value: Optional[float] = Field(None, ge=0)  # [VJ]
    valuation_addons: Optional[List[dict]] = Field(None)              # [VJ]
    valuation_total_addons_value: Optional[float] = Field(None, ge=0) # [VJ]
    valuation_market_value: Optional[float] = Field(None, ge=0)       # [VJ]
    valuation_forced_sale_percentage: Optional[float] = Field(None, ge=0, le=100)  # [VJ]
    valuation_forced_sale_value: Optional[float] = Field(None, ge=0)  # [VJ]
    valuation_insurance_value: Optional[float] = Field(None, ge=0)    # [VJ]
    valuation_manual_overrides: Optional[dict] = Field(None)          # [VJ]


class CertificationFields(BaseModel):
    """
    Certification and invoice data.
    Category: [CD] Computed / Derived
    All certification fields are auto-populated from the User profile on report creation.
    The valuer may edit them, but they are not collected from paper or inspection.
    invoice_data totals are system-computed from user-entered line items.
    """
    certification_text: Optional[str] = Field(None)                   # [CD] pre-filled template
    certificate_identity_confirmed: Optional[bool] = Field(None)      # [CD]
    certification_valuer_name: Optional[str] = Field(None, max_length=255)   # [CD] ← User.full_name
    certification_valuer_designation: Optional[str] = Field(None, max_length=200)  # [CD] ← User.professional_designation
    certification_date: Optional[str] = Field(None, max_length=50)    # [CD] ← report_date / today
    invoice_data: Optional[InvoiceData] = Field(None)                 # [CD]/[VJ] computed totals


class ReportBase(BaseModel):
    report_type: str = Field(default="residential_property", description="Type of report")
    status: str = Field(default="draft", description="Report status (draft, completed)")

    is_multi_property: Optional[bool] = Field(None)
    property_count: Optional[int] = Field(None)

    primary_vehicle_id: Optional[int] = Field(None)
    is_office_use: Optional[bool] = Field(None)
    vehicle_count: Optional[int] = Field(None)
    folio_number: Optional[str] = Field(None, max_length=100)
    inspection_place: Optional[str] = Field(None)

    lot_number: Optional[str] = Field(None, max_length=200)
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_date: Optional[str] = Field(None, max_length=50)
    licensed_surveyor_name: Optional[str] = Field(None, max_length=255)

    property_identification_type: Optional[str] = Field(None, max_length=50)
    property_identification_documents: Optional[dict] = Field(None)

    applicant_title: Optional[str] = Field(None, max_length=20)
    applicant_full_name: Optional[str] = Field(None, max_length=500)
    applicant_id_type: Optional[str] = Field(None, max_length=50)
    applicant_id_number: Optional[str] = Field(None, max_length=100)
    applicant_address_line1: Optional[str] = Field(None, max_length=500)
    applicant_address_line2: Optional[str] = Field(None, max_length=500)
    applicant_district: Optional[str] = Field(None, max_length=100)
    applicant_province: Optional[str] = Field(None, max_length=100)
    applicant_country: Optional[str] = Field(default="Sri Lanka", max_length=100)

    request_type: Optional[str] = Field(None, max_length=50)
    applicant_contact_number: Optional[str] = Field(None, max_length=50)

    valuation_type: Optional[str] = Field(None, max_length=100)
    property_type_valued: Optional[str] = Field(None, max_length=200)
    valuation_purpose: Optional[str] = Field(None, max_length=200)

    has_additional_owner: Optional[str] = Field(None, max_length=10)
    additional_owner_names: Optional[str] = Field(None)

    has_deed_info: Optional[str] = Field(None, max_length=10)
    deeds: Optional[List[DeedInfo]] = Field(None)

    submission_organization: Optional[str] = Field(None)
    submission_address: Optional[str] = Field(None)
    submission_recipient_position: Optional[str] = Field(None, max_length=200)

    inspection_date: Optional[str] = Field(None, max_length=50)

    has_special_note: Optional[str] = Field(None, max_length=10)
    special_note_text: Optional[str] = Field(None)

    report_reference: Optional[str] = Field(None, max_length=100)
    report_date: Optional[str] = Field(None, max_length=50)

    use_applicant_address_as_property: Optional[bool] = Field(None)
    assessment_number: Optional[str] = Field(None, max_length=100)
    property_village: Optional[str] = Field(None, max_length=200)
    property_divisional_secretariat: Optional[str] = Field(None, max_length=200)
    property_district: Optional[str] = Field(None, max_length=100)
    property_province: Optional[str] = Field(None, max_length=100)
    property_latitude: Optional[float] = Field(None)
    property_longitude: Optional[float] = Field(None)

    property_number: Optional[str] = Field(None, max_length=50)
    grama_niladari_division: Optional[str] = Field(None, max_length=200)
    hathpaththuwa: Optional[str] = Field(None, max_length=300)
    korale: Optional[str] = Field(None, max_length=300)
    pradeshiya_sabha: Optional[str] = Field(None, max_length=200)
    ward_number: Optional[str] = Field(None, max_length=20)
    is_municipal_limit: Optional[bool] = Field(None)
    location_direction: Optional[str] = Field(None, max_length=50)

    access_starting_point_name: Optional[str] = Field(None)
    access_starting_point_latitude: Optional[float] = Field(None)
    access_starting_point_longitude: Optional[float] = Field(None)
    access_route_data: Optional[dict] = Field(None)
    access_directions_text: Optional[str] = Field(None)
    access_distance_km: Optional[float] = Field(None)
    access_duration_minutes: Optional[int] = Field(None)
    access_road_type: Optional[str] = Field(None, max_length=200)
    property_road_position: Optional[str] = Field(None, max_length=100)
    location_map_image_data: Optional[str] = Field(None)
    access_road_conditions: Optional[List[RoadCondition]] = Field(None)
    access_entry_mode: Optional[str] = Field('simple', max_length=20)
    access_road_classes_detected: Optional[dict] = Field(None)

    land_extent_acres: Optional[float] = Field(None, ge=0, le=99999.99)
    land_extent_roods: Optional[int] = Field(None, ge=0, le=3)
    land_extent_perches: Optional[float] = Field(None, ge=0, lt=40)
    land_extent_hectares: Optional[float] = Field(None, ge=0)
    land_extent_square_meters: Optional[float] = Field(None, ge=0)
    land_extent_formatted: Optional[str] = Field(None, max_length=50)

    land_traditional_name: Optional[str] = Field(None, max_length=300)

    boundaries: Optional[dict] = Field(None)
    physical_boundaries_types: Optional[List[str]] = Field(None)
    physical_boundaries_description: Optional[str] = Field(None)
    boundary_types_per_direction: Optional[dict] = Field(None)
    entrance_type: Optional[str] = Field(None, max_length=100)
    boundaries_summary_text: Optional[str] = Field(None)

    has_multiple_lots: Optional[bool] = Field(None)
    lots_data: Optional[List[dict]] = Field(None)

    uploaded_documents: Optional[List[dict]] = Field(None)
    field_sources: Optional[dict] = Field(None)

    survey_plan_scale: Optional[str] = Field(None, max_length=50)
    plan_reference_notes: Optional[str] = Field(None)

    land_shape: Optional[str] = Field(None, max_length=50)
    land_type: Optional[str] = Field(None, max_length=50)
    land_frontage_type: Optional[str] = Field(None, max_length=100)
    land_frontage_width: Optional[float] = Field(None)
    land_frontage_description: Optional[str] = Field(None)
    land_level: Optional[str] = Field(None, max_length=50)
    land_level_difference: Optional[float] = Field(None)
    soil_type: Optional[str] = Field(None, max_length=50)
    water_table_depth: Optional[float] = Field(None)
    flood_risk: Optional[str] = Field(None, max_length=50)
    inundation_risk: Optional[str] = Field(None, max_length=50)
    earth_slip_risk: Optional[str] = Field(None, max_length=50)
    land_condition: Optional[str] = Field(None, max_length=50)
    land_condition_description: Optional[str] = Field(None)
    land_description_text: Optional[str] = Field(None)
    ongoing_construction_notes: Optional[str] = Field(None)

    elevation_changes: Optional[str] = Field(None, max_length=50)
    drainage_pattern: Optional[str] = Field(None, max_length=50)
    vegetation_type: Optional[str] = Field(None, max_length=50)
    natural_features: Optional[str] = Field(None)

    buildings: Optional[List[Building]] = Field(None)
    occupier_name: Optional[str] = Field(None, max_length=300, description="DEPRECATED: Moved to building level. Kept for backward compatibility.")
    occupier_relationship: Optional[str] = Field(None, max_length=50, description="DEPRECATED: Moved to building level. Kept for backward compatibility.")

    property_photos: Optional[List[BuildingPhoto]] = Field(None, max_items=20)

    distance_to_major_town_km: Optional[float] = Field(None)
    major_town_name: Optional[str] = Field(None, max_length=200)
    nearby_facilities: Optional[List[dict]] = Field(None)
    has_electricity: Optional[bool] = Field(None)
    water_supply_type: Optional[List[str]] = Field(None)
    telecommunication_types: Optional[List[str]] = Field(None)
    internet_types: Optional[List[str]] = Field(None)
    has_public_transport: Optional[bool] = Field(None)
    public_transport_routes: Optional[str] = Field(None)
    public_transport_frequency: Optional[str] = Field(None, max_length=200)
    nearest_bus_stop_distance_km: Optional[float] = Field(None)
    nearest_bus_stop_name: Optional[str] = Field(None, max_length=200)
    nearest_railway_station: Optional[str] = Field(None, max_length=200)
    nearest_railway_distance_km: Optional[float] = Field(None)
    area_type: Optional[str] = Field(None, max_length=50)
    development_level: Optional[str] = Field(None, max_length=50)
    predominant_building_type: Optional[List[str]] = Field(None)
    is_tourist_area: Optional[bool] = Field(None)
    tourist_attractions_nearby: Optional[str] = Field(None)
    locality_description_text: Optional[str] = Field(None)

    ownership_type: Optional[str] = Field(None, max_length=200)
    street_lines_status: Optional[str] = Field(None, max_length=200)
    building_limits_status: Optional[str] = Field(None, max_length=200)
    local_authority_data: Optional[str] = Field(None)
    rent_act_effectiveness: Optional[str] = Field(None, max_length=200)
    title_search_conducted: Optional[str] = Field(None, max_length=3)
    pedigree_search_conducted: Optional[str] = Field(None, max_length=3)
    valuation_basis_note: Optional[str] = Field(None)
    property_encumbered: Optional[str] = Field(None, max_length=3)
    encumbrance_type: Optional[str] = Field(None, max_length=100)
    encumbrance_details: Optional[str] = Field(None)
    street_lines_gazette_ref: Optional[str] = Field(None, max_length=100)
    street_lines_gazette_date: Optional[str] = Field(None, max_length=20)
    street_lines_impact_description: Optional[str] = Field(None)
    building_distance_from_road: Optional[str] = Field(None, max_length=50)
    building_plan_approved: Optional[str] = Field(None, max_length=20)
    building_plan_reference: Optional[str] = Field(None, max_length=200)
    building_approval_authority: Optional[str] = Field(None, max_length=200)
    building_within_limits: Optional[str] = Field(None, max_length=3)
    local_authority_rated: Optional[str] = Field(None, max_length=3)
    local_authority_tax_levy: Optional[str] = Field(None)

    comparable_properties: Optional[List[dict]] = Field(None)
    land_market_analysis: Optional[str] = Field(None)

    valuation_land_extent: Optional[float] = Field(None, ge=0)
    valuation_rate_per_perch: Optional[float] = Field(None, ge=0)
    valuation_total_land_value: Optional[float] = Field(None, ge=0)
    valuation_buildings_data: Optional[List[dict]] = Field(None)
    valuation_total_buildings_value: Optional[float] = Field(None, ge=0)
    valuation_addons: Optional[List[dict]] = Field(None)
    valuation_total_addons_value: Optional[float] = Field(None, ge=0)
    valuation_market_value: Optional[float] = Field(None, ge=0)
    valuation_forced_sale_percentage: Optional[float] = Field(None, ge=0, le=100)
    valuation_forced_sale_value: Optional[float] = Field(None, ge=0)
    valuation_insurance_value: Optional[float] = Field(None, ge=0)
    valuation_manual_overrides: Optional[dict] = Field(None)

    certification_text: Optional[str] = Field(None)
    certificate_identity_confirmed: Optional[bool] = Field(None)
    certification_valuer_name: Optional[str] = Field(None, max_length=255)
    certification_valuer_designation: Optional[str] = Field(None, max_length=200)
    certification_date: Optional[str] = Field(None, max_length=50)

    invoice_data: Optional[InvoiceData] = Field(None)

    @field_validator('applicant_full_name')
    @classmethod
    def validate_applicant_name(cls, v):
        if v:
            return sanitize_dangerous_characters(v)
        return v

    @field_validator('plan_number')
    @classmethod
    def validate_plan_number(cls, v):
        if v:
            return sanitize_dangerous_characters(v)
        return v

    @field_validator('applicant_id_number')
    @classmethod
    def validate_id_number(cls, v, info):
        if not v:
            return v
        id_type = info.data.get('applicant_id_type', '').lower() if hasattr(info, 'data') else ''
        if not id_type:
            return sanitize_dangerous_characters(v)
        if 'nic' in id_type:
            if not validate_sri_lankan_nic(v):
                raise ValueError('Invalid Sri Lankan NIC format. Use old format (123456789V) or new format (200012345678)')
        elif 'passport' in id_type:
            if not validate_passport(v):
                raise ValueError('Invalid passport format. Must be 6-12 alphanumeric characters (supports international passports)')
        elif 'other' in id_type:
            if len(v.strip()) < 3:
                raise ValueError('ID number must be at least 3 characters')
        return sanitize_dangerous_characters(v)

    @field_validator('valuation_purpose')
    @classmethod
    def validate_valuation_purpose(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError('Purpose of valuation cannot be empty or only whitespace')
            if len(v) > 200:
                raise ValueError('Purpose of valuation must be 200 characters or less')
        return v

    @field_validator('property_latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v is not None:
            if v < -90 or v > 90:
                raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @field_validator('property_longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v is not None:
            if v < -180 or v > 180:
                raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

    @field_validator('access_starting_point_latitude')
    @classmethod
    def validate_access_latitude(cls, v):
        if v is not None:
            if v < -90 or v > 90:
                raise ValueError('Access point latitude must be between -90 and 90 degrees')
        return v

    @field_validator('access_starting_point_longitude')
    @classmethod
    def validate_access_longitude(cls, v):
        if v is not None:
            if v < -180 or v > 180:
                raise ValueError('Access point longitude must be between -180 and 180 degrees')
        return v

    @field_validator('land_extent_acres')
    @classmethod
    def validate_land_acres(cls, v):
        if v is not None and v < 0:
            raise ValueError('Land extent in acres cannot be negative')
        return v

    @field_validator('has_additional_owner', 'has_deed_info', 'has_special_note')
    @classmethod
    def convert_bool_to_string(cls, v):
        if v is None:
            return v
        if isinstance(v, bool):
            return "yes" if v else "no"
        return v

    @field_validator('plan_date', 'inspection_date', 'report_date', 'certification_date')
    @classmethod
    def validate_and_normalize_date(cls, v):
        if v is None:
            return v
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(
                f'Invalid date format: "{v}". Use DD-MM-YYYY format (e.g., 25-12-2023)'
            )
        return normalized

    @field_validator('applicant_id_number')
    @classmethod
    def validate_applicant_id(cls, v, info):
        if v is None:
            return v
        id_type = info.data.get('applicant_id_type') if info.data else None
        if id_type:
            is_valid, error_msg = validate_id_number(id_type, v)
            if not is_valid:
                raise ValueError(error_msg)
        return v.strip() if v else v

    @field_validator('boundaries')
    @classmethod
    def validate_boundaries_json(cls, v):
        if v is not None:
            is_valid, error_msg = validate_boundaries(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('buildings')
    @classmethod
    def validate_buildings_json(cls, v):
        if v is not None:
            buildings_data = [
                b.model_dump() if hasattr(b, 'model_dump') else b
                for b in v
            ] if isinstance(v, list) else v
            if isinstance(buildings_data, list):
                for building in buildings_data:
                    if isinstance(building, dict) and 'floors' in building:
                        for floor in building.get('floors', []):
                            if isinstance(floor, dict) and 'rooms' in floor:
                                for room in floor.get('rooms', []):
                                    if isinstance(room, dict):
                                        room.pop('length', None)
                                        room.pop('width', None)
            is_valid, error_msg = validate_buildings(buildings_data)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('comparable_properties')
    @classmethod
    def validate_comparable_properties_json(cls, v):
        if v is not None:
            is_valid, error_msg = validate_comparable_properties(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('deeds')
    @classmethod
    def validate_deeds_json(cls, v):
        if v is not None:
            is_valid, error_msg = validate_deeds(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('nearby_facilities')
    @classmethod
    def validate_nearby_facilities_json(cls, v):
        if v is not None:
            is_valid, error_msg = validate_nearby_facilities(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('property_photos')
    @classmethod
    def validate_property_photos_json(cls, v):
        if v is not None:
            is_valid, error_msg = validate_property_photos(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('access_road_conditions')
    @classmethod
    def validate_access_road_conditions_json(cls, v):
        if v is not None:
            v_dicts = [item.model_dump() if hasattr(item, 'model_dump') else item for item in v]
            is_valid, error_msg = validate_access_road_conditions(v_dicts)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('water_supply_type')
    @classmethod
    def validate_water_supply_type(cls, v):
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("Maximum 5 water supply types allowed")
        for item in v:
            if not item or len(item) > 50:
                raise ValueError("Invalid water supply type: must be 1-50 characters")
        seen = set()
        unique_values = []
        for item in v:
            normalized = item.strip()
            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                unique_values.append(normalized)
        return unique_values

    @field_validator('predominant_building_type')
    @classmethod
    def validate_predominant_building_type(cls, v):
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("Maximum 5 building types allowed")
        for item in v:
            if not item or len(item) > 50:
                raise ValueError("Invalid building type: must be 1-50 characters")
        seen = set()
        unique_values = []
        for item in v:
            normalized = item.strip()
            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                unique_values.append(normalized)
        return unique_values


class ReportCreate(ReportBase):
    pass


class ReportUpdate(ReportBase):
    pass


class BareLandReportCreate(
    IdentificationFields, ApplicantFields, LocationFields, LandFields,
    LocalityFields, LegalFields, ValuationFields, CertificationFields,
    BaseModel
):
    """Schema for bare land reports - no building fields."""
    report_type: str = Field(default='bare_land')
    status: str = Field(default='draft')
    property_photos: Optional[List[BuildingPhoto]] = Field(None, max_items=20)
    inspection_date: Optional[str] = Field(None, max_length=50)
    has_special_note: Optional[str] = Field(None, max_length=10)
    special_note_text: Optional[str] = Field(None)
    report_reference: Optional[str] = Field(None, max_length=100)
    report_date: Optional[str] = Field(None, max_length=50)
    valuation_type: Optional[str] = Field(None, max_length=100)
    property_type_valued: Optional[str] = Field(None, max_length=200)
    valuation_purpose: Optional[str] = Field(None, max_length=200)


class ResidentialReportCreate(
    IdentificationFields, ApplicantFields, LocationFields, LandFields,
    BuildingFields, LocalityFields, LegalFields, ValuationFields,
    CertificationFields, BaseModel
):
    """Schema for residential property reports - includes building fields."""
    report_type: str = Field(default='residential_property')
    status: str = Field(default='draft')
    inspection_date: Optional[str] = Field(None, max_length=50)
    has_special_note: Optional[str] = Field(None, max_length=10)
    special_note_text: Optional[str] = Field(None)
    report_reference: Optional[str] = Field(None, max_length=100)
    report_date: Optional[str] = Field(None, max_length=50)
    valuation_type: Optional[str] = Field(None, max_length=100)
    property_type_valued: Optional[str] = Field(None, max_length=200)
    valuation_purpose: Optional[str] = Field(None, max_length=200)


class ReportUpdateRequest(ReportBase):
    """
    Schema for report update requests with explicit field whitelisting.
    Prevents injection of internal fields like user_id.
    """
    properties: Optional[List[Dict]] = Field(None)
    property_metadata: Optional[Dict] = Field(None)

    class Config:
        extra = 'forbid'


class ReportResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    report_type: Optional[str] = None
    status: Optional[str] = None
    is_multi_property: Optional[bool] = None
    property_count: Optional[int] = None

    primary_vehicle_id: Optional[int] = None
    is_office_use: Optional[bool] = None
    vehicle_count: Optional[int] = None
    folio_number: Optional[str] = None
    inspection_place: Optional[str] = None

    lot_number: Optional[str] = None
    plan_number: Optional[str] = None
    plan_date: Optional[str] = None
    licensed_surveyor_name: Optional[str] = None
    property_identification_type: Optional[str] = None
    property_identification_documents: Optional[dict] = None
    applicant_title: Optional[str] = None
    applicant_full_name: Optional[str] = None
    applicant_id_type: Optional[str] = None
    applicant_id_number: Optional[str] = None
    applicant_address_line1: Optional[str] = None
    applicant_address_line2: Optional[str] = None
    applicant_district: Optional[str] = None
    applicant_province: Optional[str] = None
    applicant_country: Optional[str] = None
    valuation_type: Optional[str] = None
    property_type_valued: Optional[str] = None
    valuation_purpose: Optional[str] = None
    has_additional_owner: Optional[str] = None
    additional_owner_names: Optional[str] = None
    has_deed_info: Optional[str] = None
    deeds: Optional[List[dict]] = None
    submission_organization: Optional[str] = None
    submission_address: Optional[str] = None
    inspection_date: Optional[str] = None
    has_special_note: Optional[str] = None
    special_note_text: Optional[str] = None
    report_reference: Optional[str] = None
    report_date: Optional[str] = None
    use_applicant_address_as_property: Optional[bool] = None
    assessment_number: Optional[str] = None
    property_village: Optional[str] = None
    property_divisional_secretariat: Optional[str] = None
    property_district: Optional[str] = None
    property_province: Optional[str] = None
    property_latitude: Optional[float] = None
    property_longitude: Optional[float] = None
    property_number: Optional[str] = None
    grama_niladari_division: Optional[str] = None
    hathpaththuwa: Optional[str] = None
    korale: Optional[str] = None
    pradeshiya_sabha: Optional[str] = None
    ward_number: Optional[str] = None
    is_municipal_limit: Optional[bool] = None
    location_direction: Optional[str] = None
    access_starting_point_name: Optional[str] = None
    access_starting_point_latitude: Optional[float] = None
    access_starting_point_longitude: Optional[float] = None
    access_route_data: Optional[dict] = None
    access_directions_text: Optional[str] = None
    access_distance_km: Optional[float] = None
    access_duration_minutes: Optional[int] = None
    access_road_type: Optional[str] = None
    property_road_position: Optional[str] = None
    location_map_image_data: Optional[str] = None
    access_road_conditions: Optional[List[RoadCondition]] = None
    access_entry_mode: Optional[str] = None
    access_road_classes_detected: Optional[dict] = None
    land_extent_acres: Optional[float] = None
    land_extent_roods: Optional[int] = None
    land_extent_perches: Optional[float] = None
    land_extent_hectares: Optional[float] = None
    land_extent_square_meters: Optional[float] = None
    land_extent_formatted: Optional[str] = None
    land_traditional_name: Optional[str] = None
    boundaries: Optional[dict] = None
    physical_boundaries_types: Optional[List[str]] = None
    physical_boundaries_description: Optional[str] = None
    boundary_types_per_direction: Optional[dict] = None
    entrance_type: Optional[str] = None
    boundaries_summary_text: Optional[str] = None
    has_multiple_lots: Optional[bool] = None
    lots_data: Optional[List[dict]] = None
    uploaded_documents: Optional[List[dict]] = None
    field_sources: Optional[dict] = None
    survey_plan_scale: Optional[str] = None
    plan_reference_notes: Optional[str] = None
    land_shape: Optional[str] = None
    land_type: Optional[str] = None
    land_frontage_type: Optional[str] = None
    land_frontage_width: Optional[float] = None
    land_frontage_description: Optional[str] = None
    land_level: Optional[str] = None
    land_level_difference: Optional[float] = None
    soil_type: Optional[str] = None
    water_table_depth: Optional[float] = None
    flood_risk: Optional[str] = None
    inundation_risk: Optional[str] = None
    earth_slip_risk: Optional[str] = None
    land_condition: Optional[str] = None
    land_condition_description: Optional[str] = None
    land_description_text: Optional[str] = None
    ongoing_construction_notes: Optional[str] = None
    elevation_changes: Optional[str] = None
    drainage_pattern: Optional[str] = None
    vegetation_type: Optional[str] = None
    natural_features: Optional[str] = None
    buildings: Optional[List[dict]] = None
    occupier_name: Optional[str] = None
    occupier_relationship: Optional[str] = None
    property_photos: Optional[List[dict]] = None
    distance_to_major_town_km: Optional[float] = None
    major_town_name: Optional[str] = None
    nearby_facilities: Optional[List[dict]] = None
    has_electricity: Optional[bool] = None
    water_supply_type: Optional[List[str]] = None
    telecommunication_types: Optional[List[str]] = None
    internet_types: Optional[List[str]] = None
    has_public_transport: Optional[bool] = None
    public_transport_routes: Optional[List[str]] = None
    public_transport_frequency: Optional[str] = None
    nearest_bus_stop_distance_km: Optional[float] = None
    nearest_bus_stop_name: Optional[str] = None
    nearest_railway_station: Optional[str] = None
    nearest_railway_distance_km: Optional[float] = None
    area_type: Optional[str] = None
    development_level: Optional[str] = None
    predominant_building_type: Optional[List[str]] = None
    is_tourist_area: Optional[bool] = None
    tourist_attractions_nearby: Optional[str] = None
    locality_description_text: Optional[str] = None
    ownership_type: Optional[str] = None
    street_lines_status: Optional[str] = None
    building_limits_status: Optional[str] = None
    local_authority_data: Optional[str] = None
    rent_act_effectiveness: Optional[str] = None
    title_search_conducted: Optional[str] = None
    pedigree_search_conducted: Optional[str] = None
    valuation_basis_note: Optional[str] = None
    property_encumbered: Optional[str] = None
    encumbrance_type: Optional[str] = None
    encumbrance_details: Optional[str] = None
    street_lines_gazette_ref: Optional[str] = None
    street_lines_gazette_date: Optional[str] = None
    street_lines_impact_description: Optional[str] = None
    building_distance_from_road: Optional[str] = None
    building_plan_approved: Optional[str] = None
    building_plan_reference: Optional[str] = None
    building_approval_authority: Optional[str] = None
    building_within_limits: Optional[str] = None
    local_authority_rated: Optional[str] = None
    local_authority_tax_levy: Optional[str] = None
    comparable_properties: Optional[List[dict]] = None
    land_market_analysis: Optional[str] = None
    valuation_land_extent: Optional[float] = None
    valuation_rate_per_perch: Optional[float] = None
    valuation_total_land_value: Optional[float] = None
    valuation_buildings_data: Optional[List[dict]] = None
    valuation_total_buildings_value: Optional[float] = None
    valuation_addons: Optional[List[dict]] = None
    valuation_total_addons_value: Optional[float] = None
    valuation_market_value: Optional[float] = None
    valuation_forced_sale_percentage: Optional[float] = None
    valuation_forced_sale_value: Optional[float] = None
    valuation_insurance_value: Optional[float] = None
    valuation_manual_overrides: Optional[dict] = None
    certification_text: Optional[str] = None
    certificate_identity_confirmed: Optional[bool] = None
    certification_valuer_name: Optional[str] = None
    certification_valuer_designation: Optional[str] = None
    certification_date: Optional[str] = None

    class Config:
        from_attributes = True


class ReportStats(BaseModel):
    """Statistics for report counts"""
    total_count: int = Field(..., description="Total number of reports")
    this_month_count: int = Field(..., description="Reports created this month")
    completed_count: int = Field(..., description="Number of completed reports")
    draft_count: int = Field(..., description="Number of draft reports")


class PaginatedReportResponse(BaseModel):
    """Paginated response for reports with stats"""
    items: List[ReportResponse] = Field(..., description="List of reports for current page")
    total: int = Field(..., description="Total number of matching reports")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    stats: ReportStats = Field(..., description="Report statistics (respects filters)")


class UserDataResponse(ReportResponse):
    """Legacy schema for backward compatibility"""
    pass


class DocxGenerateRequest(BaseModel):
    report_id: int = Field(..., description="ID of the report to generate DOCX for")
