// Enhanced Land Description Generator
// Generates professional, flowing land descriptions from form data

interface LandDescriptionData {
  land_shape?: string;
  land_type?: string;
  land_level?: string;
  land_level_difference?: number;
  land_frontage_type?: string;
  land_frontage_width?: number;
  soil_type?: string;
  water_table_depth?: number;
  flood_risk?: string;
  land_condition?: string;
  land_frontage_description?: string;
  // Topographical Features
  elevation_changes?: string;
  drainage_pattern?: string;
  vegetation_type?: string;
  natural_features?: string;
}

// Helper function to select random variation
function selectVariation(templates: string[]): string {
  return templates[Math.floor(Math.random() * templates.length)];
}

// Helper function to normalize values for template keys
function normalizeValue(value: string | undefined): string {
  if (!value) return '';
  return value.toLowerCase().replace(/\s+/g, '_');
}

// Opening templates based on shape and type combinations
function buildOpeningParagraph(shape?: string, landType?: string): string {
  const shapeNorm = normalizeValue(shape);
  const typeNorm = normalizeValue(landType);

  const templates: Record<string, string[]> = {
    'rectangular_high_land': [
      'This property comprises a rectangular parcel of elevated land that commands an advantageous position',
      'A well-proportioned rectangular plot of elevated terrain forms the basis of this property',
      'The property consists of a rectangular expanse of naturally elevated land',
    ],
    'rectangular_low_land': [
      'The property encompasses a rectangular plot of lower-lying land',
      'A rectangular parcel of lower elevation land forms the basis of this property',
      'This rectangular property is situated on lower-lying terrain',
    ],
    'rectangular_flat_land': [
      'The property comprises a rectangular parcel of evenly graded land',
      'A well-proportioned rectangular plot of level terrain forms this property',
      'The property consists of a rectangular block of flat land',
    ],
    'square_high_land': [
      'This property comprises a square-shaped parcel of elevated land',
      'A uniformly proportioned square plot of elevated terrain constitutes this property',
      'The property consists of a square block of naturally raised land',
    ],
    'square_low_land': [
      'The property encompasses a square-shaped plot of lower-lying land',
      'A well-proportioned square parcel of lower elevation land forms the basis of this property',
      'This square property is situated on lower-lying terrain',
    ],
    'square_flat_land': [
      'The property comprises a square-shaped plot of evenly graded land',
      'A uniformly proportioned square parcel of flat land constitutes this property',
      'The subject property consists of a square block of level terrain',
    ],
    'irregular_sloping_land': [
      'The property features an irregular boundary encompassing sloping terrain',
      'This irregularly-shaped property is characterized by sloping topography',
      'An irregular parcel of land with pronounced slopes forms the property',
    ],
    'l-shaped_paddy_land': [
      'The property takes an L-shaped configuration, encompassing paddy land',
      'An L-shaped parcel of paddy cultivation land comprises this property',
      'The property is configured in an L-shape and contains productive paddy land',
    ],
    'pentagon_garden_land': [
      'The property is configured as a five-sided parcel designated for horticultural use',
      'A pentagonal plot of cultivated garden land forms this property',
      'The property comprises a pentagon-shaped parcel of productive garden land',
    ],
  };

  const key = `${shapeNorm}_${typeNorm}`;
  if (templates[key]) {
    return selectVariation(templates[key]);
  }

  // Fallback to shape-only or type-only templates
  if (shapeNorm && typeNorm) {
    const shapeDescriptions: Record<string, string> = {
      'rectangular': 'a rectangular parcel',
      'square': 'a square-shaped plot',
      'triangular': 'a triangular parcel',
      'trapezoidal': 'a trapezoidal plot',
      'quadrilateral': 'a four-sided parcel',
      'irregular': 'an irregularly-shaped parcel',
      'l-shaped': 'an L-shaped plot',
      'pentagon': 'a pentagonal parcel',
    };

    const typeDescriptions: Record<string, string> = {
      'high_land': 'elevated land',
      'low_land': 'lower-lying land',
      'flat_land': 'level land',
      'sloping_land': 'sloping terrain',
      'paddy_land': 'paddy cultivation land',
      'garden_land': 'garden land',
    };

    const shapeDesc = shapeDescriptions[shapeNorm] || 'a parcel';
    const typeDesc = typeDescriptions[typeNorm] || 'land';

    return `The property comprises ${shapeDesc} of ${typeDesc}`;
  }

  return 'The property comprises a parcel of land';
}

