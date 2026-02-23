"""
Navigation entity extraction from Google Maps directions.
"""

import re
from typing import Dict, Any, List, Optional


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
