from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer
from datetime import datetime
from typing import Optional, List
import re
from .utils.json_validators import validate_boundaries, validate_buildings, validate_comparable_properties

# ===== VALIDATION HELPER FUNCTIONS =====

def sanitize_dangerous_characters(value: str) -> str:
    """Remove dangerous characters that could be used for injection attacks"""
    if not value:
        return value
    # Remove <>{}(); characters but preserve unicode
    dangerous_chars = ['<', '>', '{', '}', '(', ')', ';']
    for char in dangerous_chars:
        value = value.replace(char, '')
    return value.strip()

def validate_sri_lankan_nic(value: str) -> bool:
    """Validate Sri Lankan NIC format (old: 9 digits + V/X, new: 12 digits)"""
    if not value:
        return True  # Optional field
    # Old format: 123456789V or 123456789X
    old_pattern = r'^\d{9}[VvXx]$'
    # New format: 200012345678 (12 digits)
    new_pattern = r'^\d{12}$'
    return bool(re.match(old_pattern, value) or re.match(new_pattern, value))

def validate_passport(value: str) -> bool:
    """Validate passport format (alphanumeric, 6-9 characters)"""
    if not value:
        return True  # Optional field
    # Most passports are 6-9 alphanumeric characters
    pattern = r'^[A-Z0-9]{6,9}$'
    return bool(re.match(pattern, value.upper()))

# Authentication Schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    honorific: Optional[str] = Field(None, max_length=10, description="Title/Honorific (e.g., Mr., Mrs., Dr.)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")

    # Professional Credentials
    academic_qualifications: Optional[str] = Field(None, description="Academic qualifications (e.g., B.Sc Estate Management)")
    membership_level: Optional[str] = Field(None, max_length=100, description="Professional membership level (e.g., Fellow Member)")
    membership_number: Optional[str] = Field(None, max_length=100, description="Membership number")
    professional_designation: Optional[str] = Field(None, max_length=200, description="Professional designation (e.g., Chartered Valuer)")
    panel_valuer_banks: Optional[List[str]] = Field(None, description="List of banks where appointed as panel valuer")

    # Residential Address (structured for report formatting)
    house_number: Optional[str] = Field(None, max_length=50, description="House number (e.g., No:43)")
    area_development: Optional[str] = Field(None, max_length=100, description="Area/Development name (e.g., Highway City)")
    village: Optional[str] = Field(None, max_length=100, description="Village name")
    locality: Optional[str] = Field(None, max_length=100, description="Locality name")
    phone_primary: Optional[str] = Field(None, max_length=50, description="Primary phone number")
    phone_secondary: Optional[str] = Field(None, max_length=50, description="Secondary phone number")

    # Office Information (optional)
    office_department: Optional[str] = Field(None, max_length=200, description="Office department")
    office_region: Optional[str] = Field(None, max_length=100, description="Office region/province")
    office_street_city: Optional[str] = Field(None, max_length=200, description="Office street and city")
    office_phone: Optional[str] = Field(None, max_length=50, description="Office phone number")

    # Letterhead template preference
    preferred_letterhead_template: Optional[str] = Field(None, max_length=50, description="Preferred letterhead template ID (e.g., 'classic', 'modern')")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters, must include uppercase, lowercase, digit, and special character)")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength requirements"""
        from .auth import validate_password_strength

        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    honorific: Optional[str] = Field(None, max_length=10, description="Title/Honorific (e.g., Mr., Mrs., Dr.)")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")

    # Professional Credentials
    academic_qualifications: Optional[str] = Field(None, description="Academic qualifications (e.g., B.Sc Estate Management)")
    membership_level: Optional[str] = Field(None, max_length=100, description="Professional membership level (e.g., Fellow Member)")
    membership_number: Optional[str] = Field(None, max_length=100, description="Membership number")
    professional_designation: Optional[str] = Field(None, max_length=200, description="Professional designation (e.g., Chartered Valuer)")
    panel_valuer_banks: Optional[List[str]] = Field(None, description="List of banks where appointed as panel valuer")

    # Residential Address (structured for report formatting)
    house_number: Optional[str] = Field(None, max_length=50, description="House number (e.g., No:43)")
    area_development: Optional[str] = Field(None, max_length=100, description="Area/Development name (e.g., Highway City)")
    village: Optional[str] = Field(None, max_length=100, description="Village name")
    locality: Optional[str] = Field(None, max_length=100, description="Locality name")
    phone_primary: Optional[str] = Field(None, max_length=50, description="Primary phone number")
    phone_secondary: Optional[str] = Field(None, max_length=50, description="Secondary phone number")

    # Office Information (optional)
    office_department: Optional[str] = Field(None, max_length=200, description="Office department")
    office_region: Optional[str] = Field(None, max_length=100, description="Office region/province")
    office_street_city: Optional[str] = Field(None, max_length=200, description="Office street and city")
    office_phone: Optional[str] = Field(None, max_length=50, description="Office phone number")

    # Letterhead template preference
    preferred_letterhead_template: Optional[str] = Field(None, max_length=50, description="Preferred letterhead template ID (e.g., 'classic', 'modern')")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Deed Information Schema
