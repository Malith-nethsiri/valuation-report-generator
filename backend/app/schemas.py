from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer
from datetime import datetime
from typing import Optional, List, Dict
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
    """Validate passport format (6-12 alphanumeric characters) - INTERNATIONAL SUPPORT"""
    if not value:
        return True  # Optional field

    value = value.strip()

    # International passports: 6-12 alphanumeric characters
    # No strict format - countries have different conventions
    # - US: 9 alphanumeric (e.g., 123456789)
    # - UK: 9 alphanumeric (e.g., 123456789)
    # - India: 1 letter + 7 digits (e.g., A1234567)
    # - Sri Lanka: N + 7 digits (e.g., N1234567)
    # - Canada: 2 letters + 6 digits (e.g., AB123456)
    pattern = r'^[A-Z0-9]{6,12}$'
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
    bank_accounts: Optional[List["BankAccount"]] = None

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

    # Bank Account Management
    bank_accounts: Optional[List["BankAccount"]] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Bank Account Schemas
class BankAccount(BaseModel):
    id: str = Field(..., description="Unique identifier (UUID)")
    bank_name: str = Field(..., min_length=1, max_length=200, description="Bank name")
    account_number: str = Field(..., min_length=1, max_length=50, description="Account number")
    branch_name: str = Field(..., min_length=1, max_length=200, description="Branch name")

class BankAccountCreate(BaseModel):
    bank_name: str = Field(..., min_length=1, max_length=200)
    account_number: str = Field(..., min_length=1, max_length=50)
    branch_name: str = Field(..., min_length=1, max_length=200)

class BankAccountUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, min_length=1, max_length=200)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    branch_name: Optional[str] = Field(None, min_length=1, max_length=200)

# Deed Information Schema
class DeedInfo(BaseModel):
    deed_type: str = Field(..., description="Type of deed (Deed of Gift, Transfer deed, etc.)")
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
    # Water and sewage
    water_supply: Optional[List[str]] = Field(None, description="Array of water supply types")
    sewage: Optional[str] = Field(None, max_length=100, description="Sewage system type")

    # Electricity and parking (detailed objects)
    electricity: Optional[Electricity] = Field(None, description="Electricity details")
    parking: Optional[Parking] = Field(None, description="Parking facilities")

    # Communication services
    telephone: Optional[bool] = Field(None, description="Telephone connection available")
    internet: Optional[bool] = Field(None, description="Internet connection available")

    # Gas connection
    gas_connection: Optional[bool] = Field(None, description="Gas connection available")

    # Security features
    security_features: Optional[List[str]] = Field(default_factory=list, description="Security features (boundary_wall, main_gate, cctv, security_lights)")

    # Modern amenities
    amenities: Optional[Dict[str, bool]] = Field(None, description="Modern amenities (air_conditioning, built_in_wardrobes, modern_kitchen, pantry_cupboards)")

    # Hot water system
    hot_water_system: Optional[str] = Field(None, max_length=50, description="Hot water system type (electric_geyser, solar_heater, gas_heater, none)")

class Room(BaseModel):
    room_type: str = Field(..., description="Room type (Bedroom, Bathroom, Attached Bathroom, Living Room, etc.)")
    count: int = Field(default=1, ge=1, description="Number of rooms of this type")
    has_attached_bathroom: Optional[bool] = Field(None, description="Whether room has attached bathroom")

