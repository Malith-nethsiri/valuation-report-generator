/**
 * Constants for PropertyDescriptionStep component.
 * Extracted from PropertyDescriptionStep.tsx to reduce file size and improve reusability.
 */

// ===== Configuration Constants =====

/**
 * Maximum number of photos allowed per building.
 */
export const MAX_BUILDING_PHOTOS = 5;

/**
 * Maximum number of property photos allowed.
 */
export const MAX_PROPERTY_PHOTOS = 20;

/**
 * Maximum number of floors per building.
 */
export const MAX_FLOORS_PER_BUILDING = 10;

/**
 * Default floor names for building floors.
 */
export const FLOOR_NAMES = [
  'Ground Floor',
  'First Floor',
  'Second Floor',
  'Third Floor',
  'Fourth Floor',
  'Fifth Floor',
  'Sixth Floor',
  'Seventh Floor',
  'Eighth Floor',
  'Ninth Floor',
] as const;

// ===== Dropdown Option Types =====

export interface DropdownOption {
  value: string;
  label: string;
}

export interface DevelopmentFeasibilityTemplate {
  value: string;
  label: string;
  text?: string;
}

// ===== Land Description Options =====

/**
 * Land shape options for property description.
 */
export const LAND_SHAPES: DropdownOption[] = [
  { value: 'rectangular', label: 'Rectangular' },
  { value: 'square', label: 'Square' },
  { value: 'triangular', label: 'Triangular' },
  { value: 'trapezoidal', label: 'Trapezoidal' },
  { value: 'quadrilateral', label: 'Quadrilateral' },
  { value: 'irregular', label: 'Irregular' },
  { value: 'l_shaped', label: 'L-Shaped' },
  { value: 'pentagon', label: 'Pentagon' },
];

/**
 * Land type options for property description.
 */
export const LAND_TYPES: DropdownOption[] = [
  { value: 'high_land', label: 'High Land' },
  { value: 'low_land', label: 'Low Land' },
  { value: 'flat_land', label: 'Flat Land' },
  { value: 'sloping_land', label: 'Sloping Land' },
  { value: 'paddy_land', label: 'Paddy Land' },
  { value: 'garden_land', label: 'Garden Land' },
];

/**
 * Road frontage type options.
 */
export const FRONTAGE_TYPES: DropdownOption[] = [
  { value: 'tarred', label: 'Tarred Road' },
  { value: 'gravel', label: 'Gravel Road' },
  { value: 'concrete_brick_paved', label: 'Concrete Brick Paved' },
  { value: 'earth', label: 'Earth Road' },
  { value: 'no_frontage', label: 'No Road Frontage' },
];

/**
 * Land level relative to road options.
 */
export const LAND_LEVELS: DropdownOption[] = [
  { value: 'at_road_level', label: 'At Road Level' },
  { value: 'above_road_level', label: 'Above Road Level' },
  { value: 'below_road_level', label: 'Below Road Level' },
];

/**
 * Soil type options for property description.
 */
export const SOIL_TYPES: DropdownOption[] = [
  { value: 'sand_clay', label: 'Sand Clay' },
  { value: 'gravel_clay', label: 'Gravel Clay' },
  { value: 'red_earth', label: 'Red Earth' },
  { value: 'loamy', label: 'Loamy' },
  { value: 'rocky', label: 'Rocky' },
  { value: 'marshy', label: 'Marshy' },
];

/**
 * Flood risk options for property description.
 */
export const FLOOD_RISK_OPTIONS: DropdownOption[] = [
  { value: 'not_subject', label: 'Not Subject to Flooding' },
  { value: 'occasionally_floods', label: 'Occasionally Floods' },
  { value: 'flood_prone', label: 'Flood Prone Area' },
];

/**
 * Land condition options for property description.
 */
export const LAND_CONDITIONS: DropdownOption[] = [
  { value: 'developed', label: 'Developed' },
  { value: 'bare_land', label: 'Bare Land' },
  { value: 'scrub_jungle', label: 'Scrub Jungle' },
  { value: 'cultivated', label: 'Cultivated' },
  { value: 'marshy', label: 'Marshy' },
];