class DeedInfo(BaseModel):
    deed_type: str = Field(..., description="Type of deed (Gift deed, Transfer deed, etc.)")
    deed_number: str = Field(..., description="Deed number")
    deed_date: str = Field(..., description="Deed date (DD-MM-YYYY)")
    notary_name: Optional[str] = Field(None, description="Notary name")
    notary_location: Optional[str] = Field(None, description="Notary location")

# Access and Road Condition Schemas
class RoadCondition(BaseModel):
    """Road condition information for access routes"""
    road_type: str = Field(..., pattern="^(paved_road|concrete_road|carpet_road|gravel_road|sand_road|earth_road)$", description="Type of road surface")
    condition: str = Field(..., pattern="^(excellent|good|fair|poor)$", description="Road surface condition")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance of this road type in kilometers (optional)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about this road segment")

# Building-Related Schemas

# NEW: Enhanced Construction Material Details
class RoofDetails(BaseModel):
    structure_type: Optional[str] = Field(None, max_length=100, description="Roof structure type (timber_frame, steel_trusses, concrete_slab, rcc_flat, prefab_trusses, mixed)")
    covering_material: Optional[List[str]] = Field(None, description="Roof covering materials - multiple selections allowed (asbestos_sheets, clay_tiles, concrete_tiles, metal_sheets, concrete_flat, cadjans, shingles)")
    additional_details: Optional[str] = Field(None, max_length=500, description="Additional roof details (optional freeform text)")

class WallDetails(BaseModel):
    material: Optional[str] = Field(None, max_length=100, description="Wall material type (brick_masonry, cement_block, stone_masonry, rcc_frame, rubble_masonry, mud_walls, timber_frame, cadjan, prefab_panels, mixed)")
    finish: Optional[List[str]] = Field(None, description="Wall finish types - multiple selections allowed (cement_plaster_painted, lime_plaster, tiles, exposed_brick, color_washed, textured, unfinished)")

    # REMOVED: Wall thickness field (not needed for reports)

class FloorDetails(BaseModel):
    material: Optional[List[str]] = Field(None, description="Floor materials - multiple selections allowed (cement, tiled, terrazzo, timber, granite, marble, vinyl, polished_concrete, earth)")
    finish_quality: Optional[str] = Field(None, max_length=50, description="Floor finish quality (basic, standard, premium)")

class DoorsWindowsDetails(BaseModel):
    window_frame_material: Optional[List[str]] = Field(None, description="Window frame materials - multiple selections (timber, aluminum, upvc, steel)")
    window_glass_type: Optional[List[str]] = Field(None, description="Window glass types - multiple selections (clear, tinted, frosted, double_glazing)")
    window_security: Optional[List[str]] = Field(None, description="Window security features - multiple selections (burglar_bars, grills, security_mesh)")
    main_door_material: Optional[str] = Field(None, max_length=100, description="Main door material (solid_timber, panel_door, metal, upvc, glass)")
    internal_door_material: Optional[str] = Field(None, max_length=100, description="Internal door material (timber, flush_doors, panel_doors, hollow_core)")
    door_security: Optional[List[str]] = Field(None, description="Door security features - multiple selections (deadbolt, security_locks, door_chain, multi_point)")

class AccommodationSummary(BaseModel):
    bedrooms: int = Field(default=0, ge=0, description="Number of bedrooms")
    bathrooms: int = Field(default=0, ge=0, description="Number of bathrooms")
    living_rooms: int = Field(default=0, ge=0, description="Number of living rooms")
    dining_rooms: int = Field(default=0, ge=0, description="Number of dining rooms")
    kitchens: int = Field(default=0, ge=0, description="Number of kitchens")
    pantries: int = Field(default=0, ge=0, description="Number of pantries")
    verandahs: int = Field(default=0, ge=0, description="Number of verandahs")
    balconies: int = Field(default=0, ge=0, description="Number of balconies")
    garages: int = Field(default=0, ge=0, description="Number of garages/car porches")
    store_rooms: int = Field(default=0, ge=0, description="Number of store rooms")
    other_rooms: int = Field(default=0, ge=0, description="Number of other rooms")

# Legacy schema (kept for backward compatibility)
class WallConstruction(BaseModel):
    material: Optional[str] = Field(None, max_length=100, description="Wall material type (DEPRECATED - use WallDetails)")
    thickness: Optional[str] = Field(None, max_length=50, description="Wall thickness (DEPRECATED - use WallDetails)")
    finish: Optional[str] = Field(None, max_length=100, description="Wall finish type (DEPRECATED - use WallDetails)")