// Build land level description
function buildLandLevelSentence(level?: string, levelDifference?: number): string {
  if (!level) return '';

  const levelNorm = normalizeValue(level);
  const hasDifference = levelDifference && levelDifference > 0;

  const templates: Record<string, { noLevelDiff: string[]; withLevelDiff: string[] }> = {
    'at_road_level': {
      noLevelDiff: [
        'The land is situated at the level of the abutting road, facilitating convenient access',
        'Being at road level, the property enjoys easy and unimpeded approach from the roadway',
        'The land surface aligns with the adjacent road elevation, ensuring straightforward access',
      ],
      withLevelDiff: [
        'The land surface is approximately at the level of the abutting road with minimal grade variations',
        'Aligned with the road level, the property maintains a consistent grade throughout',
      ],
    },
    'above_road_level': {
      noLevelDiff: [
        'The property is situated at an elevated position relative to the abutting road',
        'The land rises above the road level, positioning the property at a commanding height',
        'Being elevated above the roadway, the property benefits from superior drainage characteristics',
      ],
      withLevelDiff: hasDifference ? [
        `The land rises approximately ${levelDifference} feet above the adjacent road level, providing elevation benefits`,
        `Positioned approximately ${levelDifference} feet above the road elevation, the property enjoys advantageous height`,
        `The property rises approximately ${levelDifference} feet above the roadway, ensuring excellent natural drainage`,
      ] : [],
    },
    'below_road_level': {
      noLevelDiff: [
        'The property is situated below the level of the abutting road',
        'The land lies at a depression relative to the adjacent roadway',
        'Being positioned below the road level, the property requires consideration for drainage management',
      ],
      withLevelDiff: hasDifference ? [
        `The land surface is approximately ${levelDifference} feet below the adjacent road level, requiring drainage provisions`,
        `The property lies approximately ${levelDifference} feet below the roadway elevation`,
        `Situated approximately ${levelDifference} feet below the road level, the property necessitates careful drainage planning`,
      ] : [],
    },
  };

  const template = templates[levelNorm];
  if (!template) return '';

  const selectedTemplates = hasDifference && template.withLevelDiff.length > 0
    ? template.withLevelDiff
    : template.noLevelDiff;

  return selectVariation(selectedTemplates);
}

// Build frontage description
function buildFrontageSentence(frontageType?: string, frontageWidth?: number): string {
  if (!frontageType) return '';

  const typeNorm = normalizeValue(frontageType);
  const hasWidth = frontageWidth && frontageWidth > 0;

  const templates: Record<string, { noWidth: string[]; withWidth: string[] }> = {
    'tarred_road': {
      noWidth: [
        'The property has frontage on a tarred (asphalt) road, ensuring all-weather access',
        'Road access is provided via tarred surfacing, facilitating year-round accessibility',
        'The property benefits from frontage on a well-maintained tarred roadway',
      ],
      withWidth: hasWidth ? [
        `The property has approximately ${frontageWidth} meters of frontage on a tarred road, ensuring convenient access`,
        `Frontage of approximately ${frontageWidth} meters on a tarred roadway provides excellent accessibility`,
        `The property enjoys approximately ${frontageWidth} meters of frontage on a sealed tar-macadam road`,
      ] : [],
    },
    'gravel_road': {
      noWidth: [
        'Road access is available via a gravel road surface',
        'The property has access through a gravel road',
        'Frontage is provided on a gravel road',
      ],
      withWidth: hasWidth ? [
        `The property has frontage of approximately ${frontageWidth} meters on a gravel road`,
        `A gravel road providing approximately ${frontageWidth} meters of frontage affords access to the property`,
        `The property fronts approximately ${frontageWidth} meters on a gravel roadway`,
      ] : [],
    },
    'concrete_brick_paved': {
      noWidth: [
        'Road access is provided via a concrete brick paved surface',
        'The property has frontage on a concrete brick paved road',
        'Frontage is on a well-constructed concrete brick paved roadway',
      ],
      withWidth: hasWidth ? [
        `The property has approximately ${frontageWidth} meters of frontage on a concrete brick paved road`,
        `Approximately ${frontageWidth} meters of frontage on a concrete brick paved surface provides access`,
        `The property fronts approximately ${frontageWidth} meters on a paved concrete brick roadway`,
      ] : [],
    },
    'earth_road': {
      noWidth: [
        'Access is provided via an earth road',
        'The property has frontage on an earth road',
        'An earth road affords access to the property',
      ],
      withWidth: hasWidth ? [
        `The property has approximately ${frontageWidth} meters of frontage on an earth road`,
        `An earth road with approximately ${frontageWidth} meters of frontage provides access`,
        `The property fronts approximately ${frontageWidth} meters on an earth roadway`,
      ] : [],
    },
    'no_road_frontage': {
      noWidth: [
        'The property does not have direct road frontage',
        'Direct road frontage is not available for this property',
        'The property is accessed via a right-of-way or indirect means',
      ],
      withWidth: [],
    },
  };

  const template = templates[typeNorm];
  if (!template) return '';

  const selectedTemplates = hasWidth && template.withWidth.length > 0
    ? template.withWidth
    : template.noWidth;

  return selectVariation(selectedTemplates);
}

