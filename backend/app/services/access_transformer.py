"""
AI-powered transformer for converting Google Maps directions to professional valuation report format.
Uses Claude AI to generate natural, professional access descriptions.
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
import re


def extract_navigation_entities(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pre-process Google Maps steps to extract key navigation entities.

    Args:
        steps: Google Maps turn-by-turn steps with instruction, distance, duration, maneuver

    Returns:
        Dict containing:
            - road_names: List of unique road names
            - landmarks: List of landmarks (hotels, hospitals, junctions, etc.)
            - major_turns: List of significant turn instructions
            - segments: Consolidated route segments
    """
    if not steps:
        return {
            "road_names": [],
            "landmarks": [],
            "major_turns": [],
            "segments": []
        }

    road_names = []
    landmarks = []
    major_turns = []
    segments = []

    # Keywords for identifying landmarks
    landmark_keywords = [
        'hotel', 'hospital', 'medical', 'school', 'college', 'university',
        'church', 'temple', 'mosque', 'junction', 'crossing', 'railway',
        'station', 'market', 'mall', 'restaurant', 'bank', 'post office',
        'police', 'clinic', 'pharmacy', 'bakery', 'museum', 'park'
    ]

    for idx, step in enumerate(steps):
        instruction = step.get('instruction', '')
        distance = step.get('distance', '')
        maneuver = step.get('maneuver', '')

        # Clean HTML tags from instruction
        clean_instruction = re.sub(r'<[^>]+>', '', instruction)

        # Extract road names using patterns like "onto XYZ Road" or "along ABC Highway"
        # Pattern: onto/along/via followed by capitalized words
        road_patterns = [
            r'(?:onto|along|via|on)\s+([A-Z][^,\.]+?(?:Road|Rd|Highway|Hwy|Street|St|Lane|Avenue|Ave|Mawatha|Veediya|[A-Z]\d+))',
            r'(?:onto|along|via|on)\s+([A-Z][^,\.]+?\s*/\s*[A-Z]\d+)',  # Highway names with numbers like A6
            r'Continue to follow\s+([A-Z][^,\.]+)',
            r'Turn\s+(?:left|right).*?onto\s+([A-Z][^,\.]+)'
        ]

        for pattern in road_patterns:
            matches = re.findall(pattern, clean_instruction, re.IGNORECASE)
            for match in matches:
                # Clean up the road name
                road_name = match.strip()
                # Prefer shorter variants (e.g., "A6" over long multi-part names)
                if '/' in road_name:
                    # Split by / and prefer the shortest meaningful part
                    parts = [p.strip() for p in road_name.split('/')]
                    # Prefer parts that are just highway numbers (A6, E01, etc.)
                    short_parts = [p for p in parts if re.match(r'^[A-Z]\d+$', p)]
                    if short_parts:
                        road_name = short_parts[0]
                    else:
                        # Use the shortest part
                        road_name = min(parts, key=len)

                if road_name and road_name not in road_names:
                    road_names.append(road_name)

        # Extract landmarks (proper nouns, especially with landmark keywords)
        # Look for capitalized phrases that contain landmark keywords
        words = clean_instruction.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,;:()')
            if word_lower in landmark_keywords:
                # Extract surrounding capitalized words
                landmark_parts = []
                # Look backward
                j = i - 1
                while j >= 0 and words[j] and words[j][0].isupper():
                    landmark_parts.insert(0, words[j])
                    j -= 1
                # Add the keyword itself
                landmark_parts.append(word.strip('.,;:()'))
                # Look forward
                j = i + 1
                while j < len(words) and words[j] and words[j][0].isupper():
                    landmark_parts.append(words[j].strip('.,;:()'))
                    j += 1

                if len(landmark_parts) >= 2:  # At least 2 words (e.g., "Railway Crossing")
                    landmark = ' '.join(landmark_parts)
                    if landmark and landmark not in landmarks:
                        landmarks.append(landmark)

        # Also extract landmarks from phrases like "at XYZ" or "Pass by XYZ"
        at_patterns = [
            r'at\s+([A-Z][A-Za-z\s&]+?)(?:\s+onto|\s+\d|\.|$)',
            r'Pass by\s+([A-Z][A-Za-z\s&]+?)(?:\s+\(on|$)'
        ]
        for pattern in at_patterns:
            matches = re.findall(pattern, clean_instruction)
            for match in matches:
                landmark = match.strip()
                if landmark and len(landmark) > 3 and landmark not in landmarks:
                    landmarks.append(landmark)

        # Identify major turns (not continuations or small adjustments)
        is_turn = 'turn' in clean_instruction.lower() and ('left' in clean_instruction.lower() or 'right' in clean_instruction.lower())

        if is_turn or maneuver in ['turn-left', 'turn-right', 'ramp-left', 'ramp-right']:
            turn_direction = 'left' if 'left' in clean_instruction.lower() else 'right'
            # Extract road name from this turn if available
            turn_road = None
            for pattern in road_patterns:
                matches = re.findall(pattern, clean_instruction, re.IGNORECASE)
                if matches:
                    turn_road = matches[0].strip()
                    if '/' in turn_road:
                        parts = [p.strip() for p in turn_road.split('/')]
                        short_parts = [p for p in parts if re.match(r'^[A-Z]\d+$', p)]
                        if short_parts:
                            turn_road = short_parts[0]
                        else:
                            turn_road = min(parts, key=len)
                    break

            major_turns.append({
                "instruction": clean_instruction,
                "direction": turn_direction,
                "road_name": turn_road,
                "distance": distance
            })

        # Build segments
        segments.append({
            "instruction": clean_instruction,
            "distance": distance,
            "is_turn": is_turn
        })

    return {
        "road_names": road_names,
        "landmarks": landmarks,
        "major_turns": major_turns,
        "segments": segments
    }


