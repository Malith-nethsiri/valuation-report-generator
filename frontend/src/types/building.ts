/**
 * Building, floor, room, and construction material types.
 */

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
  rooms?: Room[];
  accommodation_summary?: AccommodationSummary;
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
