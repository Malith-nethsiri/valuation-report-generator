"""
Text formatting utilities for access description generation.
"""

import re
from typing import Dict, Any, List


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
