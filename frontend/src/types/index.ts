// Bank Account Types
export interface BankAccount {
  id: string;
  bank_name: string;
  account_number: string;
  branch_name: string;
}

export interface BankAccountCreate {
  bank_name: string;
  account_number: string;
  branch_name: string;
}

export interface BankAccountUpdate {
  bank_name?: string;
  account_number?: string;
  branch_name?: string;
}

// Authentication Types
export interface User {
  id: number;
  email: string;
  honorific?: string;
  full_name: string;
  phone?: string;

  // Professional Credentials
  academic_qualifications?: string;
  membership_level?: string;
  membership_number?: string;
  professional_designation?: string;
  panel_valuer_banks?: string[];

  // Residential Address
  house_number?: string;
  area_development?: string;
  village?: string;
  locality?: string;
  phone_primary?: string;
  phone_secondary?: string;

  // Office Information
  office_department?: string;
  office_region?: string;
  office_street_city?: string;
  office_phone?: string;

  // Letterhead template preference
  preferred_letterhead_template?: string;

  // Bank Account Management
  bank_accounts?: BankAccount[];

  created_at: string;
  updated_at?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegister {
  email: string;
  password: string;
  honorific?: string;
  full_name: string;
  phone?: string;

  // Professional Credentials
  academic_qualifications?: string;
  membership_level?: string;
  membership_number?: string;
  professional_designation?: string;
  panel_valuer_banks?: string[];

  // Residential Address
  house_number?: string;
  area_development?: string;
  village?: string;
  locality?: string;
  phone_primary?: string;
  phone_secondary?: string;

  // Office Information
  office_department?: string;
  office_region?: string;
  office_street_city?: string;
  office_phone?: string;
}

export interface UserUpdate {
  honorific?: string;
  full_name?: string;
  phone?: string;

  // Professional Credentials
  academic_qualifications?: string;
  membership_level?: string;
  membership_number?: string;
  professional_designation?: string;
  panel_valuer_banks?: string[];

  // Residential Address
  house_number?: string;
  area_development?: string;
  village?: string;
  locality?: string;
  phone_primary?: string;
  phone_secondary?: string;

  // Office Information
  office_department?: string;
  office_region?: string;
  office_street_city?: string;
  office_phone?: string;

  // Letterhead template preference
  preferred_letterhead_template?: string;

