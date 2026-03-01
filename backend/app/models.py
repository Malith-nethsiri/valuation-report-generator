from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Numeric, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import uuid
import enum


class JobType(str, enum.Enum):
    """Types of background jobs."""
    DOCX_GENERATION = "docx_generation"
    PDF_GENERATION = "pdf_generation"


class JobStatus(str, enum.Enum):
    """Status states for background jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """
    Job model for tracking async document generation tasks.

    Used for long-running operations like DOCX/PDF generation
    that should not block the API response.
    """
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)

    job_type = Column(String(50), nullable=False)  # 'docx_generation', 'pdf_generation'
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'processing', 'completed', 'failed'

    # Result data
    result_url = Column(String(500), nullable=True)  # Path to generated file
    result_filename = Column(String(255), nullable=True)  # Original filename
    error_message = Column(Text, nullable=True)  # Error details if failed

    # Progress tracking (optional)
    progress_percent = Column(Integer, nullable=True, default=0)  # 0-100
    progress_message = Column(String(255), nullable=True)  # Current step description

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    report = relationship("Report")

    def __repr__(self):
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    honorific = Column(String(10), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)

    # User Role for RBAC
    role = Column(String(20), nullable=False, default='user')  # 'user', 'admin'

    # Password Reset Fields
    # Token is stored as bcrypt hash (not plaintext) for security
    password_reset_token = Column(String(255), nullable=True)  # Hashed token
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    # Email Verification Fields
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)

    # OAuth Fields
    google_id = Column(String(255), nullable=True, unique=True, index=True)
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'facebook', etc.

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

    # Bank Account Management
    bank_accounts = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (with cascading delete)
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    properties = relationship("Property", back_populates="user", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}', designation='{self.professional_designation}')>"


class PropertyDataMixin:
    """
    Mixin containing all property data columns shared between Report and Property models.

    This mixin defines ~132 columns that are identical in both the reports and properties
    tables, covering: property identification, location, access directions, land extent,
    boundaries, property description, buildings, photos, locality, legal aspects,
    comparable properties, and valuation data.

    Using a mixin eliminates code duplication while keeping the database schema unchanged -
    each table still has its own copy of these columns.

    Data Category Legend (see backend/app/utils/field_categories.py for full mapping):
      [P:C] Paper-Based / Client Document  — survey plan, deed, applicant info
      [P:O] Paper-Based / Official Record  — gazette, building approval, local authority
      [I]   Inspection-Based              — physically observed / measured on-site
      [CD]  Computed / Derived            — AI, Google Maps, extent calculator, system
      [VJ]  Valuation Judgment            — comparables, rates, final professional values
    """

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Survey Plan & Property ID =====
    lot_number = Column(String(200), nullable=True)                    # [P:C] From survey plan
    plan_number = Column(String(100), nullable=True)                   # [P:C] From survey plan
    plan_date = Column(String(50), nullable=True)                      # [P:C] From survey plan
    licensed_surveyor_name = Column(String(255), nullable=True)        # [P:C] From survey plan
    property_identification_type = Column(String(50), nullable=True)   # [P:C] plan/deed/certificate
    property_identification_documents = Column(JSON, nullable=True)    # [CD]  Uploaded file metadata

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Deed Information =====
    has_deed_info = Column(String(10), nullable=True)                  # [P:C] Boolean flag
    deeds = Column(JSON, nullable=True)                                # [P:C] Deed details array

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Additional Owner =====
    has_additional_owner = Column(String(10), nullable=True)           # [P:C] From client info
    additional_owner_names = Column(Text, nullable=True)               # [P:C] From client info

    # ===== [I] INSPECTION-BASED — Site Visit Metadata =====
    inspection_date = Column(String(50), nullable=True)                # [I]  Date of physical site visit

    # ===== [P:O] / [CD] PROPERTY LOCATION =====
    assessment_number = Column(String(100), nullable=True)             # [P:O] Rates assessment notice
    property_village = Column(String(200), nullable=True)              # [P:C] From plan / client
    property_divisional_secretariat = Column(String(200), nullable=True)  # [P:O] Admin division record
    property_district = Column(String(100), nullable=True)             # [P:O] Admin division record
    property_province = Column(String(100), nullable=True)             # [P:O] Admin division record
    property_latitude = Column(Numeric(10, 8), nullable=True)          # [CD]  Google Maps API
    property_longitude = Column(Numeric(11, 8), nullable=True)         # [CD]  Google Maps API
    property_number = Column(String(50), nullable=True)                # [P:O] Authority records
    grama_niladari_division = Column(String(200), nullable=True)       # [P:O] Admin division record
    hathpaththuwa = Column(String(300), nullable=True)                 # [P:O] Admin division record
    korale = Column(String(300), nullable=True)                        # [P:O] Admin division record
    pradeshiya_sabha = Column(String(200), nullable=True)              # [P:O] Admin division record
    ward_number = Column(String(20), nullable=True)                    # [P:O] Admin division record
    location_direction = Column(String(50), nullable=True)             # [I]  Physically observed on-site

    # ===== [I] / [CD] ACCESS DIRECTIONS =====
    access_starting_point_name = Column(Text, nullable=True)           # [I]  Valuer's starting point
    access_starting_point_latitude = Column(Numeric(10, 8), nullable=True)   # [CD]  Google Maps
    access_starting_point_longitude = Column(Numeric(11, 8), nullable=True)  # [CD]  Google Maps
    access_route_data = Column(JSON, nullable=True)                    # [CD]  Google Maps route
    access_directions_text = Column(Text, nullable=True)               # [CD]  Google Directions / manual
    access_distance_km = Column(Numeric(10, 2), nullable=True)         # [CD]  Google Maps calculated
    access_duration_minutes = Column(Integer, nullable=True)           # [CD]  Google Maps calculated
    access_road_type = Column(String(200), nullable=True)              # [I]  Observed on-site
    property_road_position = Column(String(100), nullable=True)        # [I]  Observed on-site
    location_map_image_data = Column(Text, nullable=True)              # [CD]  Google Maps Static image
    access_road_conditions = Column(JSON, nullable=True)               # [I]  On-site road assessment
    access_entry_mode = Column(String(20), nullable=True)              # [I]  Observed on-site
    access_road_classes_detected = Column(JSON, nullable=True)         # [CD]  System / AI detected

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Land Extent (from survey plan) =====
    land_extent_acres = Column(Numeric(8, 2), nullable=True)           # [P:C] From survey plan
    land_extent_roods = Column(Integer, nullable=True)                 # [P:C] From survey plan
    land_extent_perches = Column(Numeric(6, 2), nullable=True)         # [P:C] From survey plan
    land_extent_hectares = Column(Numeric(10, 4), nullable=True)       # [CD]  Auto-calculated (extent_calculator)
    land_extent_square_meters = Column(Numeric(12, 2), nullable=True)  # [CD]  Auto-calculated (extent_calculator)
    land_extent_formatted = Column(String(50), nullable=True)          # [CD]  Display string e.g. "0A-1R-13.8P"
    land_traditional_name = Column(String(300), nullable=True)         # [P:C] From survey plan

    # ===== [P:C] / [I] / [CD] BOUNDARIES =====
    boundaries = Column(JSON, nullable=True)                           # [P:C] Legal boundary from survey plan
    physical_boundaries_types = Column(JSON, nullable=True)            # [I]  What physically exists on-site
    physical_boundaries_description = Column(Text, nullable=True)      # [I]  On-site physical description
    boundary_types_per_direction = Column(JSON, nullable=True)         # [I]  Physical type per direction
    entrance_type = Column(String(100), nullable=True)                 # [I]  Physical gate type observed
    boundaries_summary_text = Column(Text, nullable=True)              # [CD]  Auto-generated summary
    lots_data = Column(JSON, nullable=True)                            # [P:C] Multiple lots breakdown

    # ===== [CD] COMPUTED — OCR Document Processing =====
    uploaded_documents = Column(JSON, nullable=True)                   # [CD]  File upload metadata
    field_sources = Column(JSON, nullable=True)                        # [CD]  Per-field source + category tracking
    survey_plan_scale = Column(String(50), nullable=True)              # [P:C] From survey plan (OCR-extracted)
    plan_reference_notes = Column(Text, nullable=True)                 # [P:C] From survey plan (OCR-extracted)

    # ===== [I] INSPECTION-BASED — Land Physical Characteristics =====
    land_shape = Column(String(50), nullable=True)                     # [I]  Observed on-site
    land_type = Column(String(50), nullable=True)                      # [I]  Assessed on-site
    land_frontage_type = Column(String(100), nullable=True)            # [I]  Observed on-site
    land_frontage_width = Column(Numeric(6, 2), nullable=True)         # [I]  Measured on-site (metres)
    land_frontage_description = Column(Text, nullable=True)            # [I]  Described from inspection
    land_level = Column(String(50), nullable=True)                     # [I]  Observed on-site
    land_level_difference = Column(Numeric(8, 2), nullable=True)       # [I]  Measured on-site (metres)
    soil_type = Column(String(50), nullable=True)                      # [I]  Observed / assessed on-site
    water_table_depth = Column(Numeric(8, 2), nullable=True)           # [I]  Assessed on-site
    flood_risk = Column(String(50), nullable=True)                     # [I]  Assessed on-site
    inundation_risk = Column(String(50), nullable=True)                # [I]  Assessed on-site
    earth_slip_risk = Column(String(50), nullable=True)                # [I]  Assessed on-site
    land_condition = Column(String(50), nullable=True)                 # [I]  Assessed on-site
    land_condition_description = Column(Text, nullable=True)           # [I]  Free-text from inspection
    land_description_text = Column(Text, nullable=True)                # [CD]  AI-generated (Claude)

    # [I] Topographical Features — observed on-site
    elevation_changes = Column(String(50), nullable=True)              # [I]  Observed on-site
    drainage_pattern = Column(String(50), nullable=True)               # [I]  Observed on-site
    vegetation_type = Column(String(50), nullable=True)                # [I]  Observed on-site
    natural_features = Column(Text, nullable=True)                     # [I]  Observed on-site

    # ===== [I] INSPECTION-BASED — Buildings (all sub-fields observed on-site) =====
    buildings = Column(JSON, nullable=True)                            # [I]  Full nested building structure
    occupier_name = Column(String(300), nullable=True)                 # [I]  Ascertained on-site
    occupier_relationship = Column(String(50), nullable=True)          # [I]  Ascertained on-site

    # ===== [I] INSPECTION-BASED — Site Photography =====
    property_photos = Column(JSON, nullable=True)                      # [I]  Photographed during site visit

    # ===== [I] / [CD] LOCALITY INFORMATION =====
    distance_to_major_town_km = Column(Numeric(6, 2), nullable=True)   # [I]  Estimated during site visit
    major_town_name = Column(String(200), nullable=True)               # [I]  Known from site visit
    nearby_facilities = Column(JSON, nullable=True)                    # [CD]  Google Places API
    water_supply_type = Column(JSON, nullable=True)                    # [I]  Physically confirmed on-site
    telecommunication_types = Column(JSON, nullable=True)              # [I]  Physically confirmed on-site
    internet_types = Column(JSON, nullable=True)                       # [I]  Physically confirmed on-site
    has_public_transport = Column(Boolean, nullable=True)              # [I]  Observed on-site
    public_transport_routes = Column(Text, nullable=True)              # [I]  Observed on-site
    public_transport_frequency = Column(String(200), nullable=True)    # [I]  Observed on-site
    nearest_bus_stop_distance_km = Column(Numeric(6, 2), nullable=True)  # [I]  Estimated during visit
    nearest_bus_stop_name = Column(String(200), nullable=True)         # [I]  Observed during site visit
    nearest_railway_station = Column(String(200), nullable=True)       # [I]  Known from site area
    nearest_railway_distance_km = Column(Numeric(6, 2), nullable=True) # [I]  Estimated during visit
    area_type = Column(String(50), nullable=True)                      # [I]  Professionally assessed on-site
    development_level = Column(String(50), nullable=True)              # [I]  Professionally assessed on-site
    predominant_building_type = Column(JSON, nullable=True)            # [I]  Observed on-site
    tourist_attractions_nearby = Column(Text, nullable=True)           # [I]  Known from site visit
    locality_description_text = Column(Text, nullable=True)            # [CD]  AI-generated (Claude)

    # ===== [P:O] PAPER-BASED: OFFICIAL RECORDS — Legal Aspects =====
    ownership_type = Column(String(200), nullable=True)                # [P:O] From title deed / registry
    street_lines_status = Column(String(200), nullable=True)           # [P:O] From gazette / authority
    building_limits_status = Column(String(200), nullable=True)        # [P:O] From local authority records
    local_authority_data = Column(Text, nullable=True)                 # [P:O] From local authority records
    rent_act_effectiveness = Column(String(200), nullable=True)        # [P:O] From legal records
    title_search_conducted = Column(String(3), nullable=True)          # [P:O] Paper search activity
    pedigree_search_conducted = Column(String(3), nullable=True)       # [P:O] Paper search activity
    valuation_basis_note = Column(Text, nullable=True)                 # [P:O] Legal basis statement
    property_encumbered = Column(String(3), nullable=True)             # [P:O] From encumbrance records
    encumbrance_type = Column(String(100), nullable=True)              # [P:O] From encumbrance records
    encumbrance_details = Column(Text, nullable=True)                  # [P:O] From encumbrance records
    street_lines_gazette_ref = Column(String(100), nullable=True)      # [P:O] From gazette publication
    street_lines_gazette_date = Column(String(20), nullable=True)      # [P:O] From gazette publication
    street_lines_impact_description = Column(Text, nullable=True)      # [P:O] Derived from gazette
    building_distance_from_road = Column(String(50), nullable=True)    # [P:O] From building approval
    building_plan_approved = Column(String(20), nullable=True)         # [P:O] From building plan document
    building_plan_reference = Column(String(200), nullable=True)       # [P:O] From building plan document
    building_approval_authority = Column(String(200), nullable=True)   # [P:O] From approval authority
    building_within_limits = Column(String(3), nullable=True)          # [P:O] From authority records
    local_authority_rated = Column(String(3), nullable=True)           # [P:O] From authority records
    local_authority_tax_levy = Column(Text, nullable=True)             # [P:O] From authority records

    # ===== [VJ] VALUATION JUDGMENT — Comparable Properties & Land Values =====
    comparable_properties = Column(JSON, nullable=True)                # [VJ]  Valuation market research
    land_market_analysis = Column(Text, nullable=True)                 # [VJ]  Professional market analysis

    # ===== [VJ] VALUATION JUDGMENT — Professional Valuation Figures =====
    valuation_land_extent = Column(Numeric(10, 2), nullable=True)      # [VJ]  Appraisal extent (may differ from plan)
    valuation_rate_per_perch = Column(Numeric(12, 2), nullable=True)   # [VJ]  Rate from comparables analysis
    valuation_total_land_value = Column(Numeric(15, 2), nullable=True) # [VJ]  rate × extent
    valuation_buildings_data = Column(JSON, nullable=True)             # [VJ]  Per-building replacement cost
    valuation_total_buildings_value = Column(Numeric(15, 2), nullable=True)  # [VJ]  Sum of building values
    valuation_addons = Column(JSON, nullable=True)                     # [VJ]  Add-on items (pool, wall, etc.)
    valuation_total_addons_value = Column(Numeric(15, 2), nullable=True)     # [VJ]  Sum of add-ons
    valuation_market_value = Column(Numeric(15, 2), nullable=True)     # [VJ]  Final market value opinion
    valuation_forced_sale_percentage = Column(Numeric(5, 2), nullable=True)  # [VJ]  Forced sale %
    valuation_forced_sale_value = Column(Numeric(15, 2), nullable=True)      # [VJ]  Calculated forced sale value
    valuation_insurance_value = Column(Numeric(15, 2), nullable=True)  # [VJ]  Insurance replacement value
    valuation_manual_overrides = Column(JSON, nullable=True)           # [VJ]  Tracks user-overridden values


class Report(PropertyDataMixin, Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Added index for query performance
    report_type = Column(String(100), nullable=False, default="residential_property", index=True)
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, completed

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Applicant Information =====
    applicant_title = Column(String(20), nullable=True)                # [P:C] Mr./Mrs./Miss./Dr.
    applicant_full_name = Column(String(500), nullable=True)           # [P:C] Client identity
    applicant_id_type = Column(String(50), nullable=True)              # [P:C] Passport, NIC, Other
    applicant_id_number = Column(String(100), nullable=True)           # [P:C] From client document
    applicant_address_line1 = Column(String(500), nullable=True)       # [P:C] house/plot, street
    applicant_address_line2 = Column(String(500), nullable=True)       # [P:C] village/area
    applicant_district = Column(String(100), nullable=True)            # [P:C] From client info
    applicant_province = Column(String(100), nullable=True)            # [P:C] From client info
    applicant_country = Column(String(100), nullable=True, default="Sri Lanka")  # [P:C]

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Request Context =====
    request_type = Column(String(50), nullable=True)                   # [P:C] client_request / organization_request
    applicant_contact_number = Column(String(50), nullable=True)       # [P:C] Client contact

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Valuation Purpose =====
    valuation_type = Column(String(100), nullable=True)                # [P:C] Market Value, Present Market Value, etc.
    property_type_valued = Column(String(200), nullable=True)          # [P:C] Immovable property, etc.
    valuation_purpose = Column(String(200), nullable=True)             # [P:C] Purpose of the valuation report

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Submission Destination =====
    submission_organization = Column(Text, nullable=True)              # [P:C] Receiving organisation
    submission_address = Column(Text, nullable=True)                   # [P:C] Submission address
    submission_recipient_position = Column(String(200), nullable=True) # [P:C] Manager, Credit Officer, etc.

    # ===== [P:C] PAPER-BASED: CLIENT DOCUMENTS — Special Notes & Report Meta =====
    has_special_note = Column(String(10), nullable=True)               # [P:C] "yes" or "no"
    special_note_text = Column(Text, nullable=True)                    # [P:C] Conditional note text
    report_reference = Column(String(100), nullable=True)              # [P:C] Valuer's reference number
    report_date = Column(String(50), nullable=True)                    # [P:C] Date of report

    # ===== [CD] COMPUTED — Convenience & System Flags =====
    use_applicant_address_as_property = Column(Boolean, nullable=True, default=False)  # [CD] UI convenience flag

    # ===== [I] INSPECTION-BASED — Site Condition Flags =====
    is_municipal_limit = Column(Boolean, nullable=True, default=False) # [P:O] Within Municipal Council limit
    has_multiple_lots = Column(Boolean, nullable=True, default=False)  # [I]  Observed on-site
    has_electricity = Column(Boolean, nullable=True, default=True)     # [I]  Confirmed on-site
    is_tourist_area = Column(Boolean, nullable=True, default=False)    # [I]  Assessed during visit

    # Development feasibility/construction status (Report-only)
    ongoing_construction_notes = Column(Text, nullable=True)           # [I]  Observed on-site

    # ===== [CD] COMPUTED / DERIVED — Certification (auto-filled from User profile) =====
    certification_text = Column(Text, nullable=True)                   # [CD]  Pre-filled template
    certificate_identity_confirmed = Column(Boolean, default=False)    # [CD]  Auto-populated
    certification_valuer_name = Column(String(300), nullable=True)     # [CD]  From User.full_name
    certification_valuer_designation = Column(String(200), nullable=True)  # [CD]  From User.professional_designation
    certification_date = Column(String(50), nullable=True)             # [CD]  From report_date / today

    # ===== [CD] / [VJ] MULTI-PROPERTY SUPPORT =====
    is_multi_property = Column(Boolean, default=False, nullable=False)   # [CD]  System-set flag
    property_count = Column(Integer, default=1, nullable=False)          # [CD]  System-set count
    total_valuation_amount = Column(Numeric(15, 2), nullable=True)       # [VJ]  Sum of all property values
    invoice_data = Column(JSON, nullable=True)  # [CD]  {items, subtotal, discount, total, payment_terms, bank_details}

    # ===== VEHICLE REPORT SUPPORT =====
    primary_vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)  # For standalone vehicle reports
    is_office_use = Column(Boolean, default=False, nullable=True)  # Office/Private distinction
    vehicle_count = Column(Integer, default=0, nullable=True)      # Number of vehicles in report

    # ===== VEHICLE REPORT HEADER FIELDS =====
    folio_number = Column(String(100), nullable=True)     # Manual entry by user
    inspection_place = Column(Text, nullable=True)        # Free text entry

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="reports")
    property_associations = relationship("ReportProperty", back_populates="report", cascade="all, delete-orphan")
    vehicle_associations = relationship("ReportVehicle", back_populates="report", cascade="all, delete-orphan")
    primary_vehicle = relationship("Vehicle", foreign_keys=[primary_vehicle_id])

    @property
    def properties(self):
        """Get all properties for this report, ordered by property_order"""
        return [rp.property for rp in sorted(self.property_associations, key=lambda x: x.property_order)]

    @property
    def vehicles(self):
        """Get all vehicles for this report, ordered by vehicle_order"""
        return [rv.vehicle for rv in sorted(self.vehicle_associations, key=lambda x: x.vehicle_order)]

    def __repr__(self):
        return f"<Report(id={self.id}, user_id={self.user_id}, type='{self.report_type}', status='{self.status}', multi={self.is_multi_property})>"


class Property(PropertyDataMixin, Base):
    """
    Property model - stores individual property data for multi-property valuation reports.

    Each property represents a distinct piece of real estate with its own:
    - Location, access, and boundaries
    - Buildings and improvements
    - Valuation data
    - Legal aspects
    - Can be reused across multiple reports (Property Library feature)
    """
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Added index for query performance

    # Property Status & Type (for multi-property reports)
    status = Column(String(50), nullable=False, default="draft")  # 'draft' or 'completed'
    property_type = Column(String(50), nullable=False, default="residential")  # 'residential' or 'bare_land'

    # Fields with Property-specific defaults (differ from Report)
    is_municipal_limit = Column(Boolean, nullable=True)
    has_multiple_lots = Column(Boolean, nullable=True)
    has_electricity = Column(Boolean, nullable=True)
    is_tourist_area = Column(Boolean, nullable=True)

    # Property Owner (can differ from report applicant for family properties)
    property_owner_title = Column(String(20), nullable=True)
    property_owner_full_name = Column(String(500), nullable=True)
    property_owner_id_type = Column(String(50), nullable=True)
    property_owner_id_number = Column(String(100), nullable=True)

    # Property Library Support
    is_template = Column(Boolean, default=False, nullable=True)
    template_name = Column(String(200), nullable=True)
    last_valued_date = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="properties")
    report_associations = relationship("ReportProperty", back_populates="property", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Property(id={self.id}, lot='{self.lot_number}', village='{self.property_village}', district='{self.property_district}')>"


class ReportProperty(Base):
    """
    ReportProperty junction table - enables many-to-many relationship between Reports and Properties.

    Allows:
    - One report to contain multiple properties
    - One property to be included in multiple reports (reuse via Property Library)
    - Custom ordering of properties within a report (drag-drop support)
    - Per-report-property overrides (e.g., different valuation for different purposes)
    """
    __tablename__ = "report_properties"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)  # Added index
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)  # Added index
    property_order = Column(Integer, nullable=False, default=1)  # For drag-drop ordering

    # Optional per-report-property data
    report_specific_notes = Column(Text, nullable=True)
    override_market_value = Column(Numeric(15, 2), nullable=True)
    override_forced_sale_value = Column(Numeric(15, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    report = relationship("Report", back_populates="property_associations")
    property = relationship("Property", back_populates="report_associations")

    def __repr__(self):
        return f"<ReportProperty(report_id={self.report_id}, property_id={self.property_id}, order={self.property_order})>"


class Vehicle(Base):
    """
    Vehicle model for vehicle valuation reports.

    Supports:
    - All vehicle types (cars, motorcycles, trucks, special vehicles)
    - Standalone vehicle reports
    - Multi-property reports with mixed assets (properties + vehicles)
    - Vehicle Library feature for reuse across reports
    """
    __tablename__ = "vehicles"

    # Table-level constraints
    __table_args__ = (
        # Unique constraint: registration number must be unique per user (excluding deleted vehicles)
        # Note: This is enforced at the database level for data integrity
        UniqueConstraint('user_id', 'registration_number', name='uq_vehicle_user_registration'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status & Type
    status = Column(String(50), nullable=False, default="draft")  # 'draft' or 'completed'
    vehicle_type = Column(String(50), nullable=True)  # 'car', 'motorcycle', 'truck', 'special'
    is_template = Column(Boolean, default=False, nullable=True)  # For Vehicle Library
    is_deleted = Column(Boolean, default=False, nullable=True)  # Soft delete
    original_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)  # For duplicates

    # ===== VEHICLE IDENTIFICATION =====
    registration_number = Column(String(50), nullable=True, index=True)
    provincial_council = Column(String(100), nullable=True)  # Sri Lankan provinces
    class_of_vehicle = Column(String(100), nullable=True)  # Car, Van, SUV, Motorcycle, etc.
    body_colour = Column(String(100), nullable=True)
    chassis_number = Column(String(100), nullable=True)
    engine_number = Column(String(100), nullable=True)
    vehicle_status = Column(String(100), nullable=True)  # Registered, De-registered, Pending, Imported
    country_of_origin = Column(String(100), nullable=True)
    make = Column(String(100), nullable=True, index=True)  # Toyota, Honda, etc.
    model = Column(String(200), nullable=True)
    date_of_first_registration = Column(String(50), nullable=True)  # DD/MM/YYYY
    year_of_manufacture = Column(Integer, nullable=True)
    cylinder_capacity = Column(Integer, nullable=True)  # in cc
    fuel_type = Column(String(50), nullable=True)  # Petrol, Diesel, Hybrid, Electric, etc.
    mileage = Column(Integer, nullable=True)
    mileage_unit = Column(String(20), nullable=True, default="km")  # 'km' or 'miles'

    # ===== ENGINE & TRANSMISSION =====
    engine_type = Column(String(100), nullable=True)  # V6, Inline-4, etc.
    transmission = Column(String(50), nullable=True)  # Manual, Automatic, CVT, etc.
    wheel_drive = Column(String(20), nullable=True)  # 2WD, 4WD, AWD

    # ===== CONDITION FIELDS (separate columns for querying) =====
    running_condition = Column(String(50), nullable=True)  # Excellent/Good/Fair/Poor/Very Poor
    clutch_status = Column(String(100), nullable=True)  # Working Properly / Needs Adjustment / Needs Replacement
    engine_condition = Column(String(50), nullable=True)
    gear_box_condition = Column(String(50), nullable=True)
    differential_status = Column(String(100), nullable=True)  # Working Properly / Has Issues / Not Working
    gear_selection = Column(String(50), nullable=True)  # Smooth / Stiff / Difficult / Not Working
    body_condition = Column(String(50), nullable=True)
    chassis_condition = Column(String(50), nullable=True)
    upholstery_condition = Column(String(50), nullable=True)
    underside_condition = Column(String(50), nullable=True)

    # ===== PARTS AVAILABILITY =====
    body_parts_status = Column(String(100), nullable=True)  # Available, Rare, Cannot Find, etc.
    engine_parts_status = Column(String(100), nullable=True)
    accessories_status = Column(String(100), nullable=True)

    # ===== FUEL & PERFORMANCE =====
    fuel_consumption = Column(Numeric(6, 2), nullable=True)
    fuel_consumption_unit = Column(String(20), nullable=True)  # 'km/L' or 'L/100km'

    # ===== BRAKES =====
    foot_brake_condition = Column(String(50), nullable=True)
    disc_brake_available = Column(Boolean, nullable=True)
    parking_brake_condition = Column(String(50), nullable=True)
    abs_available = Column(Boolean, nullable=True)

    # ===== FEATURES (JSONB for flexibility) =====
    features = Column(JSON, nullable=True)
    # Structure: {
    #   air_condition: Boolean,
    #   dual_air_condition: Boolean,
    #   power_mirror: Boolean,
    #   power_window: Boolean,
    #   power_steering: Boolean,
    #   airbag: Boolean,
    #   num_airbags: Integer,
    #   seats: Integer,
    #   doors: Integer
    # }

    # ===== SUSPENSION (JSONB) =====
    suspension = Column(JSON, nullable=True)
    # Structure: { front: String, rear: String }

    # ===== TYRES (JSONB) =====
    tyres = Column(JSON, nullable=True)
    # Structure: {
    #   front: {brand, size, tread_percent, condition},
    #   rear: {brand, size, tread_percent, condition},
    #   spare_available: Boolean,
    #   need_replacement: Boolean,
    #   rear_type: 'single' | 'dual'
    # }

    # ===== ELECTRICAL (JSONB) =====
    electrical = Column(JSON, nullable=True)
    # Structure: { starter: Boolean, horn: Boolean, wiper: Boolean, battery_condition: String }

    # ===== LIGHTS (JSONB) =====
    lights = Column(JSON, nullable=True)
    # Structure: { head: Boolean, dim: Boolean, signal: Boolean, parking: Boolean, reverse: Boolean, meter: Boolean }

    # ===== HISTORY =====
    has_accidents = Column(Boolean, nullable=True)
    has_repairs = Column(Boolean, nullable=True)
    needs_repairs_within_year = Column(Boolean, nullable=True)
    body_parts_replaced = Column(Boolean, nullable=True)

    # ===== VALUATION =====
    purchase_price = Column(Numeric(15, 2), nullable=True)  # LKR
    brand_new_price = Column(Numeric(15, 2), nullable=True)  # LKR
    market_value = Column(Numeric(15, 2), nullable=True)  # LKR
    forced_sale_value = Column(Numeric(15, 2), nullable=True)  # LKR
    valuation_summary = Column(Text, nullable=True)  # AI-generated, editable

    # ===== OFFICE USE (JSONB for conditional fields) =====
    office_data = Column(JSON, nullable=True)
    # Structure: { civil_no: String, military_no: String, approval_position: String }

    # ===== PAST VALUATIONS (JSONB for dynamic rows) =====
    past_valuations = Column(JSON, nullable=True)
    # Structure: [{ serial, civil_no, military_no, year, value, market_value }, ...]

    # ===== PHOTOS (JSONB) =====
    vehicle_photos = Column(JSON, nullable=True)  # [{id, image_data, caption, order}]
    book_images = Column(JSON, nullable=True)  # [{id, image_data, order}] - for OCR

    # ===== TIMESTAMPS =====
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="vehicles")
    report_associations = relationship("ReportVehicle", back_populates="vehicle", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, make='{self.make}', model='{self.model}', reg='{self.registration_number}')>"


class ReportVehicle(Base):
    """
    ReportVehicle junction table - enables many-to-many relationship between Reports and Vehicles.

    Allows:
    - One report to contain multiple vehicles
    - One vehicle to be included in multiple reports (reuse via Vehicle Library)
    - Custom ordering of vehicles within a report (drag-drop support)
    - Per-report-vehicle overrides (e.g., different valuation for different purposes)
    """
    __tablename__ = "report_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_order = Column(Integer, nullable=False, default=1)  # For drag-drop ordering

    # Optional per-report-vehicle data
    report_specific_notes = Column(Text, nullable=True)
    override_market_value = Column(Numeric(15, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    report = relationship("Report", back_populates="vehicle_associations")
    vehicle = relationship("Vehicle", back_populates="report_associations")

    def __repr__(self):
        return f"<ReportVehicle(report_id={self.report_id}, vehicle_id={self.vehicle_id}, order={self.vehicle_order})>"


class TokenBlacklist(Base):
    """
    Token blacklist for logout functionality.

    Stores revoked JWT tokens (by their JTI claim) so that logout
    actually invalidates tokens before their natural expiration.

    Cleanup: Entries can be deleted after expires_at since the token
    would be invalid anyway due to natural expiration.
    """
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)  # JWT ID from token
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Token's original expiry
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TokenBlacklist(jti={self.jti}, user_id={self.user_id}, type={self.token_type})>"


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    ROLE_CHANGE = "role_change"
    EXPORT = "export"


class AuditLog(Base):
    """
    Audit log model for tracking sensitive operations.

    Records:
    - User actions (who did what)
    - Resource modifications (reports, properties, vehicles)
    - Authentication events
    - Role changes
    - Data exports

    Important for:
    - Security compliance
    - Debugging issues
    - Forensic analysis
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Action details
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, login, etc.
    resource_type = Column(String(50), nullable=False, index=True)  # report, property, vehicle, user
    resource_id = Column(Integer, nullable=True, index=True)  # ID of affected resource

    # Additional context
    description = Column(Text, nullable=True)  # Human-readable description
    details = Column(JSON, nullable=True)  # Additional structured data (e.g., changed fields)

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(36), nullable=True)  # Correlation ID

    # Status
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)  # If success=False

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship (nullable because user might be deleted)
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"
