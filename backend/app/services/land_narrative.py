"""
AI-powered narrative generation for land descriptions in valuation reports.
Uses Claude API to generate professional, contextual land descriptions.
"""
from typing import Optional, Dict, Any
from .anthropic_client import get_anthropic_client, is_anthropic_configured
from .base_narrative import BaseNarrativeService


def format_land_value(value: str) -> str:
    """Convert snake_case field values to readable text."""
    # Mapping for common land field values
    value_map = {
        # Land shapes
        'rectangular': 'rectangular',
        'square': 'square',
        'triangular': 'triangular',
        'trapezoidal': 'trapezoidal',
        'quadrilateral': 'quadrilateral',
        'irregular': 'irregular',
        'l_shaped': 'L-shaped',
        'pentagon': 'pentagonal',

        # Land types
        'high_land': 'elevated land',
        'low_land': 'low-lying land',
        'flat_land': 'flat land',
        'sloping_land': 'sloping land',
        'paddy_land': 'paddy land',
        'garden_land': 'garden land',

        # Frontage types
        'tarred': 'tarred road',
        'gravel': 'gravel road',
        'concrete_brick_paved': 'concrete/brick paved road',
        'earth': 'earth road',
        'no_frontage': 'no road frontage',

        # Land level
        'at_road_level': 'at road level',
        'above_road_level': 'above road level',
        'below_road_level': 'below road level',

        # Soil types
        'sand_clay': 'sand-clay mixture',
        'gravel_clay': 'gravel-clay mixture',
        'red_earth': 'red earth',
        'loamy': 'loamy soil',
        'rocky': 'rocky soil',
        'marshy': 'marshy soil',

        # Flood risk
        'not_subject': 'not subject to flooding',
        'occasionally_floods': 'occasionally subject to flooding',
        'flood_prone_area': 'flood-prone area',

        # Land condition
        'developed': 'developed',
        'scrub_jungle': 'scrub jungle',
        'cultivated': 'cultivated land',

        # Elevation changes
        'relatively_flat': 'relatively flat',
        'gentle_slope': 'gentle slopes',
        'moderate_slope': 'moderate slopes',
        'steep_gradients': 'steep gradients',
        'undulating': 'undulating terrain',

        # Drainage pattern
        'well_drained': 'well-drained',
        'adequate_drainage': 'adequate drainage',
        'poor_drainage': 'poor drainage',
        'seasonal_waterlogging': 'seasonal waterlogging',
        'artificial_drainage': 'artificial drainage system',

        # Vegetation type
        'grass_coverage': 'grass coverage',
        'shrubs_bushes': 'shrubs and bushes',
        'mature_trees': 'mature trees',
        'mixed_vegetation': 'mixed vegetation',
        'dense_jungle': 'dense jungle'
    }

    return value_map.get(value, value.replace('_', ' ').title())


