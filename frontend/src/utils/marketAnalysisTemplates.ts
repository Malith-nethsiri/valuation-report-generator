/**
 * Market Analysis Templates
 *
 * Premade templates for market analysis section categorized by:
 * - Property type (residential, commercial, mixed)
 * - Location type (highway, interior, village, urban)
 */

export interface MarketAnalysisTemplate {
  id: string;
  name: string;
  propertyType: 'residential' | 'commercial' | 'mixed';
  locationType: 'highway' | 'interior' | 'village' | 'urban';
  template: string;
  description: string;
}

export const MARKET_ANALYSIS_TEMPLATES: MarketAnalysisTemplate[] = [
  {
    id: 'res_highway',
    name: 'Residential - Highway Frontage',
    propertyType: 'residential',
    locationType: 'highway',
    description: 'For residential properties with direct highway access',
    template: 'Building blocks in extent about 15-20 perches located fronting {{roadName}} in this village are being sold at LKR {{minRate}}/= Per Perch to LKR {{maxRate}}/= Per Perch, depending on their location, topography, available conveniences, etc.'
  },
  {
    id: 'res_interior',
    name: 'Residential - Interior',
    propertyType: 'residential',
    locationType: 'interior',
    description: 'For residential properties located away from main roads',
    template: 'Residential building blocks in extent about 15-20 Perches located in this village are being sold at rates ranging from LKR {{minRate}}/= Per Perch to LKR {{maxRate}}/= Per Perch, depending on the location, nature of the property and convenience etc.'
  },
  {
    id: 'res_interior_near_road',
    name: 'Residential - Interior (Near Road)',
    propertyType: 'residential',
    locationType: 'interior',
    description: 'For residential properties within 100m of main road',
    template: 'Building blocks in extent about 15-20 perches, interior residential land located within 100 Meters from the road in this village are being sold at LKR {{minRate}}/= Per Perch to LKR {{maxRate}}/= Per Perch depending on their location, topography, available conveniences etc.'
  },
  {
    id: 'res_village',
    name: 'Residential - Village',
    propertyType: 'residential',
    locationType: 'village',
    description: 'For residential properties in village areas',
    template: 'Building blocks in extent about 15-20 Perches located in this village are being sold at Rs {{minRate}}/= Per Perch to Rs {{maxRate}}/= Per Perch influenced by factors affecting the property market.'
  },
  {
    id: 'com_highway',
    name: 'Commercial - Highway',
    propertyType: 'commercial',
    locationType: 'highway',
    description: 'For commercial properties fronting highways',
    template: 'Commercial building blocks in extent about 15-20 Perches located fronting {{roadName}} in this village are being sold at Rs {{minRate}}/= Per Perch to Rs {{maxRate}}/= Per Perch influenced by factors affecting the property market.'
  },
  {
    id: 'com_interior',
    name: 'Commercial - Interior',
    propertyType: 'commercial',
    locationType: 'interior',
    description: 'For commercial properties in interior locations',
    template: 'Commercial building block in extent about 6-10 perches located in this village are being sold at LKR {{minRate}}/= Per Perch to LKR {{maxRate}}/= Per Perch, influenced by factors affecting the property market.'
  },
  {
    id: 'res_urban',
    name: 'Residential - Urban',
    propertyType: 'residential',
    locationType: 'urban',
    description: 'For residential properties in urban/city areas',
    template: 'Building blocks in extent about 10-15 Perches located in this village are being sold at rates ranging from LKR {{minRate}}/= Per Perch to LKR {{maxRate}}/= Per Perch, depending on the access, location, nature of the property and convenience etc.'
  },
  {
    id: 'mixed_highway',
    name: 'Mixed Use - Highway',
    propertyType: 'mixed',
    locationType: 'highway',
    description: 'For mixed-use properties fronting highways',
    template: 'Building blocks in extent about 10-20 perches located fronting {{roadName}} in this area are being sold at LKR {{minRate}}/= Per Perch to LKR {{maxRate}}/= Per Perch, depending on their location, accessibility, and available infrastructure.'
  },
  {
    id: 'res_general',
    name: 'Residential - General',
    propertyType: 'residential',
    locationType: 'village',
    description: 'General residential template - fallback option',
    template: 'Residential land parcels in this locality are being traded at prices ranging from LKR {{minRate}}/= to LKR {{maxRate}}/= per perch, with variations attributable to location advantages, road access quality, topographical features, and proximity to essential amenities.'
  }
];

