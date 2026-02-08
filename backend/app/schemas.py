from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer
from datetime import datetime
from typing import Optional, List, Dict
import re
from .utils.json_validators import (
    validate_boundaries,
    validate_buildings,
    validate_comparable_properties,
    validate_deeds,
    validate_nearby_facilities,
    validate_property_photos,
    validate_access_road_conditions
)

# ===== VALIDATION HELPER FUNCTIONS =====

def _validate_password_common(password: str) -> str:
    """Common password validation logic for all password fields.

    Validates password strength requirements using auth module validator.
    Raises ValueError if password doesn't meet requirements.
    Returns the validated password.
    """
    from .auth import validate_password_strength

    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)
    return password


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


def validate_date_format(value: str) -> bool:
    """
    Validate date format DD-MM-YYYY.
    Returns True if valid or empty, False otherwise.
    This ensures consistency between frontend collection and database storage.
    """
    if not value:
        return True  # Optional field

    value = value.strip()

    # DD-MM-YYYY format pattern
    pattern = r'^(\d{2})-(\d{2})-(\d{4})$'
    match = re.match(pattern, value)

    if not match:
        return False

    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

    # Basic range validation
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False
    if year < 1900 or year > 2100:
        return False

    # Days in month validation
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Leap year check for February
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        days_in_month[1] = 29

    if day > days_in_month[month - 1]:
        return False

    return True


def normalize_date_format(value: str) -> str:
    """
    Normalize date to DD-MM-YYYY format.
    Handles common input formats: DD/MM/YYYY, DD.MM.YYYY, YYYY-MM-DD
    Returns normalized date or original if already correct/unrecognized.
    """
    if not value:
        return value

    value = value.strip()

    # Already in DD-MM-YYYY format
    if re.match(r'^\d{2}-\d{2}-\d{4}$', value):
        return value

    # DD/MM/YYYY format
    match = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # DD.MM.YYYY format
    match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # YYYY-MM-DD format (ISO)
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', value)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"

    return value