class LandNarrativeService(BaseNarrativeService):
    """
    Service for generating professional land descriptions for Sri Lankan valuation reports.
    Extends BaseNarrativeService with land-specific prompt engineering and adaptive length.
    """

    def get_service_name(self) -> str:
        return "LAND_NARRATIVE"

    def get_max_tokens(self) -> int:
        return 400

    def _calculate_richness(self, data: Dict[str, Any]) -> tuple:
        """Calculate data richness level and return (level, word_range, sentence_guide, count)."""
        countable_fields = [
            'land_shape', 'land_type', 'land_level', 'land_frontage_type',
            'soil_type', 'flood_risk', 'elevation_changes', 'drainage_pattern',
            'vegetation_type', 'natural_features'
        ]
        data_count = sum(1 for field in countable_fields if data.get(field))

        if data_count <= 3:
            return ("minimal", "30-50 words", "1-2 sentences", data_count)
        elif data_count <= 6:
            return ("moderate", "60-90 words", "3-4 sentences", data_count)
        else:
            return ("rich", "100-140 words", "4-6 sentences", data_count)

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build the land narrative prompt from input data."""
        context_parts = []

        # Basic characteristics
        land_shape = data.get('land_shape')
        if land_shape:
            context_parts.append(f"Land Shape: {format_land_value(land_shape)}")

        land_type = data.get('land_type')
        if land_type:
            context_parts.append(f"Land Type: {format_land_value(land_type)}")

        land_level = data.get('land_level')
        if land_level:
            level_text = f"Land Level: {format_land_value(land_level)}"
            land_level_difference = data.get('land_level_difference')
            if land_level_difference:
                level_text += f" (difference: {land_level_difference} feet)"
            context_parts.append(level_text)

        # Frontage
        land_frontage_type = data.get('land_frontage_type')
        if land_frontage_type:
            frontage_text = f"Road Frontage: {format_land_value(land_frontage_type)}"
            land_frontage_width = data.get('land_frontage_width')
            if land_frontage_width:
                frontage_text += f" ({land_frontage_width} meters wide)"
            context_parts.append(frontage_text)

        land_frontage_description = data.get('land_frontage_description')
        if land_frontage_description:
            context_parts.append(f"Frontage Details: {land_frontage_description}")

        # Soil & Water
        soil_type = data.get('soil_type')
        if soil_type:
            context_parts.append(f"Soil Type: {format_land_value(soil_type)}")

        water_table_depth = data.get('water_table_depth')
        if water_table_depth:
            context_parts.append(f"Water Table Depth: {water_table_depth} feet below ground level")

        # Risks & Conditions
        flood_risk = data.get('flood_risk')
        if flood_risk:
            context_parts.append(f"Flood Risk: {format_land_value(flood_risk)}")

        land_condition = data.get('land_condition')
        if land_condition:
            context_parts.append(f"Land Condition: {format_land_value(land_condition)}")

        # Topographical features
        elevation_changes = data.get('elevation_changes')
        if elevation_changes:
            context_parts.append(f"Elevation: {format_land_value(elevation_changes)}")

        drainage_pattern = data.get('drainage_pattern')
        if drainage_pattern:
            context_parts.append(f"Drainage: {format_land_value(drainage_pattern)}")

        vegetation_type = data.get('vegetation_type')
        if vegetation_type:
            context_parts.append(f"Vegetation: {format_land_value(vegetation_type)}")

        natural_features = data.get('natural_features')
        if natural_features:
            context_parts.append(f"Natural Features: {natural_features}")

        # Determine data richness level
        richness_level, word_range, sentence_guide, data_count = self._calculate_richness(data)

        # Create the full context
        full_context = "\n".join(context_parts) if context_parts else "No data provided"

        return f"""You are a professional property valuer in Sri Lanka writing the LAND DESCRIPTION section of a formal valuation report.

AVAILABLE DATA:
{full_context}

DATA RICHNESS: {richness_level} data provided ({data_count} fields)

CRITICAL INSTRUCTIONS:

1. PARAGRAPH LENGTH REQUIREMENT (MUST FOLLOW):
   - Current data richness: {richness_level}
   - Target length: {word_range} ({sentence_guide})
   - IMPORTANT: Paragraph length MUST be proportional to data available
   - Do NOT write long descriptions when minimal data is provided
   - Do NOT write short descriptions when rich data is provided

2. MANDATORY FIELD USAGE:
   - Use EVERY field provided in the data above
   - If natural_features is provided, it MUST be explicitly mentioned
   - Topographical data (elevation, drainage, vegetation) MUST be woven into the narrative
   - Do NOT omit any provided field

3. STRUCTURE (adapt based on available data):
   - Opening: Shape + Type combination (e.g., "The property comprises a rectangular parcel of elevated land")
   - Level/Elevation: Road level relationship + topography
   - Access: Frontage type, width, and description
   - Soil/Water: Soil composition + water table depth
   - Environmental: Drainage + flood risk + vegetation
   - Natural Features: Explicitly describe if provided
   - Condition: Current state of land

