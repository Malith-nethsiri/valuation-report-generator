/**
 * Types specific to PropertyDescriptionStep component.
 * For common types like Building, Floor, Room, BuildingPhoto, see types/index.ts.
 */

/**
 * Tab type for switching between land and building views.
 */
export type TabType = 'land' | 'building';

/**
 * Props for PropertyDescriptionStep component.
 */
export interface PropertyDescriptionStepProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
  isBareLand?: boolean;  // Hide building sections for bare land reports
}

/**
 * Property photo with metadata.
 * Similar to BuildingPhoto but specifically for property-level photos.
 */
export interface PropertyPhoto {
  id: string;
  image_data: string;
  caption: string;
  order: number;
}