/**
 * Elevation change options for topographical features.
 */
export const ELEVATION_CHANGES: DropdownOption[] = [
  { value: 'relatively_flat', label: 'Relatively Flat' },
  { value: 'gentle_slope', label: 'Gently Sloping' },
  { value: 'moderate_slope', label: 'Moderate Slopes' },
  { value: 'steep_gradients', label: 'Steep Gradients' },
  { value: 'undulating', label: 'Undulating Topography' },
];

/**
 * Drainage pattern options for topographical features.
 */
export const DRAINAGE_PATTERNS: DropdownOption[] = [
  { value: 'well_drained', label: 'Well Drained' },
  { value: 'adequate_drainage', label: 'Adequate Drainage' },
  { value: 'poor_drainage', label: 'Poor Drainage' },
  { value: 'seasonal_waterlogging', label: 'Seasonal Waterlogging' },
  { value: 'artificial_drainage', label: 'Artificial Drainage Systems' },
];

/**
 * Vegetation type options for topographical features.
 */
export const VEGETATION_TYPES: DropdownOption[] = [
  { value: 'bare_land', label: 'Bare Land' },
  { value: 'grass_coverage', label: 'Grass Coverage' },
  { value: 'shrubs_bushes', label: 'Shrubs and Bushes' },
  { value: 'mature_trees', label: 'Mature Trees' },
  { value: 'mixed_vegetation', label: 'Mixed Vegetation' },
  { value: 'dense_jungle', label: 'Dense Jungle/Forest' },
];

// ===== Building Description Options =====

/**
 * Building type options for building description.
 */
export const BUILDING_TYPES: DropdownOption[] = [
  { value: 'residential', label: 'Residential' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'mixed_use', label: 'Mixed-use' },
  { value: 'outbuilding', label: 'Outbuilding' },
];

/**
 * Building condition options.
 */