4. STYLE REQUIREMENTS:
   - Professional, formal Sri Lankan valuation report style
   - Use third person for characteristics
   - Technical terminology appropriate for valuers
   - Flowing narrative, NOT bullet points
   - Connect sentences with appropriate transitions
   - Examples: "positioned", "facilitating", "approximately", "comprises", "exhibits"

5. HANDLING PARTIAL DATA:
   - If only 1-2 fields provided: Write concise 1-2 sentence description
   - Focus on what IS provided, do not speculate or add generic filler
   - Avoid phrases like "suitable for development" unless data supports it

EXAMPLE OUTPUTS:

Minimal data (land_shape="rectangular", land_type="high_land"):
"The property comprises a rectangular parcel of elevated land. The land is suitable for residential or commercial development."

Moderate data (shape, type, level, frontage, soil, flood risk):
"The property comprises a rectangular parcel of elevated land positioned approximately 2 feet above the adjacent road level. The land has 12 meters of frontage on a tarred road, facilitating convenient vehicular access. The soil composition is predominantly sand-clay mixture with satisfactory load-bearing characteristics. The land is not subject to flooding and is presently in good condition."

Rich data (all fields including natural features):
"The property comprises a rectangular parcel of elevated land positioned approximately 2 feet above the adjacent road level. The terrain exhibits gentle slopes with undulating characteristics. The land has 12 meters of frontage on a tarred road, facilitating convenient vehicular access. The soil composition is predominantly sand-clay mixture with satisfactory load-bearing characteristics, and the water table is located at approximately 15 feet below the natural ground surface. The property demonstrates adequate natural drainage characteristics and is covered with grass and shrubs. A seasonal pond is located in the southwest corner of the property, adding to its natural features. The land is not subject to flooding and is presently maintained in good condition."

Now generate the land description following the {word_range} guideline:"""


# Singleton instance for the service
_land_narrative_service = LandNarrativeService()


async def generate_land_narrative(
    # Basic characteristics
    land_shape: Optional[str] = None,
    land_type: Optional[str] = None,
    land_level: Optional[str] = None,
    land_level_difference: Optional[float] = None,

    # Frontage
    land_frontage_type: Optional[str] = None,
    land_frontage_width: Optional[float] = None,
    land_frontage_description: Optional[str] = None,

    # Soil & Water
    soil_type: Optional[str] = None,
    water_table_depth: Optional[float] = None,

    # Risks & Conditions
    flood_risk: Optional[str] = None,
    land_condition: Optional[str] = None,

    # Topographical features
    elevation_changes: Optional[str] = None,
    drainage_pattern: Optional[str] = None,
    vegetation_type: Optional[str] = None,
    natural_features: Optional[str] = None
) -> Optional[str]:
    """
    Generate a professional land description narrative using Claude AI.

    The narrative length adapts to the amount of data provided:
    - Minimal data (1-3 fields): 30-50 words
    - Moderate data (4-6 fields): 60-90 words
    - Rich data (7+ fields): 100-140 words

    This function maintains backward compatibility while using the new BaseNarrativeService.
    """
    # Package parameters into data dict for the service
    data = {
        'land_shape': land_shape,
        'land_type': land_type,
        'land_level': land_level,
        'land_level_difference': land_level_difference,
        'land_frontage_type': land_frontage_type,
        'land_frontage_width': land_frontage_width,
        'land_frontage_description': land_frontage_description,
        'soil_type': soil_type,
        'water_table_depth': water_table_depth,
        'flood_risk': flood_risk,
        'land_condition': land_condition,
        'elevation_changes': elevation_changes,
        'drainage_pattern': drainage_pattern,
        'vegetation_type': vegetation_type,
        'natural_features': natural_features
    }

    return await _land_narrative_service.generate(data)