// Build soil and water table description (combined)
function buildSoilSentence(soilType?: string, waterTableDepth?: number): string {
  if (!soilType) return '';

  const typeNorm = normalizeValue(soilType);
  const hasWaterTable = waterTableDepth && waterTableDepth > 0;

  const templates: Record<string, { noWaterTable: string[]; withWaterTable: string[] }> = {
    'sand_clay': {
      noWaterTable: [
        'The soil composition comprises sand-clay mixture, presenting good load-bearing capacity',
        'Sand and clay mixture constitutes the soil, offering adequate structural support',
        'The predominant soil type is sand-clay mixture with satisfactory bearing strength',
      ],
      withWaterTable: hasWaterTable ? [
        `The soil is predominantly sand-clay mixture with satisfactory load-bearing characteristics; the water table is located at approximately ${waterTableDepth} feet below the natural ground surface`,
        `A sand-clay soil matrix provides good structural support, with subsurface water occurring at approximately ${waterTableDepth} feet below ground level`,
        `The soil comprises sand-clay mixture in favorable proportions; the water table is found at approximately ${waterTableDepth} feet depth`,
      ] : [],
    },
    'gravel_clay': {
      noWaterTable: [
        'Gravel-clay mixture forms the soil, offering excellent drainage and stability',
        'The soil is primarily gravel-clay matrix with superior bearing capacity',
        'Gravel-clay composition provides robust structural foundations',
      ],
      withWaterTable: hasWaterTable ? [
        `The soil comprises gravel-clay mixture with superior drainage characteristics; the water table depth is approximately ${waterTableDepth} feet below surface`,
        `Gravel-clay soil affords excellent load-bearing capacity, with the water table occurring at approximately ${waterTableDepth} feet depth`,
        `A gravel-clay soil composition with good permeability characteristics; the water table is at approximately ${waterTableDepth} feet below ground level`,
      ] : [],
    },
    'red_earth': {
      noWaterTable: [
        'Red earth forms the primary soil constituent',
        'The soil is predominantly red earth type',
        'Red earth comprises the soil matrix',
      ],
      withWaterTable: hasWaterTable ? [
        `The soil composition is predominantly red earth; the water table is located at approximately ${waterTableDepth} feet below the surface`,
        `Red earth constitutes the soil matrix, with subsurface water occurring at approximately ${waterTableDepth} feet depth`,
        `The primary soil is red earth; the water table is at approximately ${waterTableDepth} feet below ground level`,
      ] : [],
    },
    'loamy': {
      noWaterTable: [
        'Loamy soil composition provides balanced drainage and retention properties',
        'The soil is loamy in nature with good workability',
        'Loam forms the soil matrix with favorable geotechnical properties',
      ],
      withWaterTable: hasWaterTable ? [
        `Loamy soil provides favorable characteristics for development; the water table is at approximately ${waterTableDepth} feet below surface`,
        `The soil matrix is predominantly loam, with the water table occurring at approximately ${waterTableDepth} feet depth`,
        `Loamy soil composition offers good development potential; the water table is at approximately ${waterTableDepth} feet below ground level`,
      ] : [],
    },
    'rocky': {
      noWaterTable: [
        'Rocky soil composition may require special consideration for development',
        'The soil contains significant rock content',
        'Rocky terrain characterizes the subsurface composition',
      ],
      withWaterTable: hasWaterTable ? [
        `Rocky composition characterizes the subsurface; the water table is at approximately ${waterTableDepth} feet depth`,
        `Rock formations are present in the soil profile, with the water table at approximately ${waterTableDepth} feet below ground level`,
        `The soil contains substantial rock content; the water table depth is approximately ${waterTableDepth} feet`,
      ] : [],
    },
    'marshy': {
      noWaterTable: [
        'Marshy soil conditions exist, requiring drainage considerations',
        'The property contains marshy soil characteristics',
        'Marshy terrain requires careful environmental planning',
      ],
      withWaterTable: hasWaterTable ? [
        `Marshy conditions prevail, with the water table occurring at approximately ${waterTableDepth} feet below surface`,
        `Marshy soil characteristics are present, with an elevated water table at approximately ${waterTableDepth} feet below ground level`,
        `The property exhibits marshy characteristics; the water table is at approximately ${waterTableDepth} feet depth`,
      ] : [],
    },
  };

  const template = templates[typeNorm];
  if (!template) return '';

  const selectedTemplates = hasWaterTable && template.withWaterTable.length > 0
    ? template.withWaterTable
    : template.noWaterTable;

  return selectVariation(selectedTemplates);
}

