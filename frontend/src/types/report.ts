/**
 * Report, ReportCreate, multi-property, and report pagination types.
 */

import type { DeedInfo, PropertyMetadata } from './property';
import type { RoadCondition } from './maps';
import type { Building, BuildingPhoto } from './building';
import type { NearbyFacility, ComparableProperty, BuildingValuation, ValuationAddon } from './valuation';
import type { InvoiceData } from './invoice';

export interface Report {
  id: number;
  user_id: number;
  report_type: string;
  status: string;
  primary_vehicle_id?: number;

  // Property & Plan Information
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
  inundation_risk?: string;
  earth_slip_risk?: string;
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
  public_transport_frequency?: string;
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
  inundation_risk?: string;
  earth_slip_risk?: string;
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
  public_transport_frequency?: string;
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
  certificate_identity_confirmed?: boolean;
  certification_valuer_name?: string;
  certification_valuer_designation?: string;
  certification_date?: string;
}

// Legacy Types (for backward compatibility)
export interface MultiPropertyFormData {
  // Report metadata
  report_type: 'multi_property';
  is_multi_property: true;
  status?: string;

  // Step 1: Applicant Information
  applicant_title?: string;
  applicant_full_name?: string;
  applicant_id_type?: string;
  applicant_id_number?: string;
  applicant_address_line1?: string;
  applicant_address_line2?: string;
  applicant_district?: string;
  applicant_province?: string;
  applicant_country?: string;
  has_additional_owner?: string;
  additional_owner_names?: string;

  // Step 2: Valuation Purpose
  valuation_type?: string;
  valuation_purpose?: string;
  property_type_valued?: string;
  submission_organization?: string;
  submission_address?: string;
  submission_recipient_position?: string;
  inspection_date?: string;
  report_reference?: string;
  report_date?: string;
  has_special_note?: string;
  special_note_text?: string;

  // Step 3: Property Source Selection
  property_source?: 'library' | 'new' | 'mix';

  // Step 4: Property Count
  property_count: number;

  // Properties (mixed from library and new)
  property_ids?: number[];
  properties?: any[];
  property_metadata?: PropertyMetadata[];

  // Invoice data
  invoice_data?: InvoiceData;

  // Certification
  certification_text?: string;
  certification_valuer_name?: string;
  certification_valuer_designation?: string;
  certification_date?: string;
  certificate_identity_confirmed?: boolean;
}

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
