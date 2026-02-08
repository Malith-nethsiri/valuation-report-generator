"""Shared constants and helpers for narrative generation services."""
from typing import List, Optional, Union
from ..docx_generator import format_list_with_grammar

WATER_SUPPLY_LABELS = {
    # Core display values (from frontend selects)
    "Pipe-borne (NWSDB)": "pipe-borne water (NWSDB)",
    "Well": "well water",
    "Bore/Tube Well": "bore/tube well water",
    "Rainwater Harvesting": "rainwater harvesting",
    # Building legacy snake_case keys
    "pipe_borne": "pipe-borne water (NWSDB)",
    "well": "well water",
    "tube_well": "tube well",
    # Locality legacy snake_case keys
    "pipe_borne_water": "pipe-borne water",
    "bore_water": "bore water",
    "well_water": "well water",
}


def format_water_supply(water_supply: Optional[Union[str, List[str]]]) -> Optional[str]:
    """Format water supply value(s) to readable text. Handles both string and list inputs."""
    if not water_supply:
        return None
    if isinstance(water_supply, str):
        return WATER_SUPPLY_LABELS.get(water_supply, water_supply)
    if isinstance(water_supply, list):
        mapped = [WATER_SUPPLY_LABELS.get(ws, ws.lower()) for ws in water_supply]
        return format_list_with_grammar(mapped)
    return None