export const CONDITIONS: DropdownOption[] = [
  { value: 'new', label: 'New' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
  { value: 'dilapidated', label: 'Dilapidated' },
];

/**
 * Roof type options for building construction.
 */
export const ROOF_TYPES: DropdownOption[] = [
  { value: 'asbestos_sheets', label: 'Asbestos Sheets' },
  { value: 'clay_tiles', label: 'Clay Tiles' },
  { value: 'concrete_flat', label: 'Concrete Flat (RCC)' },
  { value: 'metal_sheets', label: 'Metal Sheets' },
  { value: 'timber_frame', label: 'Timber Frame' },
  { value: 'cadjans', label: 'Cadjans' },
];

/**
 * Wall type options for building construction.
 */
export const WALL_TYPES: DropdownOption[] = [
  { value: 'brick_masonry', label: 'Brick Masonry' },
  { value: 'rcc_columns', label: 'RCC Columns' },
  { value: 'rubble_masonry', label: 'Rubble Masonry' },
  { value: 'timber', label: 'Timber' },
  { value: 'cadjan', label: 'Cadjan' },
  { value: 'plastered', label: 'Plastered' },
  { value: 'color_washed', label: 'Color Washed' },
];

/**
 * Floor type options for building construction.
 */
export const FLOOR_TYPES: DropdownOption[] = [
  { value: 'cement', label: 'Cement' },
  { value: 'tiled', label: 'Tiled' },
  { value: 'terrazzo', label: 'Terrazzo' },
  { value: 'timber', label: 'Timber' },
  { value: 'earth', label: 'Earth' },
];

/**
 * Room type options for accommodation details.
 */
export const ROOM_TYPES = [
  'Balcony',
  'Bathroom',
  'Bedroom',
  'Car Porch',
  'Dining Hall',
  'Garage',
  'Kitchen',
  'Living Hall',
  'Office',
  'Other',
  'Pantry',
  'Store Room',
  'Terrace',
  'Utility Room',
  'Verandah',
] as const;

export type RoomType = typeof ROOM_TYPES[number];

/**
 * Occupier relationship options.
 */
export const OCCUPIER_RELATIONSHIPS: DropdownOption[] = [
  { value: 'owner', label: 'Owner' },
  { value: 'tenant', label: 'Tenant' },
  { value: 'caretaker', label: 'Caretaker' },
  { value: 'family_member', label: 'Family Member' },
  { value: 'vacant', label: 'Vacant' },
];

// ===== Development Feasibility Templates =====

/**
 * Development feasibility templates for bare land reports.
 */
export const DEVELOPMENT_FEASIBILITY_TEMPLATES: DevelopmentFeasibilityTemplate[] = [
  {
    value: '',
    label: '-- Select a template (optional) --',
  },
  {
    value: 'residential_ready',
    label: 'Ready for Residential Development',
    text: 'The land is cleared and ready for residential development. All essential infrastructure including electricity, water supply, and road access are available. The site is suitable for immediate construction without requiring major preparatory work.',
  },
  {
    value: 'residential_potential',
    label: 'Residential Development Potential',
    text: 'The land has good potential for residential development. The location is well-connected with nearby access to main roads and utilities. With proper land preparation and obtaining necessary approvals, the site would be suitable for residential construction.',
  },
  {
    value: 'commercial_ready',
    label: 'Ready for Commercial Development',
    text: 'The property is well-positioned for commercial development with excellent road frontage and visibility. Essential infrastructure is in place, and the zoning permits commercial use. The location benefits from high traffic flow and proximity to commercial centers.',
  },
  {
    value: 'commercial_potential',
    label: 'Commercial Development Potential',
    text: 'The land shows promising potential for commercial development due to its strategic location. Subject to obtaining necessary planning approvals and zoning clearances, the site could be developed for commercial purposes with good accessibility and infrastructure availability.',
  },
  {
    value: 'infrastructure_pending',
    label: 'Infrastructure Development Pending',
    text: 'The land is currently undeveloped but has development potential. Essential infrastructure such as electricity and water connections are planned for the area. Development is feasible once the necessary infrastructure is established and relevant approvals are obtained.',
  },
  {
    value: 'agricultural',
    label: 'Agricultural/Cultivation Use',
    text: 'The land is currently utilized for agricultural purposes. The soil quality and drainage patterns are suitable for cultivation. While primarily suited for agricultural use, the land could potentially be considered for development subject to obtaining necessary change of use approvals.',
  },
  {
    value: 'subdivision_potential',
    label: 'Subdivision Potential',
    text: 'The property has potential for subdivision into multiple parcels, subject to local planning regulations and obtaining necessary approvals. The land extent and configuration are suitable for subdivision, which could enhance overall development value.',
  },
  {
    value: 'ongoing_construction',
    label: 'Construction in Progress',
    text: 'There is ongoing construction activity on the property. Foundation work has been completed and structural work is in progress. The development is being carried out with proper building approvals and is progressing according to plan.',
  },
  {
    value: 'infrastructure_ready',
    label: 'Infrastructure Ready',
    text: 'All necessary infrastructure is in place including water supply connections, electricity, sewerage system, and proper road access. The land is leveled and ready for construction. No major site preparation work is required before commencing development.',
  },
  {
    value: 'planned_development',
    label: 'Planned Development Project',
    text: 'The property is part of a planned development project in the area. Infrastructure improvements are underway, and the locality is witnessing steady development. The land benefits from upcoming infrastructure projects and improved connectivity.',
  },
];

// ===== Helper Functions =====

/**
 * Get the label for a dropdown option by value.
 */
export function getOptionLabel(options: DropdownOption[], value: string): string {
  const option = options.find(opt => opt.value === value);
  return option?.label || value;
}

/**
 * Get development feasibility template text by value.
 */
export function getDevelopmentFeasibilityText(value: string): string {
  const template = DEVELOPMENT_FEASIBILITY_TEMPLATES.find(t => t.value === value);
  return template?.text || '';
}