// Build flood risk description
function buildFloodSentence(floodRisk?: string): string {
  if (!floodRisk) return '';

  const riskNorm = normalizeValue(floodRisk);

  const templates: Record<string, string[]> = {
    'not_subject_to_flooding': [
      'The property is not subject to flooding',
      'Flooding is not a typical concern for this property',
      'The location does not present flood-related risks',
      'The property is situated in a non-flood-prone zone',
    ],
    'occasionally_floods': [
      'The property is occasionally subject to flooding during periods of excessive rainfall',
      'The property experiences occasional inundation during heavy precipitation events',
      'Flooding may occur periodically during monsoon or heavy rain periods',
      'The property is in an area that occasionally experiences flooding conditions',
    ],
    'flood_prone_area': [
      'The property is located in an area prone to flooding',
      'This location is designated as flood-prone and requires careful water management',
      'The property is subject to regular or recurring flood risk',
      'Flooding is a persistent consideration for this property location',
    ],
  };

  const template = templates[riskNorm];
  if (!template) return '';

  return selectVariation(template);
}

// Build land condition description
function buildConditionSentence(landCondition?: string): string {
  if (!landCondition) return '';

  const conditionNorm = normalizeValue(landCondition);

  const templates: Record<string, string[]> = {
    'developed': [
      'The land is presently developed with existing improvements in place',
      'Development has occurred on the property with improvements present',
      'The property is in a developed state with infrastructure in place',
    ],
    'bare_land': [
      'The property is bare land awaiting development',
      'The land remains in a natural, undeveloped state',
      'No improvements or developments are present on the land at this time',
    ],
    'scrub_jungle': [
      'Scrub jungle and secondary vegetation cover the property',
      'The property is covered with scrub jungle vegetation',
      'Dense scrub jungle comprises the current land cover',
    ],
    'cultivated': [
      'The property is currently under active cultivation',
      'Agricultural cultivation is being conducted on the property',
      'The land is maintained under productive cultivation',
    ],
    'marshy': [
      'Marshy conditions and wetland characteristics define the property',
      'The property exhibits marshy conditions requiring environmental consideration',
      'Wetland and marshy characteristics are present throughout the property',
    ],
  };

  const template = templates[conditionNorm];
  if (!template) return '';

  return selectVariation(template);
}

