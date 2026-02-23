/**
 * Valuation component, building valuation, addon, and facility types.
 */

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
