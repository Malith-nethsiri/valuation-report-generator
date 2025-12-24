"""
AI-powered transformer for converting Google Maps directions to professional valuation report format.
Uses Claude AI to generate natural, professional access descriptions.
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
import re

# MAJOR landmarks to KEEP (for turn reference):
MAJOR_LANDMARK_KEYWORDS = {
    'junction', 'roundabout', 'intersection',
    'railway crossing', 'railway station', 'bridge',
    'town', 'city'
}

# MINOR landmarks to REMOVE:
MINOR_LANDMARK_KEYWORDS = {
    'salon', 'shop', 'store', 'bakery', 'restaurant',
    'hotel', 'building', 'house', 'on the', 'near'
}


def filter_landmarks(landmarks: List[str]) -> List[str]:
    """
    Filter landmarks to keep only major ones (junctions, towns, railway crossings).
    Remove minor landmarks (shops, salons, small businesses).

    Args:
        landmarks: List of extracted landmark strings

    Returns:
        List of filtered major landmarks only
    """
    filtered = []
    for landmark in landmarks:
        landmark_lower = landmark.lower()

        # Check if contains minor keywords - skip these
        if any(keyword in landmark_lower for keyword in MINOR_LANDMARK_KEYWORDS):
            # Special case: "Hotel" can be major if part of a junction/town name
            if 'junction' not in landmark_lower and 'town' not in landmark_lower:
                continue

        # Check if contains major keywords - keep these
        if any(keyword in landmark_lower for keyword in MAJOR_LANDMARK_KEYWORDS):
            filtered.append(landmark)
            continue

        # Check if proper noun (capitalized multi-word like "Digampathana")
        # AND not too long (< 4 words usually means it's a place name, not a business)
        words = landmark.split()
        if landmark and landmark[0].isupper() and 1 <= len(words) <= 3:
            filtered.append(landmark)

    return filtered


def detect_road_class_from_name(road_name: str) -> Optional[Dict[str, str]]:
    """
    Detect Sri Lankan road class from road name (for backend analytics only).
    Returns: {"class": "A", "number": "6", "confidence": "high"} or None

    NOTE: This is for backend analytics only - NOT shown in output text.
    """
    if not road_name:
        return None

    patterns = [
        (r'\bA(\d+)\b', 'A'),           # A6, A1, A12
        (r'\bB(\d+)\b', 'B'),           # B425, B28
        (r'\bE0?(\d+)\b', 'E'),         # E01, E3 (Expressways)
        (r'\bClass\s+A\b', 'A'),        # "Class A Road"
        (r'\bClass\s+B\b', 'B'),
        (r'\bClass\s+C\b', 'C'),
        (r'\bClass\s+D\b', 'D'),
    ]

    for pattern, road_class in patterns:
        match = re.search(pattern, road_name, re.IGNORECASE)
        if match:
            result = {
                "class": road_class,
                "confidence": "high"
            }
            if match.groups():
                result["number"] = match.group(1)
            return result

    return None  # Assume "Local" if can't detect


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
    Validate that summary mode output doesn't contain hallucinated distance breakdowns
    or road classification mentions (Class A, B, C).
    Returns True if valid, False if contains hallucination patterns.
    """
    import re

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
