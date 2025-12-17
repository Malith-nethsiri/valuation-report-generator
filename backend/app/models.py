from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Numeric, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    honorific = Column(String(10), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)

    # Professional Credentials
    academic_qualifications = Column(Text, nullable=True)
    membership_level = Column(String(100), nullable=True)
    membership_number = Column(String(100), nullable=True)
    professional_designation = Column(String(200), nullable=True)
    panel_valuer_banks = Column(JSON, nullable=True)

    # Residential Address (structured for report formatting)
    house_number = Column(String(50), nullable=True)
    area_development = Column(String(100), nullable=True)
    village = Column(String(100), nullable=True)
    locality = Column(String(100), nullable=True)
    phone_primary = Column(String(50), nullable=True)
    phone_secondary = Column(String(50), nullable=True)

    # Office Information (optional)
    office_department = Column(String(200), nullable=True)
    office_region = Column(String(100), nullable=True)
    office_street_city = Column(String(200), nullable=True)
    office_phone = Column(String(50), nullable=True)

    # Letterhead template preference
    preferred_letterhead_template = Column(String(50), nullable=True, default='classic')

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to reports (with cascading delete)
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}', designation='{self.professional_designation}')>"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(100), nullable=False, default="residential_property")
    status = Column(String(50), nullable=False, default="draft")  # draft, completed

    # Property & Plan Information
    property_lot_description = Column(String(200), nullable=True)  # e.g., "Lot 15", "Lots 1 & 2"
    plan_number = Column(String(100), nullable=True)  # e.g., "1035", "2005/65"
    plan_date = Column(String(50), nullable=True)  # DD-MM-YYYY format
    licensed_surveyor_name = Column(String(255), nullable=True)

    # Property Identification Type (new) - UPDATED: Now supports hybrid mode
    property_identification_type = Column(String(50), nullable=True)  # "plan", "deed", "plan_and_deed", "certificate_of_sale", NULL for old reports

    # Property Identification Documents Metadata (JSON) - NEW: Track which documents user has
    # Format: {"has_plan": bool, "has_deed": bool, "has_certificate": bool, "primary_type": str}
    property_identification_documents = Column(JSON, nullable=True)

    # Applicant Information
    applicant_title = Column(String(20), nullable=True)  # Mr./Mrs./Miss./Dr.
    applicant_full_name = Column(String(500), nullable=True)
    applicant_id_type = Column(String(50), nullable=True)  # Passport, NIC, Other
    applicant_id_number = Column(String(100), nullable=True)
    applicant_address_line1 = Column(String(500), nullable=True)  # house/plot, street
    applicant_address_line2 = Column(String(500), nullable=True)  # village/area
    applicant_district = Column(String(100), nullable=True)
    applicant_province = Column(String(100), nullable=True)
    applicant_country = Column(String(100), nullable=True, default="Sri Lanka")

    # Valuation Purpose
    valuation_type = Column(String(100), nullable=True)  # Market Value, Present Market Value, etc.
    property_ownership = Column(String(200), nullable=True)  # "owned by him", "owned by her", etc.
    property_type_valued = Column(String(200), nullable=True)  # immovable property, movable & immovable properties

    # Valuation Purpose (new)
    valuation_purpose = Column(String(200), nullable=True)  # Purpose of the valuation report

    # Additional Property Owner (optional)
    has_additional_owner = Column(String(10), nullable=True)  # "yes" or "no"
    additional_owner_names = Column(Text, nullable=True)

    # Deed Information (stored as JSON for multiple deeds)
    has_deed_info = Column(String(10), nullable=True)  # "yes" or "no"
    deeds = Column(JSON, nullable=True)  # Array of deed objects

    # Submission Destination
    submission_organization = Column(Text, nullable=True)
    submission_address = Column(Text, nullable=True)

    # Date of Inspection
    inspection_date = Column(String(50), nullable=True)  # DD-MM-YYYY format

    # Special Notes (optional)
    has_special_note = Column(String(10), nullable=True)  # "yes" or "no"
    special_note_text = Column(Text, nullable=True)

    # Report metadata (keeping for compatibility)
    report_reference = Column(String(100), nullable=True)
    report_date = Column(String(50), nullable=True)

    # ===== PROPERTY LOCATION & ACCESS (Phase 2) =====

    # Property Location Information
    use_applicant_address_as_property = Column(Boolean, nullable=True, default=False)  # Checkbox to reuse applicant address
    property_name = Column(String(200), nullable=True)  # Optional property name (e.g., "Searock The Kings Domain")
    assessment_number = Column(String(100), nullable=True)  # Optional assessment number
    property_address_full = Column(Text, nullable=True)  # Full formatted address from Google Places
    property_village = Column(String(200), nullable=True)  # Village name (from Google or manual)
    property_divisional_secretariat = Column(String(200), nullable=True)  # Divisional Secretariat division
    property_district = Column(String(100), nullable=True)  # District (from Google or manual)
    property_province = Column(String(100), nullable=True)  # Province (from Google or manual)
    property_latitude = Column(Numeric(10, 8), nullable=True)  # GPS latitude (8 decimal places)
    property_longitude = Column(Numeric(11, 8), nullable=True)  # GPS longitude (8 decimal places)

    # Sri Lankan Administrative Subdivisions (Phase 2 - Enhancement)
    property_number = Column(String(50), nullable=True)  # Property number within village (e.g., "No: 1202")
    grama_niladari_division = Column(String(200), nullable=True)  # Grama Niladari Division (smallest admin unit)
    korale = Column(String(300), nullable=True)  # Korale (traditional administrative division)
    pradeshiya_sabha = Column(String(200), nullable=True)  # Pradeshiya Sabha (if applicable)
    ward_number = Column(String(20), nullable=True)  # Ward number (for urban/municipal areas)
    is_municipal_limit = Column(Boolean, nullable=True, default=False)  # Within Municipal Council limit
    location_direction = Column(String(50), nullable=True)  # Direction from town center (e.g., "north-east")

    # Access Directions Information
    access_starting_point_name = Column(Text, nullable=True)  # Starting landmark name (e.g., "Rambukkana Bus Stand")
    access_starting_point_latitude = Column(Numeric(10, 8), nullable=True)  # Starting point GPS latitude
    access_starting_point_longitude = Column(Numeric(11, 8), nullable=True)  # Starting point GPS longitude
    access_route_data = Column(JSON, nullable=True)  # Raw Google Directions API response
    access_directions_text = Column(Text, nullable=True)  # Editable professional directions text
    access_distance_km = Column(Numeric(10, 2), nullable=True)  # Route distance in kilometers
    access_duration_minutes = Column(Integer, nullable=True)  # Estimated travel time in minutes
    access_road_type = Column(String(200), nullable=True)  # Road type description (e.g., "highway", "gravelly motorable")
    property_road_position = Column(String(100), nullable=True)  # Position relative to road (e.g., "left side", "right side")
    location_map_image_data = Column(Text, nullable=True)  # Static map image URL or base64 data
    access_road_segments = Column(JSON, nullable=True)  # DEPRECATED: Detailed road segment information (kept for backward compatibility)
    access_road_conditions = Column(JSON, nullable=True)  # NEW: Simplified road conditions array [{road_type, condition, notes}]
    access_entry_mode = Column(String(20), nullable=True)  # NEW: Entry mode for road conditions ('simple' or 'advanced')

    # ===== PROPERTY HEADER FIELDS (Land Extent, Boundaries, Physical Features) =====

    # Land Extent (Acres-Roods-Perches format)
    land_extent_acres = Column(Numeric(8, 2), nullable=True)  # 0-999999.99 acres
    land_extent_roods = Column(Integer, nullable=True)  # 0-3 roods (1 acre = 4 roods)
    land_extent_perches = Column(Numeric(6, 2), nullable=True)  # 0-39.99 perches (1 rood = 40 perches)
    land_extent_hectares = Column(Numeric(10, 4), nullable=True)  # Auto-calculated from A-R-P
    land_extent_square_meters = Column(Numeric(12, 2), nullable=True)  # Auto-calculated
    land_extent_formatted = Column(String(50), nullable=True)  # Auto-generated: "00A-0R-13.8P"

    # Traditional/Historical Land Name
    land_traditional_name = Column(String(300), nullable=True)  # e.g., "Hakuruketiyawe Wela alias Hakuruketiyawe watta now Poranewatta"

    # Boundary Information (Hybrid: structured + free text)
    # Structure: {"north": {"description": "...", "length": "...", "adjoins": "...", "notes": "..."}, "south": {...}, "east": {...}, "west": {...}}
    boundaries = Column(JSON, nullable=True)

    # Physical Boundaries
    physical_boundaries_types = Column(JSON, nullable=True)  # Array: ["brick_walls", "barbed_wire", "live_fence", "concrete_posts", "iron_gate", "rubble_foundation"]
    physical_boundaries_description = Column(Text, nullable=True)

    # Boundary Types Per Direction (for professional summary generation)
    # Structure: {"north": "brick_walls", "south": "barbed_wire", "east": "brick_walls", "west": "live_fence"}
    boundary_types_per_direction = Column(JSON, nullable=True)

    # Entrance/Gate Type
    entrance_type = Column(String(100), nullable=True)  # "auto_roller_gate", "iron_gate", "wooden_gate", "no_gate", etc.

    # Auto-generated (editable) boundary summary sentence
    boundaries_summary_text = Column(Text, nullable=True)  # Custom text description

    # Multiple Lots Support (optional, for subdivided properties)
    has_multiple_lots = Column(Boolean, nullable=True, default=False)
    # Structure: [{"lot_number": "1", "extent": {"acres": 0, "roods": 3, "perches": 8.50, "hectares": 0.3250}, "boundaries": {...}, "physical_boundaries": {...}}]
    lots_data = Column(JSON, nullable=True)

    # OCR Document Processing Support
    # Structure: [{"filename": "plan.pdf", "type": "survey_plan", "uploaded_at": "2024-01-15", "ocr_processed": true, "file_path": "..."}]
    uploaded_documents = Column(JSON, nullable=True)
    # Structure: {"plan_number": {"source": "ocr"|"manual"|"api", "confidence": 0.95, "timestamp": "..."}, ...}
    field_sources = Column(JSON, nullable=True)

    # Survey Plan Additional Details
    survey_plan_scale = Column(String(50), nullable=True)  # e.g., "1:500", "1:1000"
    plan_reference_notes = Column(Text, nullable=True)  # Additional plan information

    # ===== DESCRIPTION OF PROPERTY =====
    land_shape = Column(String(50), nullable=True)
    land_type = Column(String(50), nullable=True)
    land_frontage_type = Column(String(100), nullable=True)
    land_frontage_width = Column(Numeric(6, 2), nullable=True)
    land_frontage_description = Column(Text, nullable=True)
    land_level = Column(String(50), nullable=True)
    land_level_difference = Column(Numeric(8, 2), nullable=True)
    soil_type = Column(String(50), nullable=True)
    water_table_depth = Column(Numeric(8, 2), nullable=True)
    flood_risk = Column(String(50), nullable=True)
    inundation_risk = Column(String(50), nullable=True)
    earth_slip_risk = Column(String(50), nullable=True)
    land_condition = Column(String(50), nullable=True)
    land_condition_description = Column(Text, nullable=True)
    land_description_text = Column(Text, nullable=True)

    # Topographical Features
    elevation_changes = Column(String(50), nullable=True)
    drainage_pattern = Column(String(50), nullable=True)
    vegetation_type = Column(String(50), nullable=True)
    natural_features = Column(Text, nullable=True)

    # ===== BUILDING DETAILS =====
    buildings = Column(JSON, nullable=True)
    occupier_name = Column(String(300), nullable=True)
    occupier_relationship = Column(String(50), nullable=True)

    # ===== PROPERTY PHOTOS =====
    property_photos = Column(JSON, nullable=True)

    # ===== LOCALITY INFORMATION =====

    # Distance to major town/city
    distance_to_major_town_km = Column(Numeric(6, 2), nullable=True)  # Distance in kilometers
    major_town_name = Column(String(200), nullable=True)  # Name of the nearest major town

    # Nearby facilities (JSON array)
    # Structure: [{"type": "hospital", "name": "Rambukkana Base Hospital", "distance_km": 2.5, "latitude": 7.xxx, "longitude": 80.xxx, "selected": true}, ...]
    nearby_facilities = Column(JSON, nullable=True)

    # Infrastructure & Utilities
    has_electricity = Column(Boolean, nullable=True, default=True)
    water_supply_type = Column(String(50), nullable=True)  # pipe_borne_water, bore_water, well_water, none
    telecommunication_types = Column(JSON, nullable=True)  # Array: ["landline", "mobile_coverage"]
    internet_types = Column(JSON, nullable=True)  # Array: ["fiber", "mobile_data"]

    # Public Transport
    has_public_transport = Column(Boolean, nullable=True)
    public_transport_routes = Column(Text, nullable=True)  # Description of routes
    public_transport_frequency = Column(String(200), nullable=True)  # e.g., "Every 15 minutes", "Hourly"
    nearest_bus_stop_distance_km = Column(Numeric(6, 2), nullable=True)
    nearest_bus_stop_name = Column(String(200), nullable=True)
    nearest_railway_station = Column(String(200), nullable=True)
    nearest_railway_distance_km = Column(Numeric(6, 2), nullable=True)

    # Area Characteristics
    area_type = Column(String(50), nullable=True)  # residential, commercial, industrial, mixed, agricultural, tourist
    development_level = Column(String(50), nullable=True)  # well_developed, developing, moderate, undeveloped
    predominant_building_type = Column(String(100), nullable=True)  # single_storey_residential, multi_storey_residential, apartments, commercial_buildings, mixed

    # Tourism/Special characteristics
    is_tourist_area = Column(Boolean, nullable=True, default=False)
    tourist_attractions_nearby = Column(Text, nullable=True)

    # Auto-generated (editable) locality narrative
    locality_description_text = Column(Text, nullable=True)  # Professional narrative text for LOCALITY section

    # ===== LEGAL ASPECTS =====
    ownership_type = Column(String(200), nullable=True)
    street_lines_status = Column(String(200), nullable=True)
    building_limits_status = Column(String(200), nullable=True)
    local_authority_data = Column(Text, nullable=True)
    rent_act_effectiveness = Column(String(200), nullable=True)

    # Ownership & Title - Extended fields
    title_search_conducted = Column(String(3), nullable=True)  # "Yes"/"No"
    pedigree_search_conducted = Column(String(3), nullable=True)  # "Yes"/"No"
    valuation_basis_note = Column(Text, nullable=True)  # Custom basis statement
    property_encumbered = Column(String(3), nullable=True)  # "Yes"/"No"
    encumbrance_type = Column(String(100), nullable=True)  # "Mortgage"/"Life Interest"/etc.
    encumbrance_details = Column(Text, nullable=True)  # Bank name, mortgagee details

    # Street Lines - Extended fields
    street_lines_gazette_ref = Column(String(100), nullable=True)  # Gazette reference
    street_lines_gazette_date = Column(String(20), nullable=True)  # Gazette date
    street_lines_impact_description = Column(Text, nullable=True)  # Detailed impact

    # Building Limits - Extended fields
    building_distance_from_road = Column(String(50), nullable=True)  # Distance measurement
    building_plan_approved = Column(String(20), nullable=True)  # "Yes"/"No"/"Not Applicable"
    building_plan_reference = Column(String(200), nullable=True)  # Plan ref number
    building_approval_authority = Column(String(200), nullable=True)  # Approval authority
    building_within_limits = Column(String(3), nullable=True)  # "Yes"/"No"

    # Local Authority - Extended fields
    local_authority_rated = Column(String(3), nullable=True)  # "Yes"/"No"
    local_authority_tax_levy = Column(Text, nullable=True)  # Tax information

    # ===== LAND VALUES =====
    comparable_properties = Column(JSON, nullable=True)  # Array of comparables
    land_market_analysis = Column(Text, nullable=True)

    # ===== VALUATION =====
    valuation_land_extent = Column(Numeric(10, 2), nullable=True)
    valuation_rate_per_perch = Column(Numeric(12, 2), nullable=True)
    valuation_total_land_value = Column(Numeric(15, 2), nullable=True)
    valuation_buildings_data = Column(JSON, nullable=True)  # Array per building
    valuation_total_buildings_value = Column(Numeric(15, 2), nullable=True)
    valuation_addons = Column(JSON, nullable=True)
    valuation_total_addons_value = Column(Numeric(15, 2), nullable=True)
    valuation_market_value = Column(Numeric(15, 2), nullable=True)
    valuation_forced_sale_percentage = Column(Numeric(5, 2), nullable=True)
    valuation_forced_sale_value = Column(Numeric(15, 2), nullable=True)
    valuation_insurance_value = Column(Numeric(15, 2), nullable=True)
    valuation_manual_overrides = Column(JSON, nullable=True)  # Track manual edits

    # ===== CERTIFICATION =====
    certification_text = Column(Text, nullable=True)
    certificate_survey_plan_ref = Column(String(200), nullable=True)
    certificate_survey_plan_date = Column(String(50), nullable=True)
    certificate_identity_confirmed = Column(Boolean, default=False)
    certification_valuer_name = Column(String(300), nullable=True)
    certification_valuer_designation = Column(String(200), nullable=True)
    certification_date = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to user
    user = relationship("User", back_populates="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, user_id={self.user_id}, type='{self.report_type}', status='{self.status}')>"
