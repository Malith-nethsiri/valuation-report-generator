/**
 * Vehicle types, interfaces, and enumerated constants.
 */

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