def format_road_names(road_names: List[str]) -> str:
    """Format list of road names for AI prompt."""
    if not road_names:
        return "No specific road names identified."

    formatted = []
    for name in road_names:
        formatted.append(f"  - {name}")
    return "\n".join(formatted)


def format_landmarks(landmarks: List[str]) -> str:
    """Format list of landmarks for AI prompt."""
    if not landmarks:
        return "No specific landmarks identified."

    formatted = []
    for landmark in landmarks:
        formatted.append(f"  - {landmark}")
    return "\n".join(formatted)


def format_major_turns(turns: List[Dict[str, Any]]) -> str:
    """Format list of major turns for AI prompt."""
    if not turns:
        return "No significant turns identified."

    formatted = []
    for idx, turn in enumerate(turns, 1):
        turn_text = f"{idx}. Turn {turn['direction']}"
        if turn.get('road_name'):
            turn_text += f" onto {turn['road_name']}"
        if turn.get('distance'):
            turn_text += f" ({turn['distance']})"
        formatted.append(turn_text)

    return "\n".join(formatted)


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

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

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

    # Build road conditions description (NEW simplified format)
    road_conditions_text = ""
    if road_conditions and len(road_conditions) > 0:
        road_conditions_text = "\nROAD SURFACE CONDITIONS (Apply to entire route - NO per-type distances):\n"
        road_conditions_text += "These road types exist along the route. Integrate them naturally into turn-by-turn navigation.\n"
        road_type_map = {
            'paved_road': 'Paved road / Asphalt',
            'carpet_road': 'Carpet road',
            'gravel_road': 'Gravel road',
            'sand_road': 'Sand road',
            'earth_road': 'Earth road'
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
        road_conditions_text += "\n⚠️ IMPORTANT: DO NOT allocate specific kilometers to each road type (e.g., NO '14.4km paved road').\n"
        road_conditions_text += "Instead, use road conditions in parentheses when mentioning actual roads from turn-by-turn directions.\n"
        road_conditions_text += "Example: 'proceed along A6 (paved road in excellent condition)'\n"

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

    prompt = f"""You are an expert at writing professional property valuation reports in Sri Lanka.
Convert the following route information into a natural, professional access description paragraph.

════════════════════════════════════════════════════════════════
SECTION A: NAVIGATION DETAILS (PRIMARY - MUST USE ALL)
════════════════════════════════════════════════════════════════

STARTING POINT: {starting_point_name}
TOTAL DISTANCE: {total_distance_km:.1f} km
TOTAL DURATION: {total_duration_mins} minutes
PROPERTY POSITION: {property_side} side of the road

SPECIFIC ROAD NAMES (MUST include in output):
{format_road_names(navigation_entities.get('road_names', []))}

LANDMARKS (MUST include when available):
{format_landmarks(navigation_entities.get('landmarks', []))}

TURN-BY-TURN NAVIGATION (MUST include turn directions):
{format_major_turns(navigation_entities.get('major_turns', []))}

════════════════════════════════════════════════════════════════
SECTION B: ROAD SURFACE CONDITIONS (SECONDARY - INTEGRATE NATURALLY)
════════════════════════════════════════════════════════════════

{road_conditions_text}

IMPORTANT: Add these in parentheses when mentioning roads, e.g.:
"proceed along A6 (paved road in excellent condition)"

════════════════════════════════════════════════════════════════
CRITICAL REQUIREMENTS (PRIORITIZED)
════════════════════════════════════════════════════════════════

PRIORITY 1 - Navigation Details:
✓ Include SPECIFIC road names from Section A (e.g., "A6", "Dambulla Road")
✓ Include turn instructions with LEFT/RIGHT directions
✓ Include landmarks naturally (e.g., "before the Railway crossing", "at Deshapriya Hotel")

PRIORITY 2 - Road Conditions Integration:
✓ Add road conditions in parentheses: "(paved road in excellent condition)"
✓ Do NOT let road conditions dominate the narrative
✓ Balance: 70% navigation details, 30% road conditions
✓ 🚨 CRITICAL - ANTI-HALLUCINATION RULES:
  - NEVER create distance breakdowns per road type (e.g., WRONG: "14.4km paved road, 13.0km carpet road")
  - NEVER allocate portions of total distance to specific road types
  - ALWAYS integrate road conditions into actual road names from turn-by-turn directions
  - Example CORRECT: "proceed along A6 (paved road in excellent condition) for 2km, turn onto Wellawa Road (carpet road in good condition)"
  - Example WRONG: "proceed 14.4 Kilometers on paved road, then 13 Kilometers on carpet road"
  - If you write "X km/Kilometers [road_type] road" you are HALLUCINATING - STOP

PRIORITY 3 - Professional Format:
✓ Start with "From {starting_point_name},"
✓ Use professional language: "proceed along", "turn left onto", "turn right onto"
✓ Use approximate distances: "about 2 Kilometers", "about 500 Meters"
✓ Combine small consecutive steps (< 200m) into larger logical segments
✓ End with property position: "to reach the property on the {property_side} side of the road fronting same"
✓ ONE flowing paragraph, 2-5 sentences
✓ NO special characters (¾, ½) - use decimals (0.75, 0.5)
✓ Title case for road names

════════════════════════════════════════════════════════════════
EXAMPLES - GOOD OUTPUT SHOWING INTEGRATION
════════════════════════════════════════════════════════════════

Example 1 - Urban route with landmarks and mixed road conditions:
"From Clock tower junction of Kurunegala town, proceed along Dambulla Road (paved road in excellent condition) for about 2 Kilometers, before the Railway crossing turn left onto Wellawa Road (carpet road in good condition) and proceed about 500 Meters, turn right onto Araliya Uyana Road, crossing the Railway and proceed about 75 Meters, turn right onto Rathu Araliya Mawatha and proceed about 50 Meters to reach the property on the right side of the road fronting same."

Example 2 - Simple route with landmark:
"From Puttalam junction of Kurunegala town, proceed along Negombo Road (paved road in excellent condition) for about 1.5 Kilometers, about 250 Meters after crossing Puwakgashandiya color light junction, turn left onto Wijayaba Mawatha and proceed about 50 Meters to reach the property on the right side of the road fronting same."

Example 3 - Highway route with landmark:
"From Deshapriya Hotel & Bakers 2, turn right onto Ambepussa - Kurunegala - Trincomalee Hwy/A6 (paved road in excellent condition) and proceed about 3 Kilometers, passing Miracle Health Hospital Medical Laboratory on the left, to reach the property on the right side of the road fronting same."

════════════════════════════════════════════════════════════════

Return ONLY the professional access description paragraph following these requirements."""

    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
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
    Validate that summary mode output doesn't contain hallucinated distance breakdowns.
    Returns True if valid, False if contains hallucination patterns.
    """
    if not road_conditions:
        return True

    # Check for patterns like "X km paved road" or "X Kilometers carpet road"
    road_type_map = {
        'paved_road': ['paved', 'asphalt'],
        'carpet_road': ['carpet'],
        'gravel_road': ['gravel'],
        'sand_road': ['sand'],
        'earth_road': ['earth']
    }

    import re
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


def clean_professional_text(text: str) -> str:
    """
    Remove non-English characters and fix formatting issues.
    Ensures professional text is suitable for valuation reports.
    """
    # Remove non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Replace special fraction characters with decimals
    text = text.replace('¾', '.75')
    text = text.replace('½', '.5')
    text = text.replace('¼', '.25')
    text = text.replace('⅓', '.33')
    text = text.replace('⅔', '.67')

    # Normalize whitespace
    text = ' '.join(text.split())

    return text.strip()