class Floor(BaseModel):
    floor_name: str = Field(..., description="Floor name (e.g., 'Ground Floor')")
    floor_area: Optional[float] = Field(None, ge=0, description="Floor area in square feet")

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
    building_age: Optional[int] = Field(None, ge=0, le=200, description="Building age in years")
    condition: Optional[str] = Field(None, max_length=50, description="Building condition")
    occupier_name: Optional[str] = Field(None, max_length=300, description="Occupier name")
    occupier_relationship: Optional[str] = Field(None, max_length=50, description="Relationship: owner, tenant, caretaker, family_member, vacant")
    is_rented: Optional[bool] = Field(None, description="Whether this building is rented")
    rent_details: Optional[str] = Field(None, max_length=500, description="Optional rent details if building is rented")
    roof_types: List[str] = Field(default_factory=list, description="Roof types")
    roof_description: Optional[str] = Field(None, description="Roof description")
    wall_types: List[str] = Field(default_factory=list, description="Wall types")
    wall_description: Optional[str] = Field(None, description="Wall description")
    floor_types: List[str] = Field(default_factory=list, description="Floor types")
    floor_description: Optional[str] = Field(None, description="Floor description")
    total_floor_area: Optional[float] = Field(None, ge=0, description="Total floor area in square feet")
    floors: List[Floor] = Field(default_factory=list, description="Building floors (simplified - floor names and areas only)")
    rooms: List[Room] = Field(default_factory=list, description="Rooms at building level (not per-floor)")
    accommodation_summary: Optional[AccommodationSummary] = Field(None, description="Auto-calculated accommodation summary at building level")
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

    # Multi-property support
    is_multi_property: Optional[bool] = Field(None, description="Whether this is a multi-property report")
    property_count: Optional[int] = Field(None, description="Number of properties in this report")

    # Property & Plan Information
    property_lot_description: Optional[str] = Field(None, max_length=200, description="DEPRECATED: Use lot_number instead")
    lot_number: Optional[str] = Field(None, max_length=200, description="Lot number (e.g., Lot 15, Lots 1 & 2)")
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

    # Request Type (client vs organization)
    request_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Request type: 'client_request' or 'organization_request'"
    )

    # Applicant Contact Number
    applicant_contact_number: Optional[str] = Field(
        None,
        max_length=50,
        description="Applicant contact/phone number"
    )

    # Valuation Purpose
    valuation_type: Optional[str] = Field(None, max_length=100, description="Type of valuation (Market Value, etc.)")
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
    hathpaththuwa: Optional[str] = Field(None, max_length=300, description="Hathpaththuwa (administrative division)")
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
    # Structure: {"north": {...}, "northeast": {...}, "east": {...}, "southeast": {...}, "south": {...}, "southwest": {...}, "west": {...}, "northwest": {...}}
    # Each direction: {"description": "...", "length": "...", "adjoins": "...", "notes": "..."}
    boundaries: Optional[dict] = Field(None, description="Boundary information (supports 4 main + 4 optional diagonal directions)")

    # Physical Boundaries
    physical_boundaries_types: Optional[List[str]] = Field(None, description="Types of physical boundaries (e.g., ['brick_walls', 'barbed_wire', 'live_fence'])")
    physical_boundaries_description: Optional[str] = Field(None, description="Detailed description of physical boundaries")

    # Boundary Types Per Direction (for professional summary generation)
    boundary_types_per_direction: Optional[dict] = Field(None, description="Boundary type for each direction - supports all 8 directions (JSON: {'north': 'brick_walls', 'northeast': '...', ...})")

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
    ongoing_construction_notes: Optional[str] = Field(None, description="Ongoing construction or development feasibility notes")

    # Topographical Features
    elevation_changes: Optional[str] = Field(None, max_length=50, description="Elevation changes pattern (relatively_flat, gentle_slope, moderate_slope, steep_gradients, undulating)")
    drainage_pattern: Optional[str] = Field(None, max_length=50, description="Drainage pattern (well_drained, adequate_drainage, poor_drainage, seasonal_waterlogging, artificial_drainage)")
    vegetation_type: Optional[str] = Field(None, max_length=50, description="Vegetation type (bare_land, grass_coverage, shrubs_bushes, mature_trees, mixed_vegetation, dense_jungle)")
    natural_features: Optional[str] = Field(None, description="Description of notable natural features (streams, ponds, rock formations, etc.)")

    # ===== BUILDING DETAILS =====
    buildings: Optional[List[Building]] = Field(None, description="Array of building objects with full schema validation")
    occupier_name: Optional[str] = Field(None, max_length=300, description="DEPRECATED: Moved to building level. Kept for backward compatibility.")
    occupier_relationship: Optional[str] = Field(None, max_length=50, description="DEPRECATED: Moved to building level. Kept for backward compatibility.")

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
    water_supply_type: Optional[List[str]] = Field(None, description="Array of water supply types (Pipe-borne (NWSDB), Well, Bore/Tube Well, Rainwater Harvesting, or custom)")
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
    predominant_building_type: Optional[List[str]] = Field(None, description="Array of predominant building types (Single Storey Residential, Multi Storey Residential, Apartments, Commercial Buildings, Mixed, or custom)")

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

    # DEPRECATED: Use plan_number and plan_date instead (kept for backward compatibility after migration)
    certificate_survey_plan_ref: Optional[str] = Field(None, max_length=200, description="DEPRECATED: Use plan_number instead. Survey plan reference for certificate of identity")
    certificate_survey_plan_date: Optional[str] = Field(None, max_length=50, description="DEPRECATED: Use plan_date instead. Survey plan date for certificate of identity")
    certificate_identity_confirmed: Optional[bool] = Field(None, description="DEPRECATED: Certificate of identity is now optional")

    certification_valuer_name: Optional[str] = Field(None, max_length=255, description="Valuer name for certification (auto-filled from user profile)")
    certification_valuer_designation: Optional[str] = Field(None, max_length=200, description="Professional designation for certification")
    certification_date: Optional[str] = Field(None, max_length=50, description="Certification date")

    # ===== INVOICE =====
    invoice_data: Optional['InvoiceData'] = Field(None, description="Invoice/professional fees data")

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
        """Validate ID number format based on ID type - OPTIONAL field"""
        if not v:
            return v  # Allow empty/None values

        # Get the ID type from the model data
        id_type = info.data.get('applicant_id_type', '').lower() if hasattr(info, 'data') else ''

        # If ID type is missing, we can't validate format - just sanitize
        if not id_type:
            return sanitize_dangerous_characters(v)

        if 'nic' in id_type:
            if not validate_sri_lankan_nic(v):
                raise ValueError('Invalid Sri Lankan NIC format. Use old format (123456789V) or new format (200012345678)')
        elif 'passport' in id_type:
            if not validate_passport(v):
                raise ValueError('Invalid passport format. Must be 6-12 alphanumeric characters (supports international passports)')
        elif 'other' in id_type:
            # For "Other" type, just check minimum length
            if len(v.strip()) < 3:
                raise ValueError('ID number must be at least 3 characters')

        # Sanitize dangerous characters regardless of type
        return sanitize_dangerous_characters(v)

    @field_validator('valuation_purpose')
    @classmethod
    def validate_valuation_purpose(cls, v):
        """Validate valuation purpose - prevent whitespace-only entries"""
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

    @field_validator('water_supply_type')
    @classmethod
    def validate_water_supply_type(cls, v):
        """Validate water supply type array"""
        if v is None:
            return v

        # Max 5 selections
        if len(v) > 5:
            raise ValueError("Maximum 5 water supply types allowed")

        # Each value max 50 characters
        for item in v:
            if not item or len(item) > 50:
                raise ValueError(f"Invalid water supply type: must be 1-50 characters")

        # Remove case-insensitive duplicates, preserve order
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
        """Validate predominant building type array"""
        if v is None:
            return v

        # Max 5 selections
        if len(v) > 5:
            raise ValueError("Maximum 5 building types allowed")

        # Each value max 50 characters
        for item in v:
            if not item or len(item) > 50:
                raise ValueError(f"Invalid building type: must be 1-50 characters")

        # Remove case-insensitive duplicates, preserve order
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
    is_multi_property: Optional[bool] = None
    property_count: Optional[int] = None
    property_lot_description: Optional[str] = None  # DEPRECATED
    lot_number: Optional[str] = None
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

    # DEPRECATED: Use plan_number and plan_date instead (kept for backward compatibility)
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