def validate_id_number(id_type: str, id_number: str) -> tuple[bool, str]:
    """
    Validate ID number based on ID type.
    Returns (is_valid, error_message).
    Ensures consistency between frontend validation and backend storage.
    """
    if not id_number:
        return True, ""  # Optional field

    if not id_type:
        return True, ""  # No type specified, allow any

    id_number = id_number.strip()
    id_type_upper = id_type.upper()

    if id_type_upper == 'NIC':
        if not validate_sri_lankan_nic(id_number):
            return False, "Invalid NIC format. Use old format (9 digits + V/X) or new format (12 digits)"
    elif id_type_upper == 'PASSPORT':
        if not validate_passport(id_number):
            return False, "Invalid passport format. Must be 6-12 alphanumeric characters"
    elif id_type_upper == 'OTHER':
        if len(id_number) < 3:
            return False, "ID number must be at least 3 characters"

    return True, ""


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
        return _validate_password_common(v)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class UserResponse(UserBase):
    id: int
    role: str = Field(default="user", description="User role: 'user' or 'admin'")
    email_verified: bool = Field(default=False, description="Whether email has been verified")
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
    refresh_token: Optional[str] = None  # Refresh token for renewing access
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str = Field(..., description="The refresh token to use for getting a new access token")


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh with token rotation."""
    access_token: str
    refresh_token: Optional[str] = None  # New refresh token for rotation (body-based clients)
    token_type: str = "bearer"


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

    @field_validator('deed_date')
    @classmethod
    def validate_deed_date(cls, v):
        """Validate and normalize deed date to DD-MM-YYYY format."""
        if not v:
            raise ValueError("Deed date is required")
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(f'Invalid deed date format: "{v}". Use DD-MM-YYYY format')
        return normalized

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

# ===== REPORT FIELD GROUP MIXINS =====
# These mixins organize ReportBase's 150+ fields into logical groups.
# Used by per-type schemas (BareLandReportCreate, ResidentialReportCreate)
# to validate only the relevant fields for each report type.


class IdentificationFields(BaseModel):
    """Property identification and plan details."""
    lot_number: Optional[str] = Field(None, max_length=200)
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_date: Optional[str] = Field(None, max_length=50)
    licensed_surveyor_name: Optional[str] = Field(None, max_length=255)
    property_identification_type: Optional[str] = Field(None, max_length=50)
    property_identification_documents: Optional[dict] = Field(None)
    has_deed_info: Optional[str] = Field(None, max_length=10)
    deeds: Optional[List[DeedInfo]] = Field(None)
    has_multiple_lots: Optional[bool] = Field(None)
    lots_data: Optional[List[dict]] = Field(None)
    uploaded_documents: Optional[List[dict]] = Field(None)
    field_sources: Optional[dict] = Field(None)
    survey_plan_scale: Optional[str] = Field(None, max_length=50)
    plan_reference_notes: Optional[str] = Field(None)
    land_traditional_name: Optional[str] = Field(None, max_length=300)


class ApplicantFields(BaseModel):
    """Applicant and request information."""
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
    """Property location, access, and GPS fields."""
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


class LandFields(BaseModel):
    """Land extent, boundaries, and physical characteristics."""
    land_extent_acres: Optional[float] = Field(None, ge=0, le=99999.99)
    land_extent_roods: Optional[int] = Field(None, ge=0, le=3)
    land_extent_perches: Optional[float] = Field(None, ge=0, lt=40)
    land_extent_hectares: Optional[float] = Field(None, ge=0)
    land_extent_square_meters: Optional[float] = Field(None, ge=0)
    land_extent_formatted: Optional[str] = Field(None, max_length=50)
    boundaries: Optional[dict] = Field(None)
    physical_boundaries_types: Optional[List[str]] = Field(None)
    physical_boundaries_description: Optional[str] = Field(None)
    boundary_types_per_direction: Optional[dict] = Field(None)
    entrance_type: Optional[str] = Field(None, max_length=100)
    boundaries_summary_text: Optional[str] = Field(None)
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


class BuildingFields(BaseModel):
    """Building details and occupier information."""
    buildings: Optional[List[Building]] = Field(None)
    occupier_name: Optional[str] = Field(None, max_length=300)
    occupier_relationship: Optional[str] = Field(None, max_length=50)
    property_photos: Optional[List[BuildingPhoto]] = Field(None, max_items=20)


class LocalityFields(BaseModel):
    """Locality and infrastructure information."""
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


class LegalFields(BaseModel):
    """Legal aspects and title information."""
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


class ValuationFields(BaseModel):
    """Valuation calculations and comparable properties."""
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


class CertificationFields(BaseModel):
    """Certification and invoice data."""
    certification_text: Optional[str] = Field(None)
    certificate_identity_confirmed: Optional[bool] = Field(None)
    certification_valuer_name: Optional[str] = Field(None, max_length=255)
    certification_valuer_designation: Optional[str] = Field(None, max_length=200)
    certification_date: Optional[str] = Field(None, max_length=50)
    invoice_data: Optional['InvoiceData'] = Field(None)


# Report Schemas
class ReportBase(BaseModel):
    report_type: str = Field(default="residential_property", description="Type of report")
    status: str = Field(default="draft", description="Report status (draft, completed)")

    # Multi-property support
    is_multi_property: Optional[bool] = Field(None, description="Whether this is a multi-property report")
    property_count: Optional[int] = Field(None, description="Number of properties in this report")

    # Vehicle report support
    primary_vehicle_id: Optional[int] = Field(None, description="ID of primary vehicle for standalone vehicle reports")
    is_office_use: Optional[bool] = Field(None, description="Whether this is an office/government report")
    vehicle_count: Optional[int] = Field(None, description="Number of vehicles in this report")
    folio_number: Optional[str] = Field(None, max_length=100, description="Folio number (manual entry)")
    inspection_place: Optional[str] = Field(None, description="Inspection place (free text)")

    # Property & Plan Information
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
    certificate_identity_confirmed: Optional[bool] = Field(None, description="Certificate of identity confirmation")

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

    # ===== DATE FORMAT VALIDATORS =====
    # These ensure consistency between frontend data collection (DD-MM-YYYY)
    # and database storage (String fields expecting DD-MM-YYYY format)

    @field_validator('plan_date', 'inspection_date', 'report_date', 'certification_date')
    @classmethod
    def validate_and_normalize_date(cls, v):
        """
        Validate and normalize date fields to DD-MM-YYYY format.
        Handles common input formats and ensures database consistency.
        """
        if v is None:
            return v

        # Normalize the date format first
        normalized = normalize_date_format(v)

        # Validate the normalized date
        if not validate_date_format(normalized):
            raise ValueError(
                f'Invalid date format: "{v}". Use DD-MM-YYYY format (e.g., 25-12-2023)'
            )

        return normalized

    @field_validator('applicant_id_number')
    @classmethod
    def validate_applicant_id(cls, v, info):
        """
        Validate applicant ID number based on ID type.
        Ensures consistency with frontend validation rules.
        """
        if v is None:
            return v

        # Get the ID type from the data being validated
        id_type = info.data.get('applicant_id_type') if info.data else None

        if id_type:
            is_valid, error_msg = validate_id_number(id_type, v)
            if not is_valid:
                raise ValueError(error_msg)

        return v.strip() if v else v

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

    @field_validator('deeds')
    @classmethod
    def validate_deeds_json(cls, v):
        """Validate deeds JSON structure"""
        if v is not None:
            is_valid, error_msg = validate_deeds(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('nearby_facilities')
    @classmethod
    def validate_nearby_facilities_json(cls, v):
        """Validate nearby facilities JSON structure"""
        if v is not None:
            is_valid, error_msg = validate_nearby_facilities(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('property_photos')
    @classmethod
    def validate_property_photos_json(cls, v):
        """Validate property photos JSON structure"""
        if v is not None:
            is_valid, error_msg = validate_property_photos(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v

    @field_validator('access_road_conditions')
    @classmethod
    def validate_access_road_conditions_json(cls, v):
        """Validate access road conditions JSON structure"""
        if v is not None:
            # Convert Pydantic models to dicts for JSON schema validation
            v_dicts = [item.model_dump() if hasattr(item, 'model_dump') else item for item in v]
            is_valid, error_msg = validate_access_road_conditions(v_dicts)
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


# ===== PER-TYPE REPORT SCHEMAS =====
# These provide stricter validation by only accepting fields relevant to each report type.
# Use with discriminated unions at API endpoints for type-safe validation.

class BareLandReportCreate(
    IdentificationFields, ApplicantFields, LocationFields, LandFields,
    LocalityFields, LegalFields, ValuationFields, CertificationFields,
    BaseModel
):
    """Schema for bare land reports - no building fields."""
    report_type: str = Field(default='bare_land')
    status: str = Field(default='draft')
    # Bare land has property photos directly (not through buildings)
    property_photos: Optional[List[BuildingPhoto]] = Field(None, max_items=20)
    # Report metadata
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
    # Report metadata
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

    This schema prevents injection of internal fields like user_id by
    only allowing fields explicitly defined here.
    """
    # Explicit properties field for multi-property reports
    properties: Optional[List[Dict]] = Field(None, description="List of property data for multi-property reports")

    # Property metadata for additional context
    property_metadata: Optional[Dict] = Field(None, description="Additional property metadata")

    class Config:
        # Forbid extra fields to prevent injection attacks
        extra = 'forbid'


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

    # Vehicle report fields
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
    tourist_attractions_nearby: Optional[str] = None  # Text field, not list
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
    certificate_identity_confirmed: Optional[bool] = None

    certification_valuer_name: Optional[str] = None
    certification_valuer_designation: Optional[str] = None
    certification_date: Optional[str] = None

    class Config:
        from_attributes = True


