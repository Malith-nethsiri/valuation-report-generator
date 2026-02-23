from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List

from .validators import normalize_date_format, validate_date_format, validate_id_number
from .invoice_schemas import InvoiceData


class PropertyBase(BaseModel):
    """Base schema for Property - contains all property-specific fields"""

    status: Optional[str] = Field("draft", max_length=50)
    property_type: Optional[str] = Field("residential", max_length=50)

    lot_number: Optional[str] = Field(None, max_length=200)
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_date: Optional[str] = Field(None, max_length=50)
    licensed_surveyor_name: Optional[str] = Field(None, max_length=255)
    property_identification_type: Optional[str] = Field(None, max_length=50)
    property_identification_documents: Optional[dict] = None

    has_deed_info: Optional[str] = Field(None, max_length=10)
    deeds: Optional[List[dict]] = None

    assessment_number: Optional[str] = Field(None, max_length=100)
    property_village: Optional[str] = Field(None, max_length=200)
    property_divisional_secretariat: Optional[str] = Field(None, max_length=200)
    property_district: Optional[str] = Field(None, max_length=100)
    property_province: Optional[str] = Field(None, max_length=100)
    property_latitude: Optional[float] = Field(None, ge=-90, le=90)
    property_longitude: Optional[float] = Field(None, ge=-180, le=180)
    property_number: Optional[str] = Field(None, max_length=50)
    grama_niladari_division: Optional[str] = Field(None, max_length=200)
    hathpaththuwa: Optional[str] = Field(None, max_length=300)
    korale: Optional[str] = Field(None, max_length=300)
    pradeshiya_sabha: Optional[str] = Field(None, max_length=200)
    ward_number: Optional[str] = Field(None, max_length=20)
    is_municipal_limit: Optional[bool] = None
    location_direction: Optional[str] = Field(None, max_length=50)

    access_starting_point_name: Optional[str] = None
    access_starting_point_latitude: Optional[float] = Field(None, ge=-90, le=90)
    access_starting_point_longitude: Optional[float] = Field(None, ge=-180, le=180)
    access_route_data: Optional[dict] = None
    access_directions_text: Optional[str] = None
    access_distance_km: Optional[float] = Field(None, ge=0)
    access_duration_minutes: Optional[int] = Field(None, ge=0)
    access_road_type: Optional[str] = Field(None, max_length=200)
    property_road_position: Optional[str] = Field(None, max_length=100)
    location_map_image_data: Optional[str] = None
    access_road_conditions: Optional[List[dict]] = None
    access_entry_mode: Optional[str] = Field(None, max_length=20)
    access_road_classes_detected: Optional[dict] = None

    land_extent_acres: Optional[float] = Field(None, ge=0)
    land_extent_roods: Optional[int] = Field(None, ge=0, le=3)
    land_extent_perches: Optional[float] = Field(None, ge=0)
    land_extent_hectares: Optional[float] = Field(None, ge=0)
    land_extent_square_meters: Optional[float] = Field(None, ge=0)
    land_extent_formatted: Optional[str] = Field(None, max_length=50)
    land_traditional_name: Optional[str] = Field(None, max_length=300)
    boundaries: Optional[dict] = None
    physical_boundaries_types: Optional[List[str]] = None
    physical_boundaries_description: Optional[str] = None
    boundary_types_per_direction: Optional[dict] = None
    entrance_type: Optional[str] = Field(None, max_length=100)
    boundaries_summary_text: Optional[str] = None
    has_multiple_lots: Optional[bool] = None
    lots_data: Optional[List[dict]] = None

    land_shape: Optional[str] = Field(None, max_length=50)
    land_type: Optional[str] = Field(None, max_length=50)
    land_frontage_type: Optional[str] = Field(None, max_length=100)
    land_frontage_width: Optional[float] = None
    land_frontage_description: Optional[str] = None
    land_level: Optional[str] = Field(None, max_length=50)
    land_level_difference: Optional[float] = None
    soil_type: Optional[str] = Field(None, max_length=50)
    water_table_depth: Optional[float] = None
    flood_risk: Optional[str] = Field(None, max_length=50)
    inundation_risk: Optional[str] = Field(None, max_length=50)
    earth_slip_risk: Optional[str] = Field(None, max_length=50)
    land_condition: Optional[str] = Field(None, max_length=50)
    land_condition_description: Optional[str] = None
    land_description_text: Optional[str] = None
    elevation_changes: Optional[str] = Field(None, max_length=50)
    drainage_pattern: Optional[str] = Field(None, max_length=50)
    vegetation_type: Optional[str] = Field(None, max_length=50)
    natural_features: Optional[str] = None

    buildings: Optional[List[dict]] = None
    occupier_name: Optional[str] = Field(None, max_length=300, description="DEPRECATED: Moved to building level")
    occupier_relationship: Optional[str] = Field(None, max_length=50, description="DEPRECATED: Moved to building level")

    property_photos: Optional[List[dict]] = None

    distance_to_major_town_km: Optional[float] = Field(None, ge=0)
    major_town_name: Optional[str] = Field(None, max_length=200)
    nearby_facilities: Optional[List[dict]] = None
    has_electricity: Optional[bool] = None
    water_supply_type: Optional[List[str]] = None
    telecommunication_types: Optional[List[str]] = None
    internet_types: Optional[List[str]] = None
    has_public_transport: Optional[bool] = None
    public_transport_routes: Optional[str] = None
    public_transport_frequency: Optional[str] = Field(None, max_length=200)
    nearest_bus_stop_distance_km: Optional[float] = Field(None, ge=0)
    nearest_bus_stop_name: Optional[str] = Field(None, max_length=200)
    nearest_railway_station: Optional[str] = Field(None, max_length=200)
    nearest_railway_distance_km: Optional[float] = Field(None, ge=0)
    area_type: Optional[str] = Field(None, max_length=50)
    development_level: Optional[str] = Field(None, max_length=50)
    predominant_building_type: Optional[List[str]] = None
    is_tourist_area: Optional[bool] = None
    tourist_attractions_nearby: Optional[str] = None
    locality_description_text: Optional[str] = None

    ownership_type: Optional[str] = Field(None, max_length=200)
    street_lines_status: Optional[str] = Field(None, max_length=200)
    street_lines_gazette_ref: Optional[str] = Field(None, max_length=100)
    street_lines_gazette_date: Optional[str] = Field(None, max_length=20)
    street_lines_impact_description: Optional[str] = None
    building_limits_status: Optional[str] = Field(None, max_length=200)
    building_distance_from_road: Optional[str] = Field(None, max_length=50)
    building_plan_approved: Optional[str] = Field(None, max_length=20)
    building_plan_reference: Optional[str] = Field(None, max_length=200)
    building_approval_authority: Optional[str] = Field(None, max_length=200)
    building_within_limits: Optional[str] = Field(None, max_length=3)
    local_authority_data: Optional[str] = None
    local_authority_rated: Optional[str] = Field(None, max_length=3)
    local_authority_tax_levy: Optional[str] = None
    rent_act_effectiveness: Optional[str] = Field(None, max_length=200)
    title_search_conducted: Optional[str] = Field(None, max_length=3)
    pedigree_search_conducted: Optional[str] = Field(None, max_length=3)
    valuation_basis_note: Optional[str] = None
    property_encumbered: Optional[str] = Field(None, max_length=3)
    encumbrance_type: Optional[str] = Field(None, max_length=100)
    encumbrance_details: Optional[str] = None

    comparable_properties: Optional[List[dict]] = None
    land_market_analysis: Optional[str] = None
    valuation_land_extent: Optional[float] = Field(None, ge=0)
    valuation_rate_per_perch: Optional[float] = Field(None, ge=0)
    valuation_total_land_value: Optional[float] = Field(None, ge=0)
    valuation_buildings_data: Optional[List[dict]] = None
    valuation_total_buildings_value: Optional[float] = Field(None, ge=0)
    valuation_addons: Optional[List[dict]] = None
    valuation_total_addons_value: Optional[float] = Field(None, ge=0)
    valuation_market_value: Optional[float] = Field(None, ge=0)
    valuation_forced_sale_percentage: Optional[float] = Field(None, ge=0, le=100)
    valuation_forced_sale_value: Optional[float] = Field(None, ge=0)
    valuation_insurance_value: Optional[float] = Field(None, ge=0)
    valuation_manual_overrides: Optional[dict] = None

    property_owner_title: Optional[str] = Field(None, max_length=20)
    property_owner_full_name: Optional[str] = Field(None, max_length=500)
    property_owner_id_type: Optional[str] = Field(None, max_length=50)
    property_owner_id_number: Optional[str] = Field(None, max_length=100)
    has_additional_owner: Optional[str] = Field(None, max_length=10)
    additional_owner_names: Optional[str] = None

    inspection_date: Optional[str] = Field(None, max_length=50)

    uploaded_documents: Optional[List[dict]] = None
    field_sources: Optional[dict] = None
    survey_plan_scale: Optional[str] = Field(None, max_length=50)
    plan_reference_notes: Optional[str] = None

    is_template: Optional[bool] = Field(default=False)
    template_name: Optional[str] = Field(None, max_length=200)
    last_valued_date: Optional[str] = Field(None, max_length=50)

    @field_validator('property_latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('property_longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @field_validator('plan_date', 'inspection_date', 'last_valued_date', 'street_lines_gazette_date')
    @classmethod
    def validate_property_dates(cls, v):
        if v is None:
            return v
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(f'Invalid date format: "{v}". Use DD-MM-YYYY format')
        return normalized

    @field_validator('property_owner_id_number')
    @classmethod
    def validate_property_owner_id(cls, v, info):
        if v is None:
            return v
        id_type = info.data.get('property_owner_id_type') if info.data else None
        if id_type:
            is_valid, error_msg = validate_id_number(id_type, v)
            if not is_valid:
                raise ValueError(error_msg)
        return v.strip() if v else v

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


class PropertyCreate(PropertyBase):
    """Schema for creating a new property"""
    pass


class PropertyUpdate(PropertyBase):
    """Schema for updating an existing property"""
    pass


class PropertyStatusUpdate(BaseModel):
    """Schema for updating property status only"""
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['draft', 'completed']:
            raise ValueError("Status must be 'draft' or 'completed'")
        return v


class PropertyResponse(PropertyBase):
    """Schema for property response (includes ID and timestamps)"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PropertyTemplateResponse(BaseModel):
    """Simplified property response for Property Library listing"""
    id: int
    template_name: Optional[str] = None
    property_village: Optional[str] = None
    property_district: Optional[str] = None
    land_extent_formatted: Optional[str] = None
    last_valued_date: Optional[str] = None
    valuation_market_value: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportPropertyBase(BaseModel):
    """Base schema for ReportProperty junction"""
    property_id: int = Field(..., description="ID of the property")
    property_order: int = Field(default=1, ge=1)
    report_specific_notes: Optional[str] = Field(None)
    override_market_value: Optional[float] = Field(None, ge=0)
    override_forced_sale_value: Optional[float] = Field(None, ge=0)


class ReportPropertyCreate(ReportPropertyBase):
    pass


class ReportPropertyUpdate(BaseModel):
    property_order: Optional[int] = Field(None, ge=1)
    report_specific_notes: Optional[str] = None
    override_market_value: Optional[float] = Field(None, ge=0)
    override_forced_sale_value: Optional[float] = Field(None, ge=0)


class ReportPropertyResponse(ReportPropertyBase):
    id: int
    report_id: int
    property: PropertyResponse
    created_at: datetime

    class Config:
        from_attributes = True


class MultiPropertyReportCreate(BaseModel):
    """Schema for creating a multi-property report"""
    report_type: str = Field(default="residential_property")
    status: str = Field(default="draft")

    applicant_title: Optional[str] = None
    applicant_full_name: Optional[str] = None
    applicant_id_type: Optional[str] = None
    applicant_id_number: Optional[str] = None
    applicant_address_line1: Optional[str] = None
    applicant_address_line2: Optional[str] = None
    applicant_district: Optional[str] = None
    applicant_province: Optional[str] = None
    applicant_country: Optional[str] = Field(default="Sri Lanka")

    valuation_type: Optional[str] = None
    valuation_purpose: Optional[str] = None
    property_type_valued: Optional[str] = None

    submission_organization: Optional[str] = None
    submission_address: Optional[str] = None
    submission_recipient_position: Optional[str] = None

    report_reference: Optional[str] = None
    report_date: Optional[str] = None

    has_special_note: Optional[str] = None
    special_note_text: Optional[str] = None

    certification_text: Optional[str] = None
    certification_valuer_name: Optional[str] = None
    certification_valuer_designation: Optional[str] = None
    certification_date: Optional[str] = None
    certificate_identity_confirmed: Optional[bool] = False

    is_multi_property: bool = Field(default=True)
    property_ids: Optional[List[int]] = Field(None)
    properties: Optional[List[PropertyCreate]] = Field(None)
    invoice_data: Optional[InvoiceData] = None


class MultiPropertyReportResponse(BaseModel):
    """Response schema for multi-property reports (includes all associated properties)"""
    id: int
    user_id: int
    report_type: str
    status: str
    is_multi_property: bool
    property_count: int
    total_valuation_amount: Optional[float] = None

    applicant_full_name: Optional[str] = None
    applicant_address_line1: Optional[str] = None
    valuation_type: Optional[str] = None
    valuation_purpose: Optional[str] = None
    submission_organization: Optional[str] = None
    report_reference: Optional[str] = None
    report_date: Optional[str] = None

    properties: List[PropertyResponse] = Field(default_factory=list)
    invoice_data: Optional[InvoiceData] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
