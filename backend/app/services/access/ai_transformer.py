"""
AI-powered transformer for converting Google Maps directions to professional valuation report format.
Uses Claude AI to generate natural, professional access descriptions.
"""

import re
from typing import Dict, Any, List, Optional
from ..anthropic_client import get_anthropic_client, AI_DEFAULT_MODEL
from .entity_extractor import extract_navigation_entities, filter_landmarks
from .text_formatter import format_road_names, format_landmarks, format_major_turns, clean_professional_text


def transform_directions_to_professional(
    starting_point_name: str,
    total_distance_km: float,
    total_duration_mins: int,
    property_position: Optional[str] = None,
    road_conditions: Optional[List[Dict[str, Any]]] = None,  # NEW: Simplified format
    road_segments: Optional[List[Dict[str, Any]]] = None,  # DEPRECATED: Old format
    steps: Optional[List[Dict[str, Any]]] = None  # Google Maps turn-by-turn steps
) -> str:
    """
    Transform Google Maps directions with road condition details into professional valuation report format.

    Args:
        starting_point_name: Human-friendly starting point (e.g., "Clock tower junction of Kurunegala town")
        total_distance_km: Total route distance in kilometers
        total_duration_mins: Total route duration in minutes
        property_position: Property position relative to road (e.g., "right", "left")
        road_conditions: NEW: Simplified road conditions array [{road_type, condition, notes}]
        road_segments: DEPRECATED: Old format with per-segment details (kept for backward compatibility)
        steps: Google Maps turn-by-turn steps [{instruction, distance, duration, maneuver}]

    Returns:
        Professional access description text suitable for valuation reports
    """

    # Get singleton client
    client = get_anthropic_client()

    property_side = property_position if property_position else "right"

    # Extract navigation entities from Google Maps steps
    navigation_entities = extract_navigation_entities(steps) if steps else {}

    # Log extracted navigation data for debugging
    print(f"\n[ACCESS_TRANSFORMER] Navigation Entities Extracted:")
    print(f"  Road names: {navigation_entities.get('road_names', [])}")
    print(f"  Landmarks: {navigation_entities.get('landmarks', [])}")
    print(f"  Major turns: {len(navigation_entities.get('major_turns', []))}")
    print(f"  Mode: {'SUMMARY' if road_conditions else 'DETAILED' if road_segments else 'NONE'}")
    if road_conditions:
        road_cond_summary = [f"{c.get('road_type')}-{c.get('condition')}" for c in road_conditions]
        print(f"  Road conditions (summary): {road_cond_summary}")
    print(f"  Total distance: {total_distance_km} km")

    # Build route description from Google Maps steps
    route_description = ""
    if steps and len(steps) > 0:
        route_description = "GOOGLE MAPS TURN-BY-TURN DIRECTIONS:\n"
        for idx, step in enumerate(steps, 1):
            instruction = step.get('instruction', '')
            distance = step.get('distance', '')
            route_description += f"{idx}. {instruction}"
            if distance:
                route_description += f" - {distance}"
            route_description += "\n"

    # Apply landmark filtering to keep only major landmarks
    if navigation_entities.get('landmarks'):
        navigation_entities['landmarks'] = filter_landmarks(navigation_entities['landmarks'])

    # Build road conditions description (NEW simplified format)
    road_conditions_text = ""
    if road_conditions and len(road_conditions) > 0:
        road_conditions_text = "\nROAD SURFACE CONDITIONS:\n"
        road_conditions_text += "List road types encountered with their conditions at the END of the paragraph.\n"
        road_type_map = {
            'paved_road': 'paved road',
            'concrete_road': 'concrete road',
            'carpet_road': 'carpet road',
            'gravel_road': 'gravel road',
            'sand_road': 'sand road',
            'earth_road': 'earth road'
        }
        for cond in road_conditions:
            road_type = road_type_map.get(cond.get('road_type', ''), cond.get('road_type', ''))
            condition = cond.get('condition', '')
            notes = cond.get('notes', '')

            road_conditions_text += f"- {road_type}"
            if condition:
                road_conditions_text += f" in {condition} condition"
            if notes:
                road_conditions_text += f": {notes}"
            road_conditions_text += "\n"

        # CRITICAL: Add anti-hallucination instruction
        road_conditions_text += "\n⚠️ CRITICAL: Add road summary at the VERY END of the paragraph.\n"
        road_conditions_text += "Format: 'The access comprises [road type] in [condition], [road type] in [condition], and [road type] fronting the property.'\n"
        road_conditions_text += "DO NOT mention road classifications (Class A, B, C) anywhere in the output.\n"

    # BACKWARD COMPATIBILITY: Handle old road_segments format if present
    elif road_segments and len(road_segments) > 0:
        road_conditions_text = "\nROAD SEGMENTS (Old Format - with per-segment details):\n"
        for idx, seg in enumerate(road_segments, 1):
            google_data = seg.get('google_maps_data', {})
            user_data = seg.get('user_details', {})

            instruction = google_data.get('instruction', '')
            road_name = google_data.get('road_name', '')

            if instruction:
                road_conditions_text += f"{idx}. {instruction}"
                if road_name:
                    road_conditions_text += f" (Road: {road_name})"
                road_conditions_text += "\n"

            if user_data.get('has_details'):
                road_type_map = {
                    'paved_road': 'paved road',
                    'gravel_road': 'gravel road',
                    'sand_road': 'sand road',
                    'earth_road': 'earth road',
                    'carpet_road': 'carpet road'
                }
                road_type = road_type_map.get(user_data.get('road_type', ''), 'road')
                condition = user_data.get('surface_condition', '')

                road_conditions_text += f"   Surface: {road_type}"
                if condition:
                    road_conditions_text += f" in {condition} condition"
                if user_data.get('road_width_meters'):
                    road_conditions_text += f", width {user_data['road_width_meters']}m"
                if user_data.get('additional_notes'):
                    road_conditions_text += f". {user_data['additional_notes']}"
                road_conditions_text += "\n"

    if not route_description:
        route_description = "No route data provided."

    prompt = f"""Generate professional property access directions in Sri Lankan valuation report style.

════════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS (CRITICAL)
════════════════════════════════════════════════════════════════

1. Single paragraph only
2. DO NOT mention road classifications (Class A, B, C, etc.) ANYWHERE in the output
3. Use ONLY major landmarks for turn references (junctions, towns, railway crossings)
4. Remove minor landmarks (shops, salons, restaurants)
5. Format: Navigation first, then road summary at very end

════════════════════════════════════════════════════════════════
NAVIGATION SECTION (FIRST 80% OF PARAGRAPH)
════════════════════════════════════════════════════════════════

STARTING POINT: {starting_point_name}
TOTAL DISTANCE: {total_distance_km:.1f} km
PROPERTY POSITION: {property_side} side of the road

ROAD NAMES:
{format_road_names(navigation_entities.get('road_names', []))}

MAJOR LANDMARKS (for turn reference only):
{format_landmarks(navigation_entities.get('landmarks', []))}

TURN-BY-TURN DIRECTIONS:
{format_major_turns(navigation_entities.get('major_turns', []))}

Navigation Format:
- Start: "From {{starting_point_name}}, proceed along..."
- Include: Road names, distances ("about X km"), turn directions
- Use landmarks ONLY for WHERE to turn (e.g., "up to Digampathana, turn right", "before Railway crossing turn left")
- End navigation: "...to reach the property on the {{property_side}} hand side of the road fronting same."

════════════════════════════════════════════════════════════════
ROAD SUMMARY SECTION (LAST 20% - AT THE VERY END)
════════════════════════════════════════════════════════════════

{road_conditions_text}

Format: "The access comprises [road type] in [condition], [road type] in [condition], and [road type] fronting the property."
Example: "The access comprises paved road in good condition, gravel road in fair condition, and concrete road in excellent condition fronting the property."

🚨 CRITICAL RULES:
- Add this sentence at the VERY END after the navigation
- DO NOT mention road types inline with navigation
- DO NOT invent distances for road types
- Make this section OPTIONAL - if no road data provided, omit entirely

════════════════════════════════════════════════════════════════
COMPLETE EXAMPLE OUTPUT
════════════════════════════════════════════════════════════════

"From Clocktower junction of Dambulla, proceed along Trincomalee Road for about 17.2km up to Digampathana, turn right on to the road leading to "Aliya Resort" and proceed for about 1km. Then turn left and proceed for about 1.2km to reach the property on the left hand side of the road fronting same. The access comprises paved road in good condition, gravel road in fair condition, and concrete road in excellent condition fronting the property."

════════════════════════════════════════════════════════════════

Return ONLY the professional access description paragraph."""

    try:
        # Call Claude API
        response = client.messages.create(
            model=AI_DEFAULT_MODEL,
            max_tokens=600,  # Increased for detailed output with navigation + road conditions
            temperature=0.5,  # Increased for more natural, varied language while maintaining coherence
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract and return the response text
        professional_text = response.content[0].text.strip()

        # Remove any quotes if Claude wrapped it
        if professional_text.startswith('"') and professional_text.endswith('"'):
            professional_text = professional_text[1:-1]

        # Clean non-English characters and fix formatting
        professional_text = clean_professional_text(professional_text)

        # Validate output if using summary mode (check for hallucinated distances)
        if road_conditions:
            is_valid = validate_summary_mode_output(professional_text, road_conditions)
            if not is_valid:
                print("[WARN] AI generated hallucinated distances. Using fallback...")
                # Use enhanced fallback instead of hallucinated output
                navigation_entities_fallback = extract_navigation_entities(steps) if steps else None
                professional_text = generate_fallback_access_text(
                    starting_point_name=starting_point_name,
                    total_distance_km=total_distance_km,
                    total_duration_mins=total_duration_mins,
                    property_position=property_position,
                    navigation_entities=navigation_entities_fallback
                )

        return professional_text

    except Exception as e:
        raise Exception(f"AI transformation failed: {str(e)}")


def generate_fallback_access_text(
    starting_point_name: str,
    total_distance_km: float,
    total_duration_mins: int,
    property_position: Optional[str] = None,
    navigation_entities: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate fallback access text if AI transformation fails.
    If navigation_entities provided, uses template-based generation with road names and landmarks.
    Otherwise, generates simple generic text.
    """
    property_side = property_position if property_position else "right"
    distance_text = f"{total_distance_km:.1f} km" if total_distance_km >= 1 else f"{int(total_distance_km * 1000)} Meters"

    # Enhanced fallback: use navigation entities if available
    if navigation_entities and (navigation_entities.get('road_names') or navigation_entities.get('landmarks') or navigation_entities.get('major_turns')):
        parts = [f"From {starting_point_name},"]

        road_names = navigation_entities.get('road_names', [])
        landmarks = navigation_entities.get('landmarks', [])
        major_turns = navigation_entities.get('major_turns', [])

        # Add road names and turns if available
        if major_turns:
            for turn in major_turns[:2]:  # Use up to first 2 major turns
                direction = turn.get('direction', '')
                road_name = turn.get('road_name', '')
                if direction and road_name:
                    parts.append(f"turn {direction} onto {road_name}")
                elif direction:
                    parts.append(f"turn {direction}")
        elif road_names:
            # If no turns but have road names, mention the primary road
            parts.append(f"proceed along {road_names[0]}")

        # Add landmarks if available
        if landmarks:
            parts.append(f"passing {landmarks[0]}")

        # Add distance
        parts.append(f"for approximately {distance_text}")

        # Add property position
        parts.append(f"to reach the property on the {property_side} side of the road fronting same.")

        return " ".join(parts)

    # Basic fallback: no navigation entities available
    return (
        f"From {starting_point_name}, proceed for approximately {distance_text} "
        f"(about {total_duration_mins} minutes) to reach the property on the {property_side} "
        f"side of the road fronting same."
    )


def validate_summary_mode_output(text: str, road_conditions: List[Dict[str, Any]]) -> bool:
    """
    Validate that summary mode output doesn't contain hallucinated distance breakdowns
    or road classification mentions (Class A, B, C).
    Returns True if valid, False if contains hallucination patterns.
    """
    # Check for road class mentions (should be absent - NEW validation)
    if re.search(r'\bClass\s+[A-E]\b', text, re.IGNORECASE):
        print(f"[VALIDATION FAILED] Output contains road classification (Class A/B/C) which should not be shown")
        return False

    if not road_conditions:
        return True

    # Check for patterns like "X km paved road" or "X Kilometers carpet road"
    road_type_map = {
        'paved_road': ['paved', 'asphalt'],
        'concrete_road': ['concrete'],
        'carpet_road': ['carpet'],
        'gravel_road': ['gravel'],
        'sand_road': ['sand'],
        'earth_road': ['earth']
    }

    for cond in road_conditions:
        road_type = cond.get('road_type', '')
        type_keywords = road_type_map.get(road_type, [])

        for keyword in type_keywords:
            # Pattern 1: "14.4 Kilometers paved road" or "13km carpet road"
            pattern1 = rf'\d+\.?\d*\s*(?:km|kilometers?)\s+(?:of\s+)?{keyword}\s+road'
            if re.search(pattern1, text, re.IGNORECASE):
                print(f"[VALIDATION FAILED] Detected hallucinated distance allocation: '{keyword} road' with distance")
                return False

            # Pattern 2: "paved road in excellent condition for about 14.4 Kilometers"
            pattern2 = rf'{keyword}\s+road.*?for\s+about\s+\d+\.?\d*\s*(?:km|kilometers?)'
            if re.search(pattern2, text, re.IGNORECASE):
                # This is OK if it's part of a named road, but suspicious if standalone
                match = re.search(pattern2, text, re.IGNORECASE)
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                # Check if there's a road name before the road type
                if not re.search(r'[A-Z][a-z]+\s+(Road|Hwy|Highway|Street|Mawatha|Veediya)', context[:50]):
                    print(f"[VALIDATION WARNING] Suspicious pattern detected: standalone '{keyword} road' with distance")

    return True