# ===== PAGINATION & FILTER RESPONSE SCHEMAS =====

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

    # Date format validators for Property
    @field_validator('plan_date', 'inspection_date', 'last_valued_date', 'street_lines_gazette_date')
    @classmethod
    def validate_property_dates(cls, v):
        """Validate and normalize date fields to DD-MM-YYYY format."""
        if v is None:
            return v
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(f'Invalid date format: "{v}". Use DD-MM-YYYY format')
        return normalized

    # ID validation for property owner
    @field_validator('property_owner_id_number')
    @classmethod
    def validate_property_owner_id(cls, v, info):
        """Validate property owner ID number based on ID type."""
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


# ===== JOB SCHEMAS FOR ASYNC DOCUMENT GENERATION =====

class JobCreate(BaseModel):
    """Schema for creating a new background job."""
    report_id: int = Field(..., description="ID of the report to generate document for")
    job_type: str = Field(
        default="docx_generation",
        pattern="^(docx_generation|pdf_generation)$",
        description="Type of job to create"
    )


class JobResponse(BaseModel):
    """Schema for job status responses."""
    id: str = Field(..., description="Unique job identifier (UUID)")
    user_id: int
    report_id: Optional[int]
    job_type: str
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    result_url: Optional[str] = Field(None, description="URL/path to download result when completed")
    result_filename: Optional[str] = Field(None, description="Original filename of generated document")
    error_message: Optional[str] = Field(None, description="Error details if job failed")
    progress_percent: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage 0-100")
    progress_message: Optional[str] = Field(None, description="Current step description")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    """Simplified job status response for polling."""
    id: str
    status: str
    progress_percent: Optional[int] = 0
    progress_message: Optional[str] = None
    error_message: Optional[str] = None
    download_ready: bool = False
    download_url: Optional[str] = None
    filename: Optional[str] = None