// Build topographical features sentence
function buildTopographicalSentence(data: LandDescriptionData): string {
  const parts: string[] = [];

  const elevationTemplates: Record<string, string> = {
    'relatively_flat': 'The land exhibits minimal elevation changes with a relatively uniform grade',
    'gentle_slope': 'The terrain features gentle slopes providing natural drainage characteristics',
    'moderate_slope': 'Moderate slopes are present across the property',
    'steep_gradients': 'The land is characterized by steep gradients',
    'undulating': 'The topography is notably undulating with varied elevations'
  };

  const drainageTemplates: Record<string, string> = {
    'well_drained': 'and demonstrates excellent natural drainage',
    'adequate_drainage': 'with adequate drainage characteristics',
    'poor_drainage': 'though drainage is impeded with evidence of water retention',
    'seasonal_waterlogging': 'with seasonal waterlogging in certain areas',
    'artificial_drainage': 'complemented by artificial drainage systems'
  };

  const vegetationTemplates: Record<string, string> = {
    'bare_land': 'The land is predominantly bare with minimal vegetation',
    'grass_coverage': 'Grass coverage is evident throughout the property',
    'shrubs_bushes': 'The land supports shrubs and bushes',
    'mature_trees': 'Mature trees are established on the property',
    'mixed_vegetation': 'Mixed vegetation including fruit-bearing trees is present',
    'dense_jungle': 'Dense jungle cover characterizes the land'
  };

  // Build elevation + drainage sentence
  const elevationNorm = normalizeValue(data.elevation_changes);
  const drainageNorm = normalizeValue(data.drainage_pattern);

  if (elevationNorm && elevationTemplates[elevationNorm]) {
    let sentence = elevationTemplates[elevationNorm];
    if (drainageNorm && drainageTemplates[drainageNorm]) {
      sentence += ' ' + drainageTemplates[drainageNorm];
    }
    parts.push(sentence + '.');
  }

  // Add vegetation sentence
  const vegetationNorm = normalizeValue(data.vegetation_type);
  if (vegetationNorm && vegetationTemplates[vegetationNorm]) {
    parts.push(vegetationTemplates[vegetationNorm] + '.');
  }

  // Add natural features
  if (data.natural_features?.trim()) {
    parts.push(`Notable natural features include ${data.natural_features.trim()}.`);
  }

  return parts.join(' ');
}

// Main generator function
export function generateEnhancedLandDescription(data: LandDescriptionData): string {
  const parts: string[] = [];

  // 1. Opening paragraph (shape + type)
  const opening = buildOpeningParagraph(data.land_shape, data.land_type);
  parts.push(opening);

  // 2. Land level description
  const levelDesc = buildLandLevelSentence(data.land_level, data.land_level_difference);
  if (levelDesc) {
    parts.push(levelDesc);
  }

  // 3. Topographical features (NEW)
  const topoDesc = buildTopographicalSentence(data);
  if (topoDesc) {
    parts.push(topoDesc);
  }

  // 4. Frontage description
  const frontageDesc = buildFrontageSentence(data.land_frontage_type, data.land_frontage_width);
  if (frontageDesc) {
    parts.push(frontageDesc);
  }

  // 5. Soil and water table description
  const soilDesc = buildSoilSentence(data.soil_type, data.water_table_depth);
  if (soilDesc) {
    parts.push(soilDesc);
  }

  // 6. Flood risk description
  const floodDesc = buildFloodSentence(data.flood_risk);
  if (floodDesc) {
    parts.push(floodDesc);
  }

  // 7. Land condition description
  const conditionDesc = buildConditionSentence(data.land_condition);
  if (conditionDesc) {
    parts.push(conditionDesc);
  }

  // 8. Add additional frontage description if provided
  if (data.land_frontage_description && data.land_frontage_description.trim()) {
    parts.push(data.land_frontage_description.trim());
  }

  // Combine all parts into a flowing paragraph with appropriate connectors
  if (parts.length === 0) {
    return 'The property comprises a parcel of land.';
  }

  // Join sentences with periods and proper spacing
  let description = parts[0];

  for (let i = 1; i < parts.length; i++) {
    const currentPart = parts[i];
    const previousPart = parts[i - 1];

    // Determine connector based on context
    // Use period for most transitions, semicolon for closely related clauses
    if (previousPart.includes('water table') || currentPart.includes('water table')) {
      // Already combined in soil sentence
      continue;
    }

    // Add appropriate spacing
    if (!description.endsWith('.')) {
      description += '.';
    }
    description += ' ' + currentPart;
  }

  // Ensure final period
  if (!description.endsWith('.')) {
    description += '.';
  }

  return description;
}
