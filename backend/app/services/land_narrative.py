"""
AI-powered narrative generation for land descriptions in valuation reports.
Uses Claude API to generate professional, contextual land descriptions.
"""
import os
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


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
        'bare_land': 'bare land',
        'scrub_jungle': 'scrub jungle',
        'cultivated': 'cultivated land',
        'marshy': 'marshy',

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
        'bare_land': 'bare',
        'grass_coverage': 'grass coverage',
        'shrubs_bushes': 'shrubs and bushes',
        'mature_trees': 'mature trees',
        'mixed_vegetation': 'mixed vegetation',
        'dense_jungle': 'dense jungle'
    }

    return value_map.get(value, value.replace('_', ' ').title())


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

    Args:
        All land-related data fields (all optional)

    Returns:
        Generated narrative text or None if generation fails
    """
    if not ANTHROPIC_API_KEY:
        print("[LAND_NARRATIVE] Warning: ANTHROPIC_API_KEY not set")
        return None

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build the context for AI
        context_parts = []

        # Count non-null fields to determine data richness
        data_count = 0

        # Basic characteristics
        if land_shape:
            context_parts.append(f"Land Shape: {format_land_value(land_shape)}")
            data_count += 1

        if land_type:
            context_parts.append(f"Land Type: {format_land_value(land_type)}")
            data_count += 1

        if land_level:
            level_text = f"Land Level: {format_land_value(land_level)}"
            if land_level_difference:
                level_text += f" (difference: {land_level_difference} feet)"
            context_parts.append(level_text)
            data_count += 1

        # Frontage
        if land_frontage_type:
            frontage_text = f"Road Frontage: {format_land_value(land_frontage_type)}"
            if land_frontage_width:
                frontage_text += f" ({land_frontage_width} meters wide)"
            context_parts.append(frontage_text)
            data_count += 1

        if land_frontage_description:
            context_parts.append(f"Frontage Details: {land_frontage_description}")

        # Soil & Water
        if soil_type:
            context_parts.append(f"Soil Type: {format_land_value(soil_type)}")
            data_count += 1

        if water_table_depth:
            context_parts.append(f"Water Table Depth: {water_table_depth} feet below ground level")

        # Risks & Conditions
        if flood_risk:
            context_parts.append(f"Flood Risk: {format_land_value(flood_risk)}")
            data_count += 1

        if land_condition:
            context_parts.append(f"Land Condition: {format_land_value(land_condition)}")

        # Topographical features
        if elevation_changes:
            context_parts.append(f"Elevation: {format_land_value(elevation_changes)}")
            data_count += 1

        if drainage_pattern:
            context_parts.append(f"Drainage: {format_land_value(drainage_pattern)}")
            data_count += 1

        if vegetation_type:
            context_parts.append(f"Vegetation: {format_land_value(vegetation_type)}")
            data_count += 1

        if natural_features:
            context_parts.append(f"Natural Features: {natural_features}")
            data_count += 1

        # Determine data richness level
        if data_count <= 3:
            richness_level = "minimal"
            word_range = "30-50 words"
            sentence_guide = "1-2 sentences"
        elif data_count <= 6:
            richness_level = "moderate"
            word_range = "60-90 words"
            sentence_guide = "3-4 sentences"
        else:
            richness_level = "rich"
            word_range = "100-140 words"
            sentence_guide = "4-6 sentences"

        # Create the full context
        full_context = "\n".join(context_parts) if context_parts else "No data provided"

        # Construct the prompt
        prompt = f"""You are a professional property valuer in Sri Lanka writing the LAND DESCRIPTION section of a formal valuation report.

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

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Same model as other narrative services
            max_tokens=400,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the generated text
        if message.content and len(message.content) > 0:
            narrative = message.content[0].text.strip()
            word_count = len(narrative.split())
            print(f"[LAND_NARRATIVE] Successfully generated narrative ({word_count} words, {len(narrative)} chars)")
            print(f"[LAND_NARRATIVE] Data richness: {richness_level} ({data_count} fields provided)")
            return narrative
        else:
            print("[LAND_NARRATIVE] No content in Claude response")
            return None

    except Exception as e:
        print(f"[LAND_NARRATIVE] Error generating narrative: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