# ===== MULTI-PROPERTY SUPPORT SCHEMAS =====

# Invoice Schemas
class InvoiceItem(BaseModel):
    """Individual line item in a professional fee invoice"""
    description: str = Field(..., description="Service description (e.g., 'Valuation of Property 1')")
    total: float = Field(..., ge=0, description="Direct price for this line item")

class InvoiceData(BaseModel):
    """Professional fee invoice data for single or multi-property reports"""
    items: List[InvoiceItem] = Field(default_factory=list, description="Itemized service charges")
    subtotal: float = Field(default=0, ge=0, description="Sum of all items")
    traveling_charges: Optional[float] = Field(None, ge=0, description="Optional traveling/site visit charges")
    discount: Optional[float] = Field(None, ge=0, description="Optional discount amount")
    total: float = Field(..., ge=0, description="Final total amount")
    bank_account_ids: List[str] = Field(default_factory=list, description="Selected bank account IDs from user profile")
    manual_bank_details: Optional[str] = Field(None, description="Manual bank details if no accounts selected")


# Property Schemas (mirrors Property model fields)
class PropertyBase(BaseModel):
    """Base schema for Property - contains all property-specific fields"""

    # Property Status & Type (for multi-property reports)
    status: Optional[str] = Field("draft", max_length=50, description="Property completion status: 'draft' or 'completed'")
    property_type: Optional[str] = Field("residential", max_length=50, description="Property type: 'residential' or 'bare_land'")

    # Property Identification
    property_lot_description: Optional[str] = Field(None, max_length=200, description="DEPRECATED: Use lot_number instead")
    lot_number: Optional[str] = Field(None, max_length=200, description="Lot number (e.g., Lot 15, Lots 1 & 2)")
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_date: Optional[str] = Field(None, max_length=50)
    licensed_surveyor_name: Optional[str] = Field(None, max_length=255)
    property_identification_type: Optional[str] = Field(None, max_length=50)
    property_identification_documents: Optional[dict] = None

    # Deed Information
    has_deed_info: Optional[str] = Field(None, max_length=10)
    deeds: Optional[List[dict]] = None

    # Property Location
    property_name: Optional[str] = Field(None, max_length=200)
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

    # Access Directions
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
    access_road_segments: Optional[List[dict]] = None
    access_road_conditions: Optional[List[dict]] = None
    access_entry_mode: Optional[str] = Field(None, max_length=20)
    access_road_classes_detected: Optional[dict] = None

    # Land Extent & Boundaries
    land_extent_acres: Optional[float] = Field(None, ge=0)
    land_extent_roods: Optional[int] = Field(None, ge=0, le=3)
    land_extent_perches: Optional[float] = Field(None, ge=0)
    land_extent_hectares: Optional[float] = Field(None, ge=0)
    land_extent_square_meters: Optional[float] = Field(None, ge=0)
    land_extent_formatted: Optional[str] = Field(None, max_length=50)
    land_traditional_name: Optional[str] = Field(None, max_length=300)
    # Boundary Information - supports 4 main directions (required) + 4 diagonal directions (optional)
    boundaries: Optional[dict] = None
    physical_boundaries_types: Optional[List[str]] = None
    physical_boundaries_description: Optional[str] = None
    # Boundary types per direction - supports all 8 directions (4 main + 4 diagonal)
    boundary_types_per_direction: Optional[dict] = None
    entrance_type: Optional[str] = Field(None, max_length=100)
    boundaries_summary_text: Optional[str] = None
    has_multiple_lots: Optional[bool] = None
    lots_data: Optional[List[dict]] = None

    # Property Description
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

    # Buildings
    buildings: Optional[List[dict]] = None
    occupier_name: Optional[str] = Field(None, max_length=300, description="DEPRECATED: Moved to building level")
    occupier_relationship: Optional[str] = Field(None, max_length=50, description="DEPRECATED: Moved to building level")

    # Property Photos
    property_photos: Optional[List[dict]] = None

    # Locality Information
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

    # Legal Aspects
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

    # Comparable Properties & Valuation
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

    # Property Owner (can differ from report applicant)
    property_owner_title: Optional[str] = Field(None, max_length=20)
    property_owner_full_name: Optional[str] = Field(None, max_length=500)
    property_owner_id_type: Optional[str] = Field(None, max_length=50)
    property_owner_id_number: Optional[str] = Field(None, max_length=100)
    has_additional_owner: Optional[str] = Field(None, max_length=10)
    additional_owner_names: Optional[str] = None

    # Per-property inspection date
    inspection_date: Optional[str] = Field(None, max_length=50)

    # OCR Metadata
    uploaded_documents: Optional[List[dict]] = None
    field_sources: Optional[dict] = None
    survey_plan_scale: Optional[str] = Field(None, max_length=50)
    plan_reference_notes: Optional[str] = None

    # Property Library Support
    is_template: Optional[bool] = Field(default=False)
    template_name: Optional[str] = Field(None, max_length=200)
    last_valued_date: Optional[str] = Field(None, max_length=50)

    # Validation for geographic coordinates
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

    @field_validator('water_supply_type')
    @classmethod
    def validate_water_supply_type(cls, v):
        """Validate water supply type array"""
        if v is None:
            return v

        # Max 5 selections
        if len(v) > 5:
            raise ValueError("Maximum 5 water supply types allowed")

        # Each value max 50 characters
        for item in v:
            if not item or len(item) > 50:
                raise ValueError(f"Invalid water supply type: must be 1-50 characters")

        # Remove case-insensitive duplicates, preserve order
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
        """Validate predominant building type array"""
        if v is None:
            return v

        # Max 5 selections
        if len(v) > 5:
            raise ValueError("Maximum 5 building types allowed")

        # Each value max 50 characters
        for item in v:
            if not item or len(item) > 50:
                raise ValueError(f"Invalid building type: must be 1-50 characters")

        # Remove case-insensitive duplicates, preserve order
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


