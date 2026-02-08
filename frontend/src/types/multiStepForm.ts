/**
 * Types specific to MultiStepForm component.
 * Extracted from MultiStepForm.tsx to reduce file size and improve reusability.
 */

import { z } from 'zod';
import { completeFormSchema } from '../schemas/multiStepFormSchemas';

/**
 * Form data type inferred from Zod schema with additional runtime fields.
 */
export type FormData = z.infer<typeof completeFormSchema> & {
    // Single deed fields (like plan info)
    deed_type?: string;
    deed_number?: string;
    deed_date?: string;
    notary_name?: string;
    notary_location?: string;
    // Location & Access fields (not validated by Zod)
    use_property_address_as_applicant?: boolean; // Reversed: applicant uses property address
    assessment_number?: string;
    property_village?: string;
    property_divisional_secretariat?: string;
    property_district?: string;
    property_province?: string;
    property_latitude?: number;
    property_longitude?: number;
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
    access_road_conditions?: any[];  // Simple mode: RoadCondition[]
    access_road_segments?: any[];     // Advanced mode: RoadSegment[]
    access_entry_mode?: 'simple' | 'advanced';  // Dual-mode state
    // New administrative fields
    property_number?: string;
    grama_niladari_division?: string;
    korale?: string;
    pradeshiya_sabha?: string;
    ward_number?: string;
    is_municipal_limit?: boolean;
    location_direction?: string;
    // Property Header Fields (Extent, Boundaries, Physical Features)
    land_extent_acres?: number;
    land_extent_roods?: number;
    land_extent_perches?: number;
    land_extent_hectares?: number;
    land_extent_square_meters?: number;
    land_extent_formatted?: string;
    land_traditional_name?: string;
    boundaries?: any; // JSON object for N/S/E/W boundaries
    physical_boundaries_types?: string[];
    physical_boundaries_description?: string;
    survey_plan_scale?: string;
    plan_reference_notes?: string;
    // Property Description fields
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
    land_condition_description?: string;
    land_description_text?: string;
    ongoing_construction_notes?: string;  // Development feasibility/construction status for bare land
    buildings?: any[];
    occupier_name?: string;
    occupier_relationship?: string;
    property_photos?: any[];
    // Locality Information fields
    distance_to_major_town_km?: number;
    major_town_name?: string;
    nearby_facilities?: any[];
    has_electricity?: boolean;
    water_supply_type?: string;
    telecommunication_types?: string[];
    internet_types?: string[];
    has_public_transport?: boolean;
    public_transport_routes?: string;
    public_transport_frequency?: string;
    nearest_bus_stop_distance_km?: number;
    nearest_bus_stop_name?: string;
    nearest_railway_station?: string;
    nearest_railway_distance_km?: number;
    area_type?: string;
    development_level?: string;
    predominant_building_type?: string;
    is_tourist_area?: boolean;
    tourist_attractions_nearby?: string;
    locality_description_text?: string;
};

/**
 * Props passed to step components.
 */
export interface StepComponentProps {
    register: any;
    errors: any;
    watch: any;
    setValue?: any;
}

/**
 * Props for the MultiStepForm component.
 */
export interface MultiStepFormProps {
    onSubmit: (data: FormData, submissionType: 'draft' | 'complete') => Promise<void>;
    isSubmitting?: boolean;
    user?: any;
    isEditMode?: boolean;
    reportId?: number;
    initialData?: Partial<FormData>;
    reportType?: 'residential_property' | 'bare_land' | 'multi_property';  // Report type

    // Multi-property context props
    isEmbeddedInMultiProperty?: boolean;
    commonData?: {
        // Applicant & Purpose (Step 9)
        applicant_title?: string;
        applicant_full_name?: string;
        applicant_id_type?: string;
        applicant_id_number?: string;
        applicant_address_line1?: string;
        applicant_address_line2?: string;
        applicant_district?: string;
        applicant_province?: string;
        applicant_country?: string;
        valuation_type?: string;
        valuation_purpose?: string;
        property_type_valued?: string;
        has_additional_owner?: string;
        additional_owner_names?: string;
        // Additional Details (Step 10)
        submission_recipient_position?: string;
        submission_organization?: string;
        submission_address?: string;
        inspection_date?: string;
        has_special_note?: string;
        special_note_text?: string;
        report_reference?: string;
        report_date?: string;
    };
    onSaveProperty?: (data: FormData) => Promise<void>;
    onFinishProperty?: (data: FormData) => Promise<void>;
    onCancelProperty?: () => void;
    hideCertification?: boolean;
}

/**
 * Data quality warning for form validation feedback.
 */
export interface DataQualityWarning {
    field: string;
    message: string;
    severity: 'warning' | 'info';
}
