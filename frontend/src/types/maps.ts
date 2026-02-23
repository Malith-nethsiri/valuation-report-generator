/**
 * Road type, road condition, and road segment types for map features.
 */

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