# ReportProperty Junction Schemas
class ReportPropertyBase(BaseModel):
    """Base schema for ReportProperty junction"""
    property_id: int = Field(..., description="ID of the property")
    property_order: int = Field(default=1, ge=1, description="Display order in report (for drag-drop)")
    report_specific_notes: Optional[str] = Field(None, description="Notes specific to this property in this report")
    override_market_value: Optional[float] = Field(None, ge=0, description="Override market value for this report")
    override_forced_sale_value: Optional[float] = Field(None, ge=0, description="Override forced sale value for this report")


class ReportPropertyCreate(ReportPropertyBase):
    """Schema for creating a report-property association"""
    pass


class ReportPropertyUpdate(BaseModel):
    """Schema for updating report-property association"""
    property_order: Optional[int] = Field(None, ge=1)
    report_specific_notes: Optional[str] = None
    override_market_value: Optional[float] = Field(None, ge=0)
    override_forced_sale_value: Optional[float] = Field(None, ge=0)


class ReportPropertyResponse(ReportPropertyBase):
    """Schema for report-property response (includes full property data)"""
    id: int
    report_id: int
    property: PropertyResponse  # Nested full property data
    created_at: datetime

    class Config:
        from_attributes = True


# Updated Report Schemas for Multi-Property Support
class MultiPropertyReportCreate(BaseModel):
    """Schema for creating a multi-property report"""
    report_type: str = Field(default="residential_property")
    status: str = Field(default="draft")

    # Common fields (shared across all properties)
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

    # Certification (common for all properties)
    certification_text: Optional[str] = None
    certification_valuer_name: Optional[str] = None
    certification_valuer_designation: Optional[str] = None
    certification_date: Optional[str] = None
    certificate_identity_confirmed: Optional[bool] = False

    # Multi-property specific fields
    is_multi_property: bool = Field(default=True)
    property_ids: Optional[List[int]] = Field(None, description="IDs of existing properties to link")
    properties: Optional[List[PropertyCreate]] = Field(None, description="New properties to create inline")
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

    # Common fields
    applicant_full_name: Optional[str] = None
    applicant_address_line1: Optional[str] = None
    valuation_type: Optional[str] = None
    valuation_purpose: Optional[str] = None
    submission_organization: Optional[str] = None
    report_reference: Optional[str] = None
    report_date: Optional[str] = None

    # Associated properties (ordered by property_order)
    properties: List[PropertyResponse] = Field(default_factory=list)

    # Invoice data
    invoice_data: Optional[InvoiceData] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