# ===== PASSWORD RESET SCHEMAS =====

class ForgotPasswordRequest(BaseModel):
    """Request schema for initiating password reset."""
    email: EmailStr = Field(..., description="Email address to send reset link to")


class ResetPasswordRequest(BaseModel):
    """Request schema for resetting password with token."""
    email: EmailStr = Field(..., description="Email address associated with the account")
    token: str = Field(..., min_length=20, description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength requirements"""
        return _validate_password_common(v)


class PasswordResetResponse(BaseModel):
    """Response for password reset operations."""
    success: bool
    message: str


# ===== EMAIL VERIFICATION SCHEMAS =====

class SendVerificationRequest(BaseModel):
    """Request to send/resend verification email. Uses authenticated user's email."""
    pass


class VerifyEmailRequest(BaseModel):
    """Request to verify email with token from email link."""
    email: EmailStr = Field(..., description="Email address to verify")
    token: str = Field(..., min_length=20, description="Verification token from email")


class EmailVerificationResponse(BaseModel):
    """Response for email verification operations."""
    success: bool
    message: str
    email_verified: bool = Field(..., description="Whether the email is now verified")


# ===== VEHICLE SCHEMAS =====

class VehiclePhoto(BaseModel):
    """Vehicle photo structure"""
    id: str = Field(..., description="Photo ID")
    image_data: str = Field(..., description="Base64 encoded image data")
    caption: Optional[str] = Field(None, description="Photo caption")
    order: int = Field(..., ge=0, description="Display order")


class VehicleTyreSet(BaseModel):
    """Tyre information for front or rear set"""
    brand: Optional[str] = Field(None, max_length=100, description="Tyre brand")
    size: Optional[str] = Field(None, max_length=50, description="Tyre size (e.g., 195/65R15)")
    tread_percent: Optional[int] = Field(None, ge=0, le=100, description="Tread percentage (0-100)")
    condition: Optional[str] = Field(None, description="Condition: Excellent/Good/Fair/Poor/Very Poor")


class VehicleTyres(BaseModel):
    """Complete tyre information"""
    front: Optional[VehicleTyreSet] = None
    rear: Optional[VehicleTyreSet] = None
    spare_available: Optional[bool] = Field(None, description="Spare tyre available")
    need_replacement: Optional[bool] = Field(None, description="Tyres need replacement")
    rear_type: Optional[str] = Field(None, description="Single or Dual (for trucks)")


class VehicleSuspension(BaseModel):
    """Suspension information"""
    front: Optional[str] = Field(None, description="Front suspension condition")
    rear: Optional[str] = Field(None, description="Rear suspension condition")


class VehicleElectrical(BaseModel):
    """Electrical system information"""
    starter: Optional[bool] = Field(None, description="Starter working")
    horn: Optional[bool] = Field(None, description="Horn working")
    wiper: Optional[bool] = Field(None, description="Wiper working")
    battery_condition: Optional[str] = Field(None, description="Battery condition: Good/Fair/Poor/Needs Replacement")


class VehicleLights(BaseModel):
    """Lights status"""
    head: Optional[bool] = Field(None, description="Head lights working")
    dim: Optional[bool] = Field(None, description="Dim lights working")
    signal: Optional[bool] = Field(None, description="Signal lights working")
    parking: Optional[bool] = Field(None, description="Parking lights working")
    reverse: Optional[bool] = Field(None, description="Reverse lights working")
    meter: Optional[bool] = Field(None, description="Dashboard/Meter lights working")


class VehicleFeatures(BaseModel):
    """Vehicle features and amenities"""
    air_condition: Optional[bool] = Field(None, description="Air condition working")
    dual_air_condition: Optional[bool] = Field(None, description="Dual air condition")
    power_mirror: Optional[bool] = Field(None, description="Power mirror available")
    power_window: Optional[bool] = Field(None, description="Power window available")
    power_steering: Optional[bool] = Field(None, description="Power steering available")
    airbag: Optional[bool] = Field(None, description="Airbag available")
    num_airbags: Optional[int] = Field(None, ge=0, description="Number of airbags")
    seats: Optional[int] = Field(None, ge=1, description="Number of seats")
    doors: Optional[int] = Field(None, ge=1, description="Number of doors")


class VehicleOfficeData(BaseModel):
    """Office use only fields (for government reports)"""
    civil_no: Optional[str] = Field(None, max_length=100, description="Civil number (government vehicles)")
    military_no: Optional[str] = Field(None, max_length=100, description="Military number (military vehicles)")
    approval_position: Optional[str] = Field(None, max_length=200, description="Approval position")


class VehiclePastValuation(BaseModel):
    """Past valuation entry for comparison table"""
    serial: Optional[int] = Field(None, description="Serial number (auto-generated)")
    civil_no: Optional[str] = Field(None, max_length=100, description="Vehicle No - Civil")
    military_no: Optional[str] = Field(None, max_length=100, description="Vehicle No - Military")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Year of past valuation")
    value: Optional[float] = Field(None, ge=0, description="Past valuation value (Rs)")
    market_value: Optional[float] = Field(None, ge=0, description="Market value (Rs)")


class VehicleBase(BaseModel):
    """Base schema for Vehicle - contains all vehicle-specific fields"""

    # Status & Type
    status: Optional[str] = Field("draft", max_length=50, description="Vehicle status: 'draft' or 'completed'")
    vehicle_type: Optional[str] = Field(None, max_length=50, description="Vehicle type: 'car', 'motorcycle', 'truck', 'special'")
    is_template: Optional[bool] = Field(False, description="Save to Vehicle Library")

    # ===== VEHICLE IDENTIFICATION =====
    registration_number: Optional[str] = Field(None, max_length=50, description="Vehicle registration number")
    provincial_council: Optional[str] = Field(None, max_length=100, description="Provincial council")
    class_of_vehicle: Optional[str] = Field(None, max_length=100, description="Class of vehicle")
    body_colour: Optional[str] = Field(None, max_length=100, description="Body colour")
    chassis_number: Optional[str] = Field(None, max_length=100, description="Chassis number")
    engine_number: Optional[str] = Field(None, max_length=100, description="Engine number")
    vehicle_status: Optional[str] = Field(None, max_length=100, description="Vehicle status")
    country_of_origin: Optional[str] = Field(None, max_length=100, description="Country of origin")
    make: Optional[str] = Field(None, max_length=100, description="Vehicle make/brand")
    model: Optional[str] = Field(None, max_length=200, description="Vehicle model")
    date_of_first_registration: Optional[str] = Field(None, max_length=50, description="Date of first registration")
    year_of_manufacture: Optional[int] = Field(None, ge=1900, le=2100, description="Year of manufacture")
    cylinder_capacity: Optional[int] = Field(None, ge=0, description="Cylinder capacity in cc")
    fuel_type: Optional[str] = Field(None, max_length=50, description="Fuel type")
    mileage: Optional[int] = Field(None, ge=0, description="Mileage")
    mileage_unit: Optional[str] = Field("km", max_length=20, description="Mileage unit: 'km' or 'miles'")

    # ===== ENGINE & TRANSMISSION =====
    engine_type: Optional[str] = Field(None, max_length=100, description="Engine type description")
    transmission: Optional[str] = Field(None, max_length=50, description="Transmission type")
    wheel_drive: Optional[str] = Field(None, max_length=20, description="Wheel drive: 2WD, 4WD, AWD")

    # ===== CONDITION FIELDS =====
    running_condition: Optional[str] = Field(None, max_length=50, description="Running condition")
    clutch_status: Optional[str] = Field(None, max_length=100, description="Clutch status")
    engine_condition: Optional[str] = Field(None, max_length=50, description="Engine condition")
    gear_box_condition: Optional[str] = Field(None, max_length=50, description="Gear box condition")
    differential_status: Optional[str] = Field(None, max_length=100, description="Differential status")
    gear_selection: Optional[str] = Field(None, max_length=50, description="Gear selection quality")
    body_condition: Optional[str] = Field(None, max_length=50, description="Body condition")
    chassis_condition: Optional[str] = Field(None, max_length=50, description="Chassis condition")
    upholstery_condition: Optional[str] = Field(None, max_length=50, description="Upholstery condition")
    underside_condition: Optional[str] = Field(None, max_length=50, description="Underside condition")

    # ===== PARTS AVAILABILITY =====
    body_parts_status: Optional[str] = Field(None, max_length=100, description="Body parts availability")
    engine_parts_status: Optional[str] = Field(None, max_length=100, description="Engine parts availability")
    accessories_status: Optional[str] = Field(None, max_length=100, description="Accessories availability")

    # ===== FUEL & PERFORMANCE =====
    fuel_consumption: Optional[float] = Field(None, ge=0, description="Average fuel consumption")
    fuel_consumption_unit: Optional[str] = Field(None, max_length=20, description="Unit: 'km/L' or 'L/100km'")

    # ===== BRAKES =====
    foot_brake_condition: Optional[str] = Field(None, max_length=50, description="Foot brake condition")
    disc_brake_available: Optional[bool] = Field(None, description="Disc brake available")
    parking_brake_condition: Optional[str] = Field(None, max_length=50, description="Parking brake condition")
    abs_available: Optional[bool] = Field(None, description="ABS available")

    # ===== FEATURES (JSONB) =====
    features: Optional[VehicleFeatures] = Field(None, description="Vehicle features")

    # ===== SUSPENSION (JSONB) =====
    suspension: Optional[VehicleSuspension] = Field(None, description="Suspension information")

    # ===== TYRES (JSONB) =====
    tyres: Optional[VehicleTyres] = Field(None, description="Tyre information")

    # ===== ELECTRICAL (JSONB) =====
    electrical: Optional[VehicleElectrical] = Field(None, description="Electrical system")

    # ===== LIGHTS (JSONB) =====
    lights: Optional[VehicleLights] = Field(None, description="Lights status")

    # ===== HISTORY =====
    has_accidents: Optional[bool] = Field(None, description="Has accident history")
    has_repairs: Optional[bool] = Field(None, description="Has repair history")
    needs_repairs_within_year: Optional[bool] = Field(None, description="Needs repairs within a year")
    body_parts_replaced: Optional[bool] = Field(None, description="Body parts have been replaced")

    # ===== VALUATION =====
    purchase_price: Optional[float] = Field(None, ge=0, description="Purchase price (LKR)")
    brand_new_price: Optional[float] = Field(None, ge=0, description="Brand new price (LKR)")
    market_value: Optional[float] = Field(None, ge=0, description="Market value (LKR)")
    forced_sale_value: Optional[float] = Field(None, ge=0, description="Forced sale value (LKR)")
    valuation_summary: Optional[str] = Field(None, description="Valuation summary text")

    # ===== OFFICE USE =====
    office_data: Optional[VehicleOfficeData] = Field(None, description="Office use only fields")

    # ===== PAST VALUATIONS =====
    past_valuations: Optional[List[VehiclePastValuation]] = Field(None, description="Past valuations for comparison")

    # ===== PHOTOS =====
    vehicle_photos: Optional[List[VehiclePhoto]] = Field(None, max_items=5, description="Vehicle photos (max 5)")
    book_images: Optional[List[VehiclePhoto]] = Field(None, max_items=5, description="Vehicle book images for OCR (max 5)")

    # ===== VALIDATORS =====
    @field_validator('date_of_first_registration')
    @classmethod
    def validate_vehicle_date(cls, v):
        """Validate and normalize date of first registration to DD-MM-YYYY or DD/MM/YYYY format."""
        if v is None:
            return v
        # Normalize common formats
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(f'Invalid date format: "{v}". Use DD-MM-YYYY format')
        return normalized

    @field_validator('registration_number')
    @classmethod
    def normalize_registration_number(cls, v):
        """Normalize vehicle registration number - uppercase and strip whitespace."""
        if v is None:
            return v
        return v.strip().upper()


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle"""
    pass


class VehicleUpdate(VehicleBase):
    """Schema for updating an existing vehicle"""
    pass


class VehicleResponse(VehicleBase):
    """Schema for vehicle response (includes ID and timestamps)"""
    id: int
    user_id: int
    is_deleted: Optional[bool] = False
    original_vehicle_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VehicleTemplateResponse(BaseModel):
    """Simplified vehicle response for Vehicle Library listing"""
    id: int
    make: Optional[str] = None
    model: Optional[str] = None
    registration_number: Optional[str] = None
    year_of_manufacture: Optional[int] = None
    market_value: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ReportVehicle Junction Schemas
class ReportVehicleBase(BaseModel):
    """Base schema for ReportVehicle junction"""
    vehicle_id: int = Field(..., description="ID of the vehicle")
    vehicle_order: int = Field(default=1, ge=1, description="Display order in report (for drag-drop)")
    report_specific_notes: Optional[str] = Field(None, description="Notes specific to this vehicle in this report")
    override_market_value: Optional[float] = Field(None, ge=0, description="Override market value for this report")


class ReportVehicleCreate(ReportVehicleBase):
    """Schema for creating a report-vehicle association"""
    pass


class ReportVehicleUpdate(BaseModel):
    """Schema for updating report-vehicle association"""
    vehicle_order: Optional[int] = Field(None, ge=1)
    report_specific_notes: Optional[str] = None
    override_market_value: Optional[float] = Field(None, ge=0)


class ReportVehicleResponse(ReportVehicleBase):
    """Schema for report-vehicle response (includes full vehicle data)"""
    id: int
    report_id: int
    vehicle: VehicleResponse  # Nested full vehicle data
    created_at: datetime

    class Config:
        from_attributes = True


# Vehicle Valuation Suggestion Schemas
class VehicleValuationSuggestion(BaseModel):
    """AI-generated valuation suggestion for a vehicle"""
    suggested_market_value: Optional[float] = Field(None, description="AI-suggested market value")
    suggested_forced_sale_value: Optional[float] = Field(None, description="AI-suggested forced sale value")
    suggested_brand_new_price: Optional[float] = Field(None, description="AI-suggested brand new price")
    valuation_summary: Optional[str] = Field(None, description="AI-generated valuation summary")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")
    reasoning: Optional[str] = Field(None, description="Explanation for the valuation")