class ConstructionMaterials(BaseModel):
    # NEW: Enhanced construction details
    roof_details: Optional[RoofDetails] = Field(None, description="Detailed roof construction information")
    wall_details: Optional[WallDetails] = Field(None, description="Detailed wall construction information")
    floor_details: Optional[FloorDetails] = Field(None, description="Detailed floor construction information")
    ceiling_type: Optional[str] = Field(None, max_length=100, description="Ceiling type")
    doors_windows_details: Optional[DoorsWindowsDetails] = Field(None, description="Doors and windows information")

    # DEPRECATED: Legacy fields kept for backward compatibility
    foundation_type: Optional[str] = Field(None, max_length=100, description="Foundation type (DEPRECATED - no longer collected)")
    wall_construction: Optional[WallConstruction] = Field(None, description="Wall construction details (DEPRECATED - use wall_details)")
    roof_structure: Optional[str] = Field(None, max_length=100, description="Roof structure type (DEPRECATED - use roof_details)")

class Electricity(BaseModel):
    source: Optional[str] = Field(None, max_length=50, description="Electricity source")
    three_phase: Optional[bool] = Field(None, description="Whether three-phase electricity")
    solar_panels: Optional[bool] = Field(None, description="Whether solar panels installed")

class Parking(BaseModel):
    covered_spaces: Optional[int] = Field(None, ge=0, description="Number of covered parking spaces")
    uncovered_spaces: Optional[int] = Field(None, ge=0, description="Number of uncovered parking spaces")

class UtilitiesServices(BaseModel):
    water_supply: Optional[str] = Field(None, max_length=100, description="Water supply type")
    sewage: Optional[str] = Field(None, max_length=100, description="Sewage system type")
    electricity: Optional[Electricity] = Field(None, description="Electricity details")
    parking: Optional[Parking] = Field(None, description="Parking facilities")

class Room(BaseModel):
    room_type: str = Field(..., description="Room type (Bedroom, Bathroom, Attached Bathroom, Living Room, etc.)")
    count: int = Field(default=1, ge=1, description="Number of rooms of this type")
    has_attached_bathroom: Optional[bool] = Field(None, description="Whether room has attached bathroom")

class Floor(BaseModel):
    floor_name: str = Field(..., description="Floor name (e.g., 'Ground Floor')")
    floor_area: Optional[float] = Field(None, ge=0, description="Floor area in square feet")
    rooms: List[Room] = Field(default_factory=list, description="Rooms on this floor")
    accommodation_summary: Optional[AccommodationSummary] = Field(None, description="Auto-calculated accommodation summary (room counts by type)")

class BuildingPhoto(BaseModel):
    id: str = Field(..., description="Photo ID")
    image_data: str = Field(..., description="Base64 encoded image data")
    caption: Optional[str] = Field(None, description="Photo caption")
    order: int = Field(..., ge=0, description="Display order")

class Building(BaseModel):
    id: str = Field(..., description="Building ID")
    building_name: Optional[str] = Field(None, max_length=200, description="Building name")
    building_type: str = Field(..., max_length=100, description="Building type (residential, commercial, etc.)")
    stories: Optional[int] = Field(None, ge=1, description="Number of stories")
    age_description: Optional[str] = Field(None, max_length=200, description="Age description")
    condition: Optional[str] = Field(None, max_length=50, description="Building condition")
    roof_types: List[str] = Field(default_factory=list, description="Roof types")
    roof_description: Optional[str] = Field(None, description="Roof description")
    wall_types: List[str] = Field(default_factory=list, description="Wall types")
    wall_description: Optional[str] = Field(None, description="Wall description")
    floor_types: List[str] = Field(default_factory=list, description="Floor types")
    floor_description: Optional[str] = Field(None, description="Floor description")
    total_floor_area: Optional[float] = Field(None, ge=0, description="Total floor area in square feet")
    floors: List[Floor] = Field(default_factory=list, description="Building floors")
    construction_materials: Optional[ConstructionMaterials] = Field(None, description="Construction materials details")
    utilities_services: Optional[UtilitiesServices] = Field(None, description="Utilities and services")
    conveniences: List[str] = Field(default_factory=list, description="Building conveniences")
    building_description_text: Optional[str] = Field(None, description="Auto-generated building description")
    building_photos: List[BuildingPhoto] = Field(default_factory=list, max_items=5, description="Building photos (max 5)")
    additional_structures_description: Optional[str] = Field(None, max_length=2000, description="Description of additional/separate structures (store rooms, garages, outbuildings)")