/**
 * Suggest the most suitable template based on property data
 */
export function suggestTemplate(formData: any): MarketAnalysisTemplate {
  // Infer property type from buildings
  let propertyType: 'residential' | 'commercial' | 'mixed' = 'residential';

  if (formData.buildings && Array.isArray(formData.buildings) && formData.buildings.length > 0) {
    const buildingTypes = formData.buildings.map((b: any) => b.building_type?.toLowerCase() || '');

    const hasCommercial = buildingTypes.some((t: string) =>
      t.includes('commercial') || t.includes('shop') || t.includes('office')
    );
    const hasResidential = buildingTypes.some((t: string) =>
      t.includes('residential') || t.includes('house') || t.includes('bungalow')
    );

    if (hasCommercial && hasResidential) {
      propertyType = 'mixed';
    } else if (hasCommercial) {
      propertyType = 'commercial';
    }
  }

  // Infer location type from access road
  let locationType: 'highway' | 'interior' | 'village' | 'urban' = 'village';

  const roadType = formData.access_road_type?.toLowerCase() || '';
  const roadName = formData.road_access?.toLowerCase() || '';
  const areaType = formData.area_type?.toLowerCase() || '';

  if (roadType.includes('highway') || roadName.includes('highway')) {
    locationType = 'highway';
  } else if (roadType.includes('main road') || roadType.includes('a road') || roadType.includes('b road')) {
    locationType = 'highway';
  } else if (areaType.includes('urban') || areaType.includes('city')) {
    locationType = 'urban';
  } else if (roadType.includes('lane') || roadType.includes('access road') || roadType.includes('internal')) {
    locationType = 'interior';
  }

  // Find matching template
  const matchingTemplates = MARKET_ANALYSIS_TEMPLATES.filter(t =>
    t.propertyType === propertyType && t.locationType === locationType
  );

  if (matchingTemplates.length > 0) {
    return matchingTemplates[0];
  }

  // Fallback to property type match
  const typeMatches = MARKET_ANALYSIS_TEMPLATES.filter(t => t.propertyType === propertyType);
  if (typeMatches.length > 0) {
    return typeMatches[0];
  }

  // Ultimate fallback
  return MARKET_ANALYSIS_TEMPLATES[MARKET_ANALYSIS_TEMPLATES.length - 1];
}

/**
 * Fill template placeholders with actual data
 */
export function fillTemplate(template: string, data: any): string {
  let filled = template;

  // Replace road name
  const roadName = data.road_access || data.access_starting_point_name || '[Road Name]';
  filled = filled.replace(/\{\{roadName\}\}/g, roadName);

  // Calculate rate range from comparable properties
  let minRate = 0;
  let maxRate = 0;

  if (data.comparable_properties && Array.isArray(data.comparable_properties) && data.comparable_properties.length > 0) {
    const rates = data.comparable_properties.map((p: any) => p.rate_per_perch || 0);
    minRate = Math.min(...rates);
    maxRate = Math.max(...rates);
  }

  // If no comparables, use suggested values or placeholders
  if (minRate === 0 && maxRate === 0) {
    minRate = data.valuation_rate_per_perch ? data.valuation_rate_per_perch * 0.8 : 0;
    maxRate = data.valuation_rate_per_perch ? data.valuation_rate_per_perch * 1.2 : 0;
  }

  // Format currency (add thousands separators)
  const formatRate = (rate: number): string => {
    if (rate === 0) return '[Rate]';
    return Math.round(rate).toLocaleString('en-US');
  };

  filled = filled.replace(/\{\{minRate\}\}/g, formatRate(minRate));
  filled = filled.replace(/\{\{maxRate\}\}/g, formatRate(maxRate));

  // Replace village/location if needed
  const village = data.property_village || '[Village]';
  filled = filled.replace(/\{\{village\}\}/g, village);

  return filled;
}

/**
 * Get templates grouped by property type
 */
export function getTemplatesByPropertyType(propertyType: 'residential' | 'commercial' | 'mixed'): MarketAnalysisTemplate[] {
  return MARKET_ANALYSIS_TEMPLATES.filter(t => t.propertyType === propertyType);
}

/**
 * Get all unique property types
 */
export function getPropertyTypes(): Array<'residential' | 'commercial' | 'mixed'> {
  return ['residential', 'commercial', 'mixed'];
}