  // Bank Account Management
  bank_accounts?: BankAccount[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Deed Information
export interface DeedInfo {
  deed_type: string;
  deed_number: string;
  deed_date: string;
  notary_name?: string;
  notary_location?: string;
}

// Building-Related Types
export interface Room {
  room_type: string;
  count: number; // How many rooms of this type
  length?: number;
  width?: number;
  has_attached_bathroom?: boolean;
}

// NEW: Enhanced Construction Material Interfaces
export interface RoofDetails {
  structure_type?: string;
  covering_material?: string[];
  additional_details?: string;
}

export interface WallDetails {
  material?: string;
  finish?: string[];
  // REMOVED: thickness field (not needed)
}

export interface FloorDetails {
  material?: string[];
  finish_quality?: string;
}

export interface DoorsWindowsDetails {
  window_frame_material?: string[];
  window_glass_type?: string[];
  window_security?: string[];
  main_door_material?: string;
  internal_door_material?: string;
  door_security?: string[];
}

export interface AccommodationSummary {
  bedrooms: number;
  bathrooms: number;
  living_rooms: number;
  dining_rooms: number;
  kitchens: number;
  pantries: number;
  verandahs: number;
  balconies: number;
  garages: number;
  store_rooms: number;
  other_rooms: number;
}

export interface Floor {
  floor_name: string;
  floor_area?: number;
}

export interface BuildingPhoto {
  id: string;
  image_data: string;
  caption?: string;
  order: number;
}

// Legacy interface (kept for backward compatibility)
/** @deprecated Use WallDetails instead */
export interface WallConstruction {
  material?: string;
  thickness?: string;
  finish?: string;
}

export interface ConstructionMaterials {
  // NEW: Enhanced construction details
  roof_details?: RoofDetails;
  wall_details?: WallDetails;
  floor_details?: FloorDetails;
  ceiling_type?: string;
  doors_windows_details?: DoorsWindowsDetails;

  // DEPRECATED: Legacy fields kept for backward compatibility
  /** @deprecated No longer collected - use roof_details instead */
  foundation_type?: string;
  /** @deprecated Use wall_details instead */
  wall_construction?: WallConstruction;
  /** @deprecated Use roof_details.structure_type instead */
  roof_structure?: string;
}

export interface Electricity {
  source?: string;
  three_phase?: boolean;
  solar_panels?: boolean;
}

export interface Parking {
  covered_spaces?: number;
  uncovered_spaces?: number;
}

export interface UtilitiesServices {
  // Water and sewage
  water_supply?: string[];  // Array of water supply types
  sewage?: string;

  // Electricity and parking (detailed objects)
  electricity?: Electricity;
  parking?: Parking;

  // Communication services
  telephone?: boolean;
  internet?: boolean;

  // Gas connection
  gas_connection?: boolean;

  // Security features
  security_features?: string[];

  // Modern amenities
  amenities?: {
    air_conditioning?: boolean;
    built_in_wardrobes?: boolean;
    modern_kitchen?: boolean;
    pantry_cupboards?: boolean;
  };

  // Hot water system
  hot_water_system?: string;
}

export interface Building {
  id: string;
  building_name?: string;
  building_type: string;
  stories?: number;
  building_age?: number;  // Age of building in years
  condition?: string;
  occupier_name?: string;
  occupier_relationship?: string;
  is_rented?: boolean;
  rent_details?: string;
  roof_types: string[];
  /** @deprecated Use roof_types array instead. This field is not displayed in UI and will be auto-generated from roof_types selections. */
  roof_description?: string;
  wall_types: string[];
  /** @deprecated Use wall_types array instead. This field is not displayed in UI and will be auto-generated from wall_types selections. */
  wall_description?: string;
  floor_types: string[];
  /** @deprecated Use floor_types array instead. This field is not displayed in UI and will be auto-generated from floor_types selections. */
  floor_description?: string;
  total_floor_area?: number;
  floors: Floor[];
  rooms: Room[];
  accommodation_summary?: AccommodationSummary;
  construction_materials?: ConstructionMaterials;
  utilities_services?: UtilitiesServices;
  conveniences: string[];
  /** @deprecated Not displayed in UI. Building descriptions will be auto-generated from building properties. */
  building_description_text?: string;
  building_photos: BuildingPhoto[];
  additional_structures_description?: string;
}

// Locality Facility Type
export interface NearbyFacility {
  type: string;
  name: string;
  distance: number;
  coordinates?: {
    lat: number;
    lng: number;
  };
  selected?: boolean;
}

// Legal Aspects, Land Values, Valuation Types
export interface ComparableProperty {
  id: string;
  property_type: 'Commercial' | 'Residential' | 'Agricultural';
  location_description: string;
  extent: number;  // perches
  rate_per_perch: number;  // LKR
  total_value: number;  // auto-calculated
}

export interface ValuationComponent {
  id: string;
  description: string;  // e.g., "Restaurant", "Pool"
  units: number;
  floor_area: number;  // sq.ft
  rate: number;  // LKR per sq.ft
  value: number;  // auto-calculated
}

export interface BuildingValuation {
  building_id: string;
  building_name?: string;
  components: ValuationComponent[];
  subtotal: number;
  // Depreciation fields
  depreciation_rate_percent?: number;  // User enters manually
  depreciation_amount?: number;
  depreciated_value?: number;
}

export interface ValuationAddon {
  id: string;
  description: string;
  value: number;
}

// NEW: Simplified Road Condition Type
export type RoadType = 'paved_road' | 'concrete_road' | 'carpet_road' | 'gravel_road' | 'sand_road' | 'earth_road';

export interface RoadCondition {
  road_type: RoadType;
  condition: 'excellent' | 'good' | 'fair' | 'poor';
  distance_km?: number;  // Optional distance in kilometers
  notes?: string;
}

// DEPRECATED: Road Segment Types (kept for backward compatibility)
export interface RoadSegment {
  id: string;
  order: number;

  // Google Maps data
  instruction?: string; // Full turn-by-turn instruction from Google Maps
  road_name?: string;
  distance_km?: number;
  distance_text?: string;

  // User-entered details
  road_type?: RoadType;
  surface_condition?: 'excellent' | 'good' | 'fair' | 'poor';
  road_width_meters?: number;
  additional_notes?: string;
  has_details: boolean;
}

export interface AccessRoadSegments {
  segments: RoadSegment[];
}

// Report Types
export interface Report {
  id: number;
  user_id: number;
  report_type: string;
  status: string;

  // Property & Plan Information
  /** @deprecated Use lot_number instead */
  property_lot_description?: string;
  lot_number?: string;  // e.g., "Lot 15", "Lots 1 & 2"
  plan_number?: string;
  plan_date?: string;
  licensed_surveyor_name?: string;

  // Property Identification Type
  property_identification_type?: 'plan' | 'deed' | 'plan_and_deed' | 'certificate_of_sale';

  // Certificate fields (form-only, not in backend)
  certificate_number?: string;
  certificate_date?: string;
  certificate_notary_name?: string;
  certificate_notary_district?: string;

  // Applicant Information
  applicant_title?: string;
  applicant_full_name?: string;
  applicant_id_type?: string;
  applicant_id_number?: string;
  applicant_address_line1?: string;
  applicant_address_line2?: string;
  applicant_district?: string;
  applicant_province?: string;
  applicant_country?: string;

  // Request Type (client vs organization)
  request_type?: 'client_request' | 'organization_request';

  // Applicant Contact Number
  applicant_contact_number?: string;

  // Valuation Purpose
  valuation_type?: string;
  property_type_valued?: string;

  // Valuation Purpose (new)
  valuation_purpose?: string;

  // Additional Property Owner
  has_additional_owner?: string;
  additional_owner_names?: string;

  // Deed Information
  has_deed_info?: string;
  deeds?: DeedInfo[];

  // Submission Destination
  submission_organization?: string;
  submission_address?: string;
  submission_recipient_position?: string;

  // Date of Inspection
  inspection_date?: string;

  // Special Notes
  has_special_note?: string;
  special_note_text?: string;

  // Report metadata
  report_reference?: string;
  report_date?: string;

  // ===== PROPERTY LOCATION & ACCESS (Phase 2) =====

  // Property Location Information
  use_applicant_address_as_property?: boolean;
  assessment_number?: string;
  property_village?: string;
  property_divisional_secretariat?: string;
  property_district?: string;
  property_province?: string;
  property_latitude?: number;
  property_longitude?: number;

  // Sri Lankan Administrative Subdivisions (Phase 2 Enhancement)
  property_number?: string;
  grama_niladari_division?: string;
  hathpaththuwa?: string;
  korale?: string;
  pradeshiya_sabha?: string;
  ward_number?: string;
  is_municipal_limit?: boolean;
  location_direction?: string;

  // Access Directions Information
  access_starting_point_name?: string;
  access_starting_point_latitude?: number;
  access_starting_point_longitude?: number;
  access_route_data?: any;
  access_directions_text?: string;
  access_distance_km?: number;
  access_duration_minutes?: number;
  access_road_type?: string;
  property_road_position?: string;
  location_map_image_data?: string;
  access_road_conditions?: RoadCondition[];  // NEW: Simplified road conditions array

  // ===== PROPERTY HEADER FIELDS (Land Extent, Boundaries) =====

  // Land Extent
  land_extent_acres?: number;
  land_extent_roods?: number;
  land_extent_perches?: number;
  land_extent_hectares?: number;
  land_extent_square_meters?: number;
  land_extent_formatted?: string;

  // Traditional Land Name
  land_traditional_name?: string;

  // Boundaries (4 main directions + 4 optional diagonal directions)
  boundaries?: {
    north?: { description?: string; length?: string; adjoins?: string; notes?: string };
    northeast?: { description?: string; length?: string; adjoins?: string; notes?: string };
    east?: { description?: string; length?: string; adjoins?: string; notes?: string };
    southeast?: { description?: string; length?: string; adjoins?: string; notes?: string };
    south?: { description?: string; length?: string; adjoins?: string; notes?: string };
    southwest?: { description?: string; length?: string; adjoins?: string; notes?: string };
    west?: { description?: string; length?: string; adjoins?: string; notes?: string };
    northwest?: { description?: string; length?: string; adjoins?: string; notes?: string };
  };

  // Physical Boundaries
  physical_boundaries_types?: string[];
  physical_boundaries_description?: string;

  // Boundary Types Per Direction (for professional summary) - supports all 8 directions
  boundary_types_per_direction?: {
    north?: string;
    northeast?: string;
    east?: string;
    southeast?: string;
    south?: string;
    southwest?: string;
    west?: string;
    northwest?: string;
  };

  // Entrance/Gate Type
  entrance_type?: string;

  // Auto-generated (editable) boundary summary
  boundaries_summary_text?: string;

  // ===== PROPERTY DESCRIPTION =====

  // Land Description
  land_shape?: string;
  land_type?: string;
  land_frontage_type?: string;
  land_frontage_width?: number;
  land_frontage_description?: string;
  land_level?: string;
  land_level_difference?: number;
  soil_type?: string;
  water_table_depth?: number;
  flood_risk?: string;
  land_condition?: string;
  land_description_text?: string;

  // Topographical Features
  elevation_changes?: string;
  drainage_pattern?: string;
  vegetation_type?: string;
  natural_features?: string;

  // Building Details
  buildings?: Building[];
  occupier_name?: string;
  occupier_relationship?: string;

  // Property Photos
  property_photos?: BuildingPhoto[];

  // ===== LOCALITY INFORMATION =====

  // Distance to major town/city
  distance_to_major_town_km?: number;
  major_town_name?: string;

  // Nearby facilities
  nearby_facilities?: NearbyFacility[];

  // Infrastructure & Utilities
  has_electricity?: boolean;
  water_supply_type?: string[];  // Array of water supply types
  telecommunication_types?: string[];
  internet_types?: string[];

  // Public Transport
  has_public_transport?: boolean;
  public_transport_routes?: string;
  nearest_bus_stop_distance_km?: number;
  nearest_bus_stop_name?: string;
  nearest_railway_station?: string;
  nearest_railway_distance_km?: number;

  // Area Characteristics
  area_type?: string;
  development_level?: string;
  predominant_building_type?: string[];  // Array of predominant building types

  // Tourism/Special characteristics
  is_tourist_area?: boolean;
  tourist_attractions_nearby?: string;

  // Auto-generated locality narrative
  locality_description_text?: string;

  // ===== LEGAL ASPECTS =====
  ownership_type?: string;
  street_lines_status?: string;
  building_limits_status?: string;
  local_authority_data?: string;
  rent_act_effectiveness?: string;

  // Ownership & Title - Extended fields
  title_search_conducted?: string; // "Yes"/"No"
  pedigree_search_conducted?: string; // "Yes"/"No"
  valuation_basis_note?: string; // Custom basis statement
  property_encumbered?: string; // "Yes"/"No"
  encumbrance_type?: string; // "Mortgage"/"Life Interest"/etc.
  encumbrance_details?: string; // Bank name, mortgagee details

  // Street Lines - Extended fields
  street_lines_gazette_ref?: string; // Gazette reference
  street_lines_gazette_date?: string; // Gazette date
  street_lines_impact_description?: string; // Impact description

  // Building Limits - Extended fields
  building_distance_from_road?: string; // Distance from road
  building_plan_approved?: string; // "Yes"/"No"/"Not Applicable"
  building_plan_reference?: string; // Plan reference number
  building_approval_authority?: string; // Approval authority
  building_within_limits?: string; // "Yes"/"No"

  // Local Authority - Extended fields
  local_authority_rated?: string; // "Yes"/"No"
  local_authority_tax_levy?: string; // Tax information

  // ===== LAND VALUES =====
  comparable_properties?: ComparableProperty[];
  land_market_analysis?: string;

  // ===== VALUATION =====
  valuation_land_extent?: number;
  valuation_rate_per_perch?: number;
  valuation_total_land_value?: number;
  valuation_buildings_data?: BuildingValuation[];
  valuation_total_buildings_value?: number;
  valuation_addons?: ValuationAddon[];
  valuation_total_addons_value?: number;
  valuation_market_value?: number;
  valuation_forced_sale_percentage?: number;
  valuation_forced_sale_value?: number;
  valuation_insurance_value?: number;
  valuation_manual_overrides?: Record<string, boolean>;

  // ===== CERTIFICATION =====
  certification_text?: string;
  certificate_survey_plan_ref?: string;
  certificate_survey_plan_date?: string;
  certificate_identity_confirmed?: boolean;
  certification_valuer_name?: string;
  certification_valuer_designation?: string;
  certification_date?: string;

  created_at: string;
  updated_at?: string;
}

export interface ReportCreate {
  report_type?: string;
  status?: string;

  // Property & Plan Information
  /** @deprecated Use lot_number instead */
  property_lot_description?: string;
  lot_number?: string;  // e.g., "Lot 15", "Lots 1 & 2"
  plan_number?: string;
  plan_date?: string;
  licensed_surveyor_name?: string;

  // Property Identification Type
  property_identification_type?: 'plan' | 'deed' | 'plan_and_deed' | 'certificate_of_sale';

  // Certificate fields (form-only, not in backend)
  certificate_number?: string;
  certificate_date?: string;
  certificate_notary_name?: string;
  certificate_notary_district?: string;

  // Applicant Information
  applicant_title?: string;
  applicant_full_name?: string;
  applicant_id_type?: string;
  applicant_id_number?: string;
  applicant_address_line1?: string;
  applicant_address_line2?: string;
  applicant_district?: string;
  applicant_province?: string;
  applicant_country?: string;

  // Request Type (client vs organization)
  request_type?: 'client_request' | 'organization_request';

  // Applicant Contact Number
  applicant_contact_number?: string;

  // Valuation Purpose
  valuation_type?: string;
  property_type_valued?: string;

  // Valuation Purpose (new)
  valuation_purpose?: string;

  // Additional Property Owner
  has_additional_owner?: string;
  additional_owner_names?: string;

  // Deed Information
  has_deed_info?: string;
  deeds?: DeedInfo[];

  // Submission Destination
  submission_organization?: string;
  submission_address?: string;
  submission_recipient_position?: string;

  // Date of Inspection
  inspection_date?: string;

  // Special Notes
  has_special_note?: string;
  special_note_text?: string;

  // Report metadata
  report_reference?: string;
  report_date?: string;

  // ===== PROPERTY LOCATION & ACCESS (Phase 2) =====

  // Property Location Information
  use_applicant_address_as_property?: boolean;
  assessment_number?: string;
  property_village?: string;
  property_divisional_secretariat?: string;
  property_district?: string;
  property_province?: string;
  property_latitude?: number;
  property_longitude?: number;

  // Sri Lankan Administrative Subdivisions (Phase 2 Enhancement)
  property_number?: string;
  grama_niladari_division?: string;
  hathpaththuwa?: string;
  korale?: string;
  pradeshiya_sabha?: string;
  ward_number?: string;
  is_municipal_limit?: boolean;
  location_direction?: string;

  // Access Directions Information
  access_starting_point_name?: string;
  access_starting_point_latitude?: number;
  access_starting_point_longitude?: number;
  access_route_data?: any;
  access_directions_text?: string;
  access_distance_km?: number;
  access_duration_minutes?: number;
  access_road_type?: string;
  property_road_position?: string;
  location_map_image_data?: string;
  access_road_conditions?: RoadCondition[];  // NEW: Simplified road conditions array

  // ===== PROPERTY HEADER FIELDS (Land Extent, Boundaries) =====

  // Land Extent
  land_extent_acres?: number;
  land_extent_roods?: number;
  land_extent_perches?: number;
  land_extent_hectares?: number;
  land_extent_square_meters?: number;
  land_extent_formatted?: string;

  // Traditional Land Name
  land_traditional_name?: string;

  // Boundaries (4 main directions + 4 optional diagonal directions)
  boundaries?: {
    north?: { description?: string; length?: string; adjoins?: string; notes?: string };
    northeast?: { description?: string; length?: string; adjoins?: string; notes?: string };
    east?: { description?: string; length?: string; adjoins?: string; notes?: string };
    southeast?: { description?: string; length?: string; adjoins?: string; notes?: string };
    south?: { description?: string; length?: string; adjoins?: string; notes?: string };
    southwest?: { description?: string; length?: string; adjoins?: string; notes?: string };
    west?: { description?: string; length?: string; adjoins?: string; notes?: string };
    northwest?: { description?: string; length?: string; adjoins?: string; notes?: string };
  };

  // Physical Boundaries
  physical_boundaries_types?: string[];
  physical_boundaries_description?: string;

  // Boundary Types Per Direction (for professional summary) - supports all 8 directions
  boundary_types_per_direction?: {
    north?: string;
    northeast?: string;
    east?: string;
    southeast?: string;
    south?: string;
    southwest?: string;
    west?: string;
    northwest?: string;
  };

  // Entrance/Gate Type
  entrance_type?: string;

  // Auto-generated (editable) boundary summary
  boundaries_summary_text?: string;

  // ===== PROPERTY DESCRIPTION =====

  // Land Description
  land_shape?: string;
  land_type?: string;
  land_frontage_type?: string;
  land_frontage_width?: number;
  land_frontage_description?: string;
  land_level?: string;
  land_level_difference?: number;
  soil_type?: string;
  water_table_depth?: number;
  flood_risk?: string;
  land_condition?: string;
  land_description_text?: string;

  // Topographical Features
  elevation_changes?: string;
  drainage_pattern?: string;
  vegetation_type?: string;
  natural_features?: string;

  // Building Details
  buildings?: Building[];
  occupier_name?: string;
  occupier_relationship?: string;

  // Property Photos
  property_photos?: BuildingPhoto[];

  // ===== LOCALITY INFORMATION =====

  // Distance to major town/city
  distance_to_major_town_km?: number;
  major_town_name?: string;

  // Nearby facilities
  nearby_facilities?: NearbyFacility[];

  // Infrastructure & Utilities
  has_electricity?: boolean;
  water_supply_type?: string[];  // Array of water supply types
  telecommunication_types?: string[];
  internet_types?: string[];

  // Public Transport
  has_public_transport?: boolean;
  public_transport_routes?: string;
  nearest_bus_stop_distance_km?: number;
  nearest_bus_stop_name?: string;
  nearest_railway_station?: string;
  nearest_railway_distance_km?: number;

  // Area Characteristics
  area_type?: string;
  development_level?: string;
  predominant_building_type?: string[];  // Array of predominant building types

  // Tourism/Special characteristics
  is_tourist_area?: boolean;
  tourist_attractions_nearby?: string;

  // Auto-generated locality narrative
  locality_description_text?: string;

  // ===== LEGAL ASPECTS =====
  ownership_type?: string;
  street_lines_status?: string;
  building_limits_status?: string;
  local_authority_data?: string;
  rent_act_effectiveness?: string;

  // Ownership & Title - Extended fields
  title_search_conducted?: string; // "Yes"/"No"
  pedigree_search_conducted?: string; // "Yes"/"No"
  valuation_basis_note?: string; // Custom basis statement
  property_encumbered?: string; // "Yes"/"No"
  encumbrance_type?: string; // "Mortgage"/"Life Interest"/etc.
  encumbrance_details?: string; // Bank name, mortgagee details

  // Street Lines - Extended fields
  street_lines_gazette_ref?: string; // Gazette reference
  street_lines_gazette_date?: string; // Gazette date
  street_lines_impact_description?: string; // Impact description

  // Building Limits - Extended fields
  building_distance_from_road?: string; // Distance from road
  building_plan_approved?: string; // "Yes"/"No"/"Not Applicable"
  building_plan_reference?: string; // Plan reference number
  building_approval_authority?: string; // Approval authority
  building_within_limits?: string; // "Yes"/"No"

  // Local Authority - Extended fields
  local_authority_rated?: string; // "Yes"/"No"
  local_authority_tax_levy?: string; // Tax information

  // ===== LAND VALUES =====
  comparable_properties?: ComparableProperty[];
  land_market_analysis?: string;

  // ===== VALUATION =====
  valuation_land_extent?: number;
  valuation_rate_per_perch?: number;
  valuation_total_land_value?: number;
  valuation_buildings_data?: BuildingValuation[];
  valuation_total_buildings_value?: number;
  valuation_addons?: ValuationAddon[];
  valuation_total_addons_value?: number;
  valuation_market_value?: number;
  valuation_forced_sale_percentage?: number;
  valuation_forced_sale_value?: number;
  valuation_insurance_value?: number;
  valuation_manual_overrides?: Record<string, boolean>;

  // ===== CERTIFICATION =====
  certification_text?: string;
  certificate_survey_plan_ref?: string;
  certificate_survey_plan_date?: string;
  certificate_identity_confirmed?: boolean;
  certification_valuer_name?: string;
  certification_valuer_designation?: string;
  certification_date?: string;
}

// Legacy Types (for backward compatibility)
export interface UserData {
  full_name: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  additional_info?: string;
}

export interface UserDataResponse extends UserData {
  id: number;
  created_at: string;
  updated_at?: string;
}

// Administrative Divisions Types (Sri Lankan specific)
export interface AdministrativeDivision {
  name: string;
  gn_count: number;
}

export interface AdministrativeDivisionsData {
  [district: string]: AdministrativeDivision[];
}

export interface AdministrativeDivisionsResponse {
  status: string;
  data: AdministrativeDivisionsData;
  total_districts: number;
  total_ds_divisions: number;
}

export interface DSDivisionsResponse {
  status: string;
  district: string;
  ds_divisions: AdministrativeDivision[];
}

// Common Types
export interface ApiError {
  detail: string;
}

export interface HealthResponse {
  status: string;
  message: string;
}

// Letterhead Template Types
export interface TemplateMetadata {
  template_id: string;
  name: string;
  description: string;
  category: string;
}

export interface TemplateListResponse {
  templates: TemplateMetadata[];
}

// ===== MULTI-PROPERTY FORM TYPES =====

/**
 * Represents a property within a multi-property report.
 * Used in PropertyMiniDashboard and multi-property form components.
 */
export interface PropertyInReport {
  id: string | number; // temp ID or DB ID
  type: 'residential' | 'bare_land' | 'vehicle';
  order: number;
  status: 'draft' | 'completed';
  data: {
    property_village?: string;
    property_district?: string;
    lot_number?: string;
    plan_number?: string;
    // Vehicle-specific fields
    registration_number?: string;
    make?: string;
    model?: string;
    market_value?: number;
    [key: string]: any;
  };
}

// Pagination & Filter Types
export interface ReportStats {
  total_count: number;
  this_month_count: number;
  completed_count: number;
  draft_count: number;
}

export interface PaginatedReportResponse {
  items: Report[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  stats: ReportStats;
}

export interface ReportFilters {
  reference?: string;
  applicant_name?: string;
  village?: string;
  report_date?: string;  // YYYY-MM-DD format
}

export interface AdjacentDateResponse {
  adjacent_date: string | null;
}

// ===== VEHICLE TYPES =====

export interface VehiclePhoto {
  id: string;
  image_data: string;
  caption?: string;
  order: number;
}

export interface VehicleTyreSet {
  brand?: string;
  size?: string;
  tread_percent?: number;
  condition?: string;
}

export interface VehicleTyres {
  front?: VehicleTyreSet;
  rear?: VehicleTyreSet;
  spare_available?: boolean;
  need_replacement?: boolean;
  rear_type?: 'single' | 'dual';
}

export interface VehicleSuspension {
  front?: string;
  rear?: string;
}

export interface VehicleElectrical {
  starter?: boolean;
  horn?: boolean;
  wiper?: boolean;
  battery_condition?: string;
}

export interface VehicleLights {
  head?: boolean;
  dim?: boolean;
  signal?: boolean;
  parking?: boolean;
  reverse?: boolean;
  meter?: boolean;
}

export interface VehicleFeatures {
  air_condition?: boolean;
  dual_air_condition?: boolean;
  power_mirror?: boolean;
  power_window?: boolean;
  power_steering?: boolean;
  airbag?: boolean;
  num_airbags?: number;
  seats?: number;
  doors?: number;
}

export interface VehicleOfficeData {
  civil_no?: string;
  military_no?: string;
  approval_position?: string;
}

export interface VehiclePastValuation {
  serial?: number;
  civil_no?: string;
  military_no?: string;
  year?: number;
  value?: number;
  market_value?: number;
}

export interface Vehicle {
  id: number;
  user_id: number;
  status: string;
  vehicle_type?: string;
  is_template?: boolean;
  is_deleted?: boolean;
  original_vehicle_id?: number;

  // Vehicle Identification
  registration_number?: string;
  provincial_council?: string;
  class_of_vehicle?: string;
  body_colour?: string;
  chassis_number?: string;
  engine_number?: string;
  vehicle_status?: string;
  country_of_origin?: string;
  make?: string;
  model?: string;
  date_of_first_registration?: string;
  year_of_manufacture?: number;
  cylinder_capacity?: number;
  fuel_type?: string;
  mileage?: number;
  mileage_unit?: string;

  // Engine & Transmission
  engine_type?: string;
  transmission?: string;
  wheel_drive?: string;

  // Condition Fields
  running_condition?: string;
  clutch_status?: string;
  engine_condition?: string;
  gear_box_condition?: string;
  differential_status?: string;
  gear_selection?: string;
  body_condition?: string;
  chassis_condition?: string;
  upholstery_condition?: string;
  underside_condition?: string;

  // Parts Availability
  body_parts_status?: string;
  engine_parts_status?: string;
  accessories_status?: string;

  // Fuel & Performance
  fuel_consumption?: number;
  fuel_consumption_unit?: string;

  // Brakes
  foot_brake_condition?: string;
  disc_brake_available?: boolean;
  parking_brake_condition?: string;
  abs_available?: boolean;

  // Structured Data
  features?: VehicleFeatures;
  suspension?: VehicleSuspension;
  tyres?: VehicleTyres;
  electrical?: VehicleElectrical;
  lights?: VehicleLights;

  // History
  has_accidents?: boolean;
  has_repairs?: boolean;
  needs_repairs_within_year?: boolean;
  body_parts_replaced?: boolean;

  // Valuation
  purchase_price?: number;
  brand_new_price?: number;
  market_value?: number;
  forced_sale_value?: number;
  valuation_summary?: string;

  // Office Use
  office_data?: VehicleOfficeData;
  past_valuations?: VehiclePastValuation[];

  // Photos
  vehicle_photos?: VehiclePhoto[];
  book_images?: VehiclePhoto[];

  // Timestamps
  created_at: string;
  updated_at?: string;
}

export interface VehicleCreate {
  status?: string;
  vehicle_type?: string;
  is_template?: boolean;

  // Vehicle Identification
  registration_number?: string;
  provincial_council?: string;
  class_of_vehicle?: string;
  body_colour?: string;
  chassis_number?: string;
  engine_number?: string;
  vehicle_status?: string;
  country_of_origin?: string;
  make?: string;
  model?: string;
  date_of_first_registration?: string;
  year_of_manufacture?: number;
  cylinder_capacity?: number;
  fuel_type?: string;
  mileage?: number;
  mileage_unit?: string;

  // Engine & Transmission
  engine_type?: string;
  transmission?: string;
  wheel_drive?: string;

  // Condition Fields
  running_condition?: string;
  clutch_status?: string;
  engine_condition?: string;
  gear_box_condition?: string;
  differential_status?: string;
  gear_selection?: string;
  body_condition?: string;
  chassis_condition?: string;
  upholstery_condition?: string;
  underside_condition?: string;

  // Parts Availability
  body_parts_status?: string;
  engine_parts_status?: string;
  accessories_status?: string;

  // Fuel & Performance
  fuel_consumption?: number;
  fuel_consumption_unit?: string;

  // Brakes
  foot_brake_condition?: string;
  disc_brake_available?: boolean;
  parking_brake_condition?: string;
  abs_available?: boolean;

  // Structured Data
  features?: VehicleFeatures;
  suspension?: VehicleSuspension;
  tyres?: VehicleTyres;
  electrical?: VehicleElectrical;
  lights?: VehicleLights;

  // History
  has_accidents?: boolean;
  has_repairs?: boolean;
  needs_repairs_within_year?: boolean;
  body_parts_replaced?: boolean;

  // Valuation
  purchase_price?: number;
  brand_new_price?: number;
  market_value?: number;
  forced_sale_value?: number;
  valuation_summary?: string;

  // Office Use
  office_data?: VehicleOfficeData;
  past_valuations?: VehiclePastValuation[];

  // Photos
  vehicle_photos?: VehiclePhoto[];
  book_images?: VehiclePhoto[];
}

export type VehicleUpdate = Partial<VehicleCreate>;

export interface VehicleTemplate {
  id: number;
  make?: string;
  model?: string;
  registration_number?: string;
  year_of_manufacture?: number;
  market_value?: number;
  created_at: string;
}

export interface ReportVehicle {
  id: number;
  report_id: number;
  vehicle_id: number;
  vehicle_order: number;
  report_specific_notes?: string;
  override_market_value?: number;
  vehicle: Vehicle;
  created_at: string;
}

export interface VehicleValuationSuggestion {
  suggested_market_value?: number;
  suggested_forced_sale_value?: number;
  suggested_brand_new_price?: number;
  valuation_summary?: string;
  confidence?: number;
  reasoning?: string;
}

// Vehicle Report Constants
export const VEHICLE_TYPES = ['car', 'motorcycle', 'truck', 'special'] as const;
export type VehicleType = typeof VEHICLE_TYPES[number];

export const PROVINCIAL_COUNCILS = [
  'Western',
  'Central',
  'Southern',
  'Northern',
  'Eastern',
  'North Western',
  'North Central',
  'Uva',
  'Sabaragamuwa'
] as const;

export const VEHICLE_CLASSES = [
  'Car',
  'Van',
  'SUV',
  'Motorcycle',
  'Three-wheeler',
  'Truck',
  'Bus',
  'Tractor'
] as const;

export const FUEL_TYPES = [
  'Petrol',
  'Diesel',
  'Hybrid (Petrol)',
  'Hybrid (Diesel)',
  'Electric',
  'CNG',
  'LPG'
] as const;

export const TRANSMISSION_TYPES = [
  'Manual',
  'Automatic',
  'CVT',
  'Semi-Automatic',
  'AMT'
] as const;

export const CONDITION_RATINGS = [
  'Excellent',
  'Good',
  'Fair',
  'Poor',
  'Very Poor'
] as const;

export const PARTS_STATUS_OPTIONS = [
  'Available',
  'Rare',
  'Cannot Find',
  'Aftermarket Available',
  'Discontinued'
] as const;

export const CLUTCH_STATUS_OPTIONS = [
  'Working Properly',
  'Needs Adjustment',
  'Needs Replacement'
] as const;

export const DIFFERENTIAL_STATUS_OPTIONS = [
  'Working Properly',
  'Has Issues',
  'Not Working'
] as const;

export const GEAR_SELECTION_OPTIONS = [
  'Smooth',
  'Stiff',
  'Difficult',
  'Not Working'
] as const;

export const BATTERY_CONDITION_OPTIONS = [
  'Good',
  'Fair',
  'Poor',
  'Needs Replacement'
] as const;

export const VEHICLE_STATUS_OPTIONS = [
  'Registered',
  'De-registered',
  'Pending',
  'Imported'
] as const;

export const VALUATION_PURPOSE_OPTIONS = [
  'Bank Loan',
  'Insurance',
  'Sale',
  'Legal',
  'Government Assessment'
] as const;