# Report Schemas
class ReportBase(BaseModel):
    report_type: str = Field(default="residential_property", description="Type of report")
    status: str = Field(default="draft", description="Report status (draft, completed)")

    # Property & Plan Information
    property_lot_description: Optional[str] = Field(None, max_length=200, description="Lot description (e.g., Lot 15)")
    plan_number: Optional[str] = Field(None, max_length=100, description="Plan number")
    plan_date: Optional[str] = Field(None, max_length=50, description="Plan date (DD-MM-YYYY)")
    licensed_surveyor_name: Optional[str] = Field(None, max_length=255, description="Licensed surveyor name")

    # Property Identification Type - UPDATED: Now supports hybrid mode
    property_identification_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of property identification: 'plan', 'deed', 'plan_and_deed', 'certificate_of_sale'"
    )

    # Property Identification Documents Metadata - NEW: Track which documents are present
    property_identification_documents: Optional[dict] = Field(
        None,
        description="Document availability metadata: {has_plan: bool, has_deed: bool, has_certificate: bool, primary_type: str}"
    )

    # Applicant Information
    applicant_title: Optional[str] = Field(None, max_length=20, description="Title (Mr./Mrs./Miss./Dr.)")
    applicant_full_name: Optional[str] = Field(None, max_length=500, description="Applicant full name")
    applicant_id_type: Optional[str] = Field(None, max_length=50, description="ID type (Passport/NIC/Other)")
    applicant_id_number: Optional[str] = Field(None, max_length=100, description="ID number")
    applicant_address_line1: Optional[str] = Field(None, max_length=500, description="Address line 1 (house/plot, street)")
    applicant_address_line2: Optional[str] = Field(None, max_length=500, description="Address line 2 (village/area)")
    applicant_district: Optional[str] = Field(None, max_length=100, description="District")
    applicant_province: Optional[str] = Field(None, max_length=100, description="Province")
    applicant_country: Optional[str] = Field(default="Sri Lanka", max_length=100, description="Country")

    # Valuation Purpose
    valuation_type: Optional[str] = Field(None, max_length=100, description="Type of valuation (Market Value, etc.)")
    property_ownership: Optional[str] = Field(None, max_length=200, description="Property ownership description")
    property_type_valued: Optional[str] = Field(None, max_length=200, description="Type of property being valued")

    # Valuation Purpose (new)
    valuation_purpose: Optional[str] = Field(
        None,
        max_length=200,
        description="Purpose of the valuation report"
    )

    # Additional Property Owner (optional)
    has_additional_owner: Optional[str] = Field(None, max_length=10, description="Has additional owner (yes/no)")
    additional_owner_names: Optional[str] = Field(None, description="Additional owner names")

    # Deed Information
    has_deed_info: Optional[str] = Field(None, max_length=10, description="Has deed information (yes/no)")
    deeds: Optional[List[DeedInfo]] = Field(None, description="List of deed information")

    # Submission Destination
    submission_organization: Optional[str] = Field(None, description="Organization to submit report to")
    submission_address: Optional[str] = Field(None, description="Submission address")
    submission_recipient_position: Optional[str] = Field(None, max_length=200, description="Recipient position (e.g., Manager, Credit Officer)")

    # Date of Inspection
    inspection_date: Optional[str] = Field(None, max_length=50, description="Inspection date (DD-MM-YYYY)")

    # Special Notes (optional)
    has_special_note: Optional[str] = Field(None, max_length=10, description="Has special note (yes/no)")
    special_note_text: Optional[str] = Field(None, description="Special note text")

    # Report metadata (keeping for compatibility)
    report_reference: Optional[str] = Field(None, max_length=100, description="Report reference number")
    report_date: Optional[str] = Field(None, max_length=50, description="Report date")

    # ===== PROPERTY LOCATION & ACCESS (Phase 2) =====

    # Property Location Information
    use_applicant_address_as_property: Optional[bool] = Field(None, description="Use applicant address as property location")
    property_name: Optional[str] = Field(None, max_length=200, description="Property name (optional)")
    assessment_number: Optional[str] = Field(None, max_length=100, description="Assessment number (optional)")
    property_village: Optional[str] = Field(None, max_length=200, description="Village name")
    property_divisional_secretariat: Optional[str] = Field(None, max_length=200, description="Divisional Secretariat division")
    property_district: Optional[str] = Field(None, max_length=100, description="District")
    property_province: Optional[str] = Field(None, max_length=100, description="Province")
    property_latitude: Optional[float] = Field(None, description="Property GPS latitude")
    property_longitude: Optional[float] = Field(None, description="Property GPS longitude")

    # Sri Lankan Administrative Subdivisions (Phase 2 - Enhancement)
    property_number: Optional[str] = Field(None, max_length=50, description="Property number within village (e.g., No: 1202, No:717)")
    grama_niladari_division: Optional[str] = Field(None, max_length=200, description="Grama Niladari Division (smallest admin unit)")
    korale: Optional[str] = Field(None, max_length=300, description="Korale (traditional administrative division)")
    pradeshiya_sabha: Optional[str] = Field(None, max_length=200, description="Pradeshiya Sabha (if applicable)")
    ward_number: Optional[str] = Field(None, max_length=20, description="Ward number (for urban/municipal areas)")
    is_municipal_limit: Optional[bool] = Field(None, description="Property within Municipal Council limit")
    location_direction: Optional[str] = Field(None, max_length=50, description="Direction from town center (e.g., north-east, south-west, west)")

    # Access Directions Information
    access_starting_point_name: Optional[str] = Field(None, description="Starting landmark name")
    access_starting_point_latitude: Optional[float] = Field(None, description="Starting point GPS latitude")
    access_starting_point_longitude: Optional[float] = Field(None, description="Starting point GPS longitude")
    access_route_data: Optional[dict] = Field(None, description="Raw Google Directions API response")
    access_directions_text: Optional[str] = Field(None, description="Editable professional directions text")
    access_distance_km: Optional[float] = Field(None, description="Route distance in kilometers")
    access_duration_minutes: Optional[int] = Field(None, description="Estimated travel time in minutes")
    access_road_type: Optional[str] = Field(None, max_length=200, description="Road type description")
    property_road_position: Optional[str] = Field(None, max_length=100, description="Position relative to road")
    location_map_image_data: Optional[str] = Field(None, description="Static map image URL or base64 data")
    access_road_segments: Optional[dict] = Field(None, description="DEPRECATED: Detailed road segment information (kept for backward compatibility)")
    access_road_conditions: Optional[List[RoadCondition]] = Field(None, description="Road conditions array with road type, condition, optional distance, and notes")
    access_entry_mode: Optional[str] = Field('simple', max_length=20, description="Entry mode for road conditions: 'simple' or 'advanced'")
    access_road_classes_detected: Optional[dict] = Field(None, description="Auto-detected road classifications for analytics (backend only, not shown in output)")

    # ===== PROPERTY HEADER FIELDS (Land Extent, Boundaries, Physical Features) =====

    # Land Extent (Acres-Roods-Perches format)
    land_extent_acres: Optional[float] = Field(None, ge=0, le=99999.99, description="Land extent in acres (0-99999.99)")
    land_extent_roods: Optional[int] = Field(None, ge=0, le=3, description="Land extent in roods (0-3, where 1 acre = 4 roods)")
    land_extent_perches: Optional[float] = Field(None, ge=0, lt=40, description="Land extent in perches (0-39.99, where 1 rood = 40 perches)")
    land_extent_hectares: Optional[float] = Field(None, ge=0, description="Land extent in hectares (auto-calculated)")
    land_extent_square_meters: Optional[float] = Field(None, ge=0, description="Land extent in square meters (auto-calculated)")
    land_extent_formatted: Optional[str] = Field(None, max_length=50, description="Formatted extent string (e.g., '00A-0R-13.8P')")

    # Traditional/Historical Land Name
    land_traditional_name: Optional[str] = Field(None, max_length=300, description="Traditional or historical name of the land (e.g., 'Hakuruketiyawe Wela alias...')")

    # Boundary Information (Hybrid: structured + free text)
    # Structure: {"north": {"description": "...", "length": "...", "adjoins": "...", "notes": "..."}, "south": {...}, "east": {...}, "west": {...}}
    boundaries: Optional[dict] = Field(None, description="Boundary information for all four directions (JSON)")

    # Physical Boundaries
    physical_boundaries_types: Optional[List[str]] = Field(None, description="Types of physical boundaries (e.g., ['brick_walls', 'barbed_wire', 'live_fence'])")
    physical_boundaries_description: Optional[str] = Field(None, description="Detailed description of physical boundaries")

    # Boundary Types Per Direction (for professional summary generation)
    boundary_types_per_direction: Optional[dict] = Field(None, description="Boundary type for each direction (JSON: {'north': 'brick_walls', ...})")

    # Entrance/Gate Type
    entrance_type: Optional[str] = Field(None, max_length=100, description="Type of entrance/gate (auto_roller_gate, iron_gate, wooden_gate, no_gate)")

    # Auto-generated (editable) boundary summary sentence
    boundaries_summary_text: Optional[str] = Field(None, description="Professional summary sentence for boundaries")

    # Multiple Lots Support (optional, for subdivided properties)
    has_multiple_lots: Optional[bool] = Field(None, description="Whether property has multiple lots")
    lots_data: Optional[List[dict]] = Field(None, description="Data for multiple lots if applicable (JSON array)")

    # OCR Document Processing Support
    uploaded_documents: Optional[List[dict]] = Field(None, description="List of uploaded documents for OCR processing")
    field_sources: Optional[dict] = Field(None, description="Tracking data source per field (manual/ocr/api)")

    # Survey Plan Additional Details
    survey_plan_scale: Optional[str] = Field(None, max_length=50, description="Survey plan scale (e.g., '1:500', '1:1000')")
    plan_reference_notes: Optional[str] = Field(None, description="Additional notes about the survey plan")
    # ===== DESCRIPTION OF PROPERTY =====
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

    # Topographical Features
    elevation_changes: Optional[str] = Field(None, max_length=50, description="Elevation changes pattern (relatively_flat, gentle_slope, moderate_slope, steep_gradients, undulating)")
    drainage_pattern: Optional[str] = Field(None, max_length=50, description="Drainage pattern (well_drained, adequate_drainage, poor_drainage, seasonal_waterlogging, artificial_drainage)")
    vegetation_type: Optional[str] = Field(None, max_length=50, description="Vegetation type (bare_land, grass_coverage, shrubs_bushes, mature_trees, mixed_vegetation, dense_jungle)")
    natural_features: Optional[str] = Field(None, description="Description of notable natural features (streams, ponds, rock formations, etc.)")

    # ===== BUILDING DETAILS =====
    buildings: Optional[List[Building]] = Field(None, description="Array of building objects with full schema validation")
    occupier_name: Optional[str] = Field(None, max_length=300)
    occupier_relationship: Optional[str] = Field(None, max_length=50)

    # ===== PROPERTY PHOTOS =====
    property_photos: Optional[List[BuildingPhoto]] = Field(None, max_items=20, description="Property photos (max 20)")

    # ===== LOCALITY INFORMATION =====

    # Distance to major town/city
    distance_to_major_town_km: Optional[float] = Field(None, description="Distance to nearest major town in kilometers")
    major_town_name: Optional[str] = Field(None, max_length=200, description="Name of the nearest major town")

    # Nearby facilities (JSON array)
    nearby_facilities: Optional[List[dict]] = Field(None, description="Array of nearby facility objects with type, name, distance, coordinates, and selection status")

    # Infrastructure & Utilities
    has_electricity: Optional[bool] = Field(None, description="Whether electricity is available")
    water_supply_type: Optional[str] = Field(None, max_length=50, description="Type of water supply (pipe_borne_water, bore_water, well_water, none)")
    telecommunication_types: Optional[List[str]] = Field(None, description="Types of telecommunication available (landline, mobile_coverage)")
    internet_types: Optional[List[str]] = Field(None, description="Types of internet available (fiber, mobile_data)")

    # Public Transport
    has_public_transport: Optional[bool] = Field(None, description="Whether public transport is available nearby")
    public_transport_routes: Optional[str] = Field(None, description="Description of public transport routes")
    public_transport_frequency: Optional[str] = Field(None, max_length=200, description="Frequency of public transport service")
    nearest_bus_stop_distance_km: Optional[float] = Field(None, description="Distance to nearest bus stop in kilometers")
    nearest_bus_stop_name: Optional[str] = Field(None, max_length=200, description="Name of nearest bus stop")
    nearest_railway_station: Optional[str] = Field(None, max_length=200, description="Name of nearest railway station")
    nearest_railway_distance_km: Optional[float] = Field(None, description="Distance to nearest railway station in kilometers")

    # Area Characteristics
    area_type: Optional[str] = Field(None, max_length=50, description="Type of area (residential, commercial, industrial, mixed, agricultural, tourist)")
    development_level: Optional[str] = Field(None, max_length=50, description="Development level (well_developed, developing, moderate, undeveloped)")
    predominant_building_type: Optional[str] = Field(None, max_length=100, description="Predominant building type in the area")

    # Tourism/Special characteristics
    is_tourist_area: Optional[bool] = Field(None, description="Whether the area is a tourist area")
    tourist_attractions_nearby: Optional[str] = Field(None, description="Description of nearby tourist attractions")

    # Auto-generated (editable) locality narrative
    locality_description_text: Optional[str] = Field(None, description="Professional narrative text for LOCALITY section")

    # ===== LEGAL ASPECTS =====
    ownership_type: Optional[str] = Field(None, max_length=200, description="Ownership type")
    street_lines_status: Optional[str] = Field(None, max_length=200, description="Street lines status")
    building_limits_status: Optional[str] = Field(None, max_length=200, description="Building limits status")
    local_authority_data: Optional[str] = Field(None, description="Local authority information")
    rent_act_effectiveness: Optional[str] = Field(None, max_length=200, description="Rent act effectiveness")

    # Ownership & Title - Extended fields
    title_search_conducted: Optional[str] = Field(None, max_length=3, description="Whether title search was conducted (Yes/No)")
    pedigree_search_conducted: Optional[str] = Field(None, max_length=3, description="Whether pedigree search was conducted (Yes/No)")
    valuation_basis_note: Optional[str] = Field(None, description="Custom valuation basis statement")
    property_encumbered: Optional[str] = Field(None, max_length=3, description="Whether property has encumbrances (Yes/No)")
    encumbrance_type: Optional[str] = Field(None, max_length=100, description="Type of encumbrance (Mortgage/Life Interest/Lease/None)")
    encumbrance_details: Optional[str] = Field(None, description="Details of encumbrance (bank name, mortgagee, etc.)")

    # Street Lines - Extended fields
    street_lines_gazette_ref: Optional[str] = Field(None, max_length=100, description="Gazette reference number")
    street_lines_gazette_date: Optional[str] = Field(None, max_length=20, description="Gazette date")
    street_lines_impact_description: Optional[str] = Field(None, description="Detailed description of street lines impact")

    # Building Limits - Extended fields
    building_distance_from_road: Optional[str] = Field(None, max_length=50, description="Distance from access road")
    building_plan_approved: Optional[str] = Field(None, max_length=20, description="Building plan approval status (Yes/No/Not Applicable)")
    building_plan_reference: Optional[str] = Field(None, max_length=200, description="Building plan reference number")
    building_approval_authority: Optional[str] = Field(None, max_length=200, description="Authority that approved the building")
    building_within_limits: Optional[str] = Field(None, max_length=3, description="Whether building is within limits (Yes/No)")

    # Local Authority - Extended fields
    local_authority_rated: Optional[str] = Field(None, max_length=3, description="Whether property is rated for taxes (Yes/No)")
    local_authority_tax_levy: Optional[str] = Field(None, description="Tax levy information")

    # ===== LAND VALUES IN THE AREA =====
    comparable_properties: Optional[List[dict]] = Field(None, description="Array of comparable properties")
    land_market_analysis: Optional[str] = Field(None, description="Land market analysis text")

    # ===== VALUATION =====
    valuation_land_extent: Optional[float] = Field(None, ge=0, description="Land extent for valuation")
    valuation_rate_per_perch: Optional[float] = Field(None, ge=0, description="Rate per perch")
    valuation_total_land_value: Optional[float] = Field(None, ge=0, description="Total land value")
    valuation_buildings_data: Optional[List[dict]] = Field(None, description="Buildings valuation data")
    valuation_total_buildings_value: Optional[float] = Field(None, ge=0, description="Total buildings value")
    valuation_addons: Optional[List[dict]] = Field(None, description="Additional valuation items")
    valuation_total_addons_value: Optional[float] = Field(None, ge=0, description="Total addons value")
    valuation_market_value: Optional[float] = Field(None, ge=0, description="Market value")
    valuation_forced_sale_percentage: Optional[float] = Field(None, ge=0, le=100, description="Forced sale percentage")
    valuation_forced_sale_value: Optional[float] = Field(None, ge=0, description="Forced sale value")
    valuation_insurance_value: Optional[float] = Field(None, ge=0, description="Insurance value")
    valuation_manual_overrides: Optional[dict] = Field(None, description="Manual override values")

    # ===== CERTIFICATION =====
    certification_text: Optional[str] = Field(None, description="Certification statement text")
    certificate_survey_plan_ref: Optional[str] = Field(None, max_length=200, description="Survey plan reference for certificate of identity")
    certificate_survey_plan_date: Optional[str] = Field(None, max_length=50, description="Survey plan date for certificate of identity")
    certificate_identity_confirmed: Optional[bool] = Field(None, description="Certificate of identity confirmation checkbox")
    certification_valuer_name: Optional[str] = Field(None, max_length=255, description="Valuer name for certification (auto-filled from user profile)")
    certification_valuer_designation: Optional[str] = Field(None, max_length=200, description="Professional designation for certification")
    certification_date: Optional[str] = Field(None, max_length=50, description="Certification date")

    # ===== FIELD VALIDATORS =====

    @field_validator('applicant_full_name')
    @classmethod
    def validate_applicant_name(cls, v):
        """Sanitize applicant name while preserving unicode characters"""
        if v:
            return sanitize_dangerous_characters(v)
        return v

    @field_validator('plan_number')
    @classmethod
    def validate_plan_number(cls, v):
        """Sanitize plan number to prevent injection attacks"""
        if v:
            return sanitize_dangerous_characters(v)
        return v

    @field_validator('applicant_id_number')
    @classmethod
    def validate_id_number(cls, v, info):
        """Validate ID number format based on ID type"""
        if not v:
            return v

        # Get the ID type from the model data
        id_type = info.data.get('applicant_id_type', '').lower() if hasattr(info, 'data') else ''

        if 'nic' in id_type:
            if not validate_sri_lankan_nic(v):
                raise ValueError('Invalid Sri Lankan NIC format. Use old format (123456789V) or new format (200012345678)')
        elif 'passport' in id_type:
            if not validate_passport(v):
                raise ValueError('Invalid passport format. Must be 6-9 alphanumeric characters')

        # Sanitize dangerous characters regardless of type
        return sanitize_dangerous_characters(v)

    @field_validator('property_latitude')
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude is within valid range"""
        if v is not None:
            if v < -90 or v > 90:
                raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @field_validator('property_longitude')
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude is within valid range"""
        if v is not None:
            if v < -180 or v > 180:
                raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

    @field_validator('access_starting_point_latitude')
    @classmethod
    def validate_access_latitude(cls, v):
        """Validate access point latitude is within valid range"""
        if v is not None:
            if v < -90 or v > 90:
                raise ValueError('Access point latitude must be between -90 and 90 degrees')
        return v

    @field_validator('access_starting_point_longitude')
    @classmethod
    def validate_access_longitude(cls, v):
        """Validate access point longitude is within valid range"""
        if v is not None:
            if v < -180 or v > 180:
                raise ValueError('Access point longitude must be between -180 and 180 degrees')
        return v

    @field_validator('land_extent_acres')
    @classmethod
    def validate_land_acres(cls, v):
        """Validate land extent in acres is positive"""
        if v is not None and v < 0:
            raise ValueError('Land extent in acres cannot be negative')
        return v

    @field_validator('has_additional_owner', 'has_deed_info', 'has_special_note')
    @classmethod
    def convert_bool_to_string(cls, v):
        """Convert boolean values to yes/no strings for backward compatibility"""
        if v is None:
            return v
        if isinstance(v, bool):
            return "yes" if v else "no"
        return v

    # ===== JSON FIELD VALIDATORS =====

    @field_validator('boundaries')
    @classmethod
    def validate_boundaries_json(cls, v):
        """Validate boundaries JSON structure"""
        if v is not None:
            is_valid, error_msg = validate_boundaries(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('buildings')
    @classmethod
    def validate_buildings_json(cls, v):
        """Validate buildings JSON structure and clean legacy fields"""
        if v is not None:
            # Convert Building objects to dict if needed
            buildings_data = [
                b.model_dump() if hasattr(b, 'model_dump') else b
                for b in v
            ] if isinstance(v, list) else v

            # Clean up legacy length/width fields from rooms
            if isinstance(buildings_data, list):
                for building in buildings_data:
                    if isinstance(building, dict) and 'floors' in building:
                        for floor in building.get('floors', []):
                            if isinstance(floor, dict) and 'rooms' in floor:
                                for room in floor.get('rooms', []):
                                    if isinstance(room, dict):
                                        # Remove legacy fields
                                        room.pop('length', None)
                                        room.pop('width', None)

            is_valid, error_msg = validate_buildings(buildings_data)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('comparable_properties')
    @classmethod
    def validate_comparable_properties_json(cls, v):
        """Validate comparable properties JSON structure"""
        if v is not None:
            is_valid, error_msg = validate_comparable_properties(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v


class ReportCreate(ReportBase):
    pass

class ReportUpdate(ReportBase):
    pass

class ReportResponse(BaseModel):
    # Inherit fields from ReportBase but without validators
    # This prevents validation errors when returning existing database records
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Copy all fields from ReportBase without validators
    report_type: Optional[str] = None
    status: Optional[str] = None
    property_lot_description: Optional[str] = None
    plan_number: Optional[str] = None
    plan_date: Optional[str] = None
    licensed_surveyor_name: Optional[str] = None
    property_identification_type: Optional[str] = None
    property_identification_documents: Optional[dict] = None
    applicant_title: Optional[str] = None
    applicant_full_name: Optional[str] = None
    applicant_id_type: Optional[str] = None
    applicant_id_number: Optional[str] = None  # No validator for response
    applicant_address_line1: Optional[str] = None
    applicant_address_line2: Optional[str] = None
    applicant_district: Optional[str] = None
    applicant_province: Optional[str] = None
    applicant_country: Optional[str] = None
    valuation_type: Optional[str] = None
    property_ownership: Optional[str] = None
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
    property_name: Optional[str] = None
    assessment_number: Optional[str] = None
    property_village: Optional[str] = None
    property_divisional_secretariat: Optional[str] = None
    property_district: Optional[str] = None
    property_province: Optional[str] = None
    property_latitude: Optional[float] = None
    property_longitude: Optional[float] = None
    property_number: Optional[str] = None
    grama_niladari_division: Optional[str] = None
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
    access_road_segments: Optional[List[dict]] = None
    access_road_conditions: Optional[List[RoadCondition]] = None
    access_entry_mode: Optional[str] = None
    access_road_classes_detected: Optional[dict] = None
    land_extent_acres: Optional[int] = None
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
    field_sources: Optional[str] = None
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
    water_supply_type: Optional[str] = None
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
    predominant_building_type: Optional[str] = None
    is_tourist_area: Optional[bool] = None
    tourist_attractions_nearby: Optional[List[str]] = None
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
    comparable_properties: Optional[List[dict]] = None  # No validator for response
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
    certificate_survey_plan_ref: Optional[str] = None
    certificate_survey_plan_date: Optional[str] = None
    certificate_identity_confirmed: Optional[bool] = None
    certification_valuer_name: Optional[str] = None
    certification_valuer_designation: Optional[str] = None
    certification_date: Optional[str] = None

    class Config:
        from_attributes = True

# Legacy schemas for compatibility (can be removed later)
class UserDataResponse(ReportResponse):
    """Legacy schema for backward compatibility"""
    pass

class DocxGenerateRequest(BaseModel):
    report_id: int = Field(..., description="ID of the report to generate DOCX for")

class HealthResponse(BaseModel):
    status: str
    message: str

# Letterhead Template Schemas
class TemplateMetadata(BaseModel):
    """Metadata for a letterhead template"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Display name of the template")
    description: str = Field(..., description="Description of the template's visual style")
    category: str = Field(default="professional", description="Template category")

class TemplateListResponse(BaseModel):
    """Response containing list of available templates"""
    templates: List[TemplateMetadata] = Field(..., description="List of available letterhead templates")
