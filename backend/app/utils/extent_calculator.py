"""
Land Extent Calculation Utilities for Sri Lankan Property Measurements
Handles conversions between Acres-Roods-Perches (A-R-P) and metric units
"""

from typing import Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

# Sri Lankan Land Measurement Constants
# Based on official Survey Department standards
PERCHES_PER_ROOD = 40
ROODS_PER_ACRE = 4
PERCHES_PER_ACRE = PERCHES_PER_ROOD * ROODS_PER_ACRE  # 160 perches = 1 acre

# Metric Conversions
SQUARE_METERS_PER_ACRE = 4046.86
HECTARES_PER_ACRE = 0.404686
SQUARE_METERS_PER_PERCH = 25.29
SQUARE_METERS_PER_ROOD = SQUARE_METERS_PER_PERCH * PERCHES_PER_ROOD  # 1011.71 sq m


def normalize_extent(acres: float = 0, roods: int = 0, perches: float = 0) -> Dict[str, float]:
    """
    Normalize land extent by converting excess perches to roods and excess roods to acres.

    Args:
        acres: Number of acres (can be decimal)
        roods: Number of roods (0-3 normally, but will normalize if > 3)
        perches: Number of perches (0-39.99 normally, but will normalize if >= 40)

    Returns:
        Dictionary with normalized acres, roods, and perches

    Example:
        normalize_extent(0, 5, 45.5) -> {"acres": 1, "roods": 1, "perches": 5.5}
        # Because 5 roods = 1 acre + 1 rood, and 45.5 perches = 1 rood + 5.5 perches
    """
    acres = float(acres) if acres else 0
    roods = int(roods) if roods else 0
    perches = float(perches) if perches else 0

    # Convert excess perches to roods
    if perches >= PERCHES_PER_ROOD:
        extra_roods = int(perches / PERCHES_PER_ROOD)
        roods += extra_roods
        perches = round(perches - (extra_roods * PERCHES_PER_ROOD), 2)

    # Convert excess roods to acres
    if roods >= ROODS_PER_ACRE:
        extra_acres = int(roods / ROODS_PER_ACRE)
        acres += extra_acres
        roods = roods - (extra_acres * ROODS_PER_ACRE)

    return {
        "acres": acres,
        "roods": roods,
        "perches": round(perches, 2)
    }


def calculate_total_perches(acres: float = 0, roods: int = 0, perches: float = 0) -> float:
    """
    Convert A-R-P to total perches for easier calculation.

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Total number of perches

    Example:
        calculate_total_perches(1, 2, 10) -> 250
        # 1 acre = 160 perches, 2 roods = 80 perches, + 10 perches = 250 total
    """
    acres = float(acres) if acres else 0
    roods = int(roods) if roods else 0
    perches = float(perches) if perches else 0

    total = (acres * PERCHES_PER_ACRE) + (roods * PERCHES_PER_ROOD) + perches
    return round(total, 2)


def perches_to_arp(total_perches: float) -> Dict[str, float]:
    """
    Convert total perches back to A-R-P format.

    Args:
        total_perches: Total number of perches

    Returns:
        Dictionary with acres, roods, and perches

    Example:
        perches_to_arp(250) -> {"acres": 1, "roods": 2, "perches": 10}
    """
    total_perches = float(total_perches)

    # Calculate acres
    acres = int(total_perches / PERCHES_PER_ACRE)
    remaining_perches = total_perches - (acres * PERCHES_PER_ACRE)

    # Calculate roods
    roods = int(remaining_perches / PERCHES_PER_ROOD)
    perches = round(remaining_perches - (roods * PERCHES_PER_ROOD), 2)

    return {
        "acres": acres,
        "roods": roods,
        "perches": perches
    }


def arp_to_hectares(acres: float = 0, roods: int = 0, perches: float = 0) -> float:
    """
    Convert A-R-P to hectares.

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Hectares (rounded to 4 decimal places)

    Example:
        arp_to_hectares(0, 0, 13.8) -> 0.0349
    """
    # Convert to total acres first
    total_acres = acres + (roods / ROODS_PER_ACRE) + (perches / PERCHES_PER_ACRE)
    hectares = total_acres * HECTARES_PER_ACRE
    return round(hectares, 4)


def arp_to_square_meters(acres: float = 0, roods: int = 0, perches: float = 0) -> float:
    """
    Convert A-R-P to square meters.

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Square meters (rounded to 2 decimal places)

    Example:
        arp_to_square_meters(0, 0, 13.8) -> 349.00
    """
    total_perches = calculate_total_perches(acres, roods, perches)
    square_meters = total_perches * SQUARE_METERS_PER_PERCH
    return round(square_meters, 2)


def hectares_to_arp(hectares: float) -> Dict[str, float]:
    """
    Convert hectares to A-R-P format.

    Args:
        hectares: Area in hectares

    Returns:
        Dictionary with acres, roods, and perches
    """
    total_acres = hectares / HECTARES_PER_ACRE
    total_perches = total_acres * PERCHES_PER_ACRE
    return perches_to_arp(total_perches)


def square_meters_to_arp(square_meters: float) -> Dict[str, float]:
    """
    Convert square meters to A-R-P format.

    Args:
        square_meters: Area in square meters

    Returns:
        Dictionary with acres, roods, and perches
    """
    total_perches = square_meters / SQUARE_METERS_PER_PERCH
    return perches_to_arp(total_perches)


def format_extent_string(acres: float = 0, roods: int = 0, perches: float = 0) -> str:
    """
    Format extent in standard Sri Lankan legal document format: "00A-0R-13.8P"

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Formatted string in "00A-0R-13.8P" format

    Example:
        format_extent_string(0, 0, 13.8) -> "00A-0R-13.8P"
        format_extent_string(2, 3, 15.5) -> "02A-3R-15.5P"
    """
    # Normalize first
    normalized = normalize_extent(acres, roods, perches)

    a = int(normalized["acres"])
    r = int(normalized["roods"])
    p = normalized["perches"]

    # Format: Always 2 digits for acres, 1 digit for roods, decimal for perches
    return f"{a:02d}A-{r}R-{p:.2f}P".rstrip('0').rstrip('.')+ ('P' if not str(p).endswith('P') else '')


def format_extent_string_cleaned(acres: float = 0, roods: int = 0, perches: float = 0) -> str:
    """
    Format extent in standard Sri Lankan legal document format with proper decimal handling.

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Formatted string in "00A-0R-13.8P" format

    Example:
        format_extent_string_cleaned(0, 0, 13.8) -> "00A-0R-13.8P"
        format_extent_string_cleaned(2, 3, 15.5) -> "02A-3R-15.5P"
        format_extent_string_cleaned(1, 2, 10.0) -> "01A-2R-10P"
    """
    # Normalize first
    normalized = normalize_extent(acres, roods, perches)

    a = int(normalized["acres"])
    r = int(normalized["roods"])
    p = normalized["perches"]

    # Format perches: show decimal only if not a whole number
    if p == int(p):
        perches_str = f"{int(p)}"
    else:
        perches_str = f"{p:.2f}".rstrip('0').rstrip('.')

    return f"{a:02d}A-{r}R-{perches_str}P"


def calculate_extent_data(acres: float = 0, roods: int = 0, perches: float = 0) -> Dict[str, any]:
    """
    Calculate all extent data from A-R-P input.
    This is the main function to use when processing form input.

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Dictionary with all calculated extent data:
        - land_extent_acres: Normalized acres
        - land_extent_roods: Normalized roods
        - land_extent_perches: Normalized perches
        - land_extent_hectares: Hectares (auto-calculated)
        - land_extent_square_meters: Square meters (auto-calculated)
        - land_extent_formatted: Formatted string (e.g., "00A-0R-13.8P")

    Example:
        calculate_extent_data(0, 0, 13.8) -> {
            "land_extent_acres": 0,
            "land_extent_roods": 0,
            "land_extent_perches": 13.8,
            "land_extent_hectares": 0.0349,
            "land_extent_square_meters": 349.00,
            "land_extent_formatted": "00A-0R-13.8P"
        }
    """
    # Normalize the input
    normalized = normalize_extent(acres, roods, perches)

    return {
        "land_extent_acres": normalized["acres"],
        "land_extent_roods": normalized["roods"],
        "land_extent_perches": normalized["perches"],
        "land_extent_hectares": arp_to_hectares(
            normalized["acres"],
            normalized["roods"],
            normalized["perches"]
        ),
        "land_extent_square_meters": arp_to_square_meters(
            normalized["acres"],
            normalized["roods"],
            normalized["perches"]
        ),
        "land_extent_formatted": format_extent_string_cleaned(
            normalized["acres"],
            normalized["roods"],
            normalized["perches"]
        )
    }


def parse_extent_string(extent_str: str) -> Dict[str, float]:
    """
    Parse a formatted extent string back to A-R-P values.

    Args:
        extent_str: Formatted extent string (e.g., "00A-0R-13.8P", "2A-3R-15.5P")

    Returns:
        Dictionary with acres, roods, and perches

    Example:
        parse_extent_string("00A-0R-13.8P") -> {"acres": 0, "roods": 0, "perches": 13.8}
        parse_extent_string("2A-3R-15.5P") -> {"acres": 2, "roods": 3, "perches": 15.5}
    """
    try:
        # Remove spaces and convert to uppercase
        extent_str = extent_str.strip().upper()

        # Split by '-' to get each component
        parts = extent_str.split('-')

        if len(parts) != 3:
            raise ValueError("Invalid extent format. Expected format: 00A-0R-13.8P")

        # Extract values
        acres = float(parts[0].replace('A', ''))
        roods = int(parts[1].replace('R', ''))
        perches = float(parts[2].replace('P', ''))

        return {
            "acres": acres,
            "roods": roods,
            "perches": perches
        }
    except Exception as e:
        raise ValueError(f"Failed to parse extent string '{extent_str}': {str(e)}")


# Validation Functions

def validate_extent_values(acres: float = 0, roods: int = 0, perches: float = 0) -> Tuple[bool, Optional[str]]:
    """
    Validate extent values.

    Args:
        acres: Number of acres
        roods: Number of roods
        perches: Number of perches

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        validate_extent_values(0, 0, 13.8) -> (True, None)
        validate_extent_values(0, 5, 0) -> (True, None)  # Will be normalized
        validate_extent_values(-1, 0, 0) -> (False, "Acres cannot be negative")
    """
    try:
        acres = float(acres) if acres else 0
        roods = int(roods) if roods else 0
        perches = float(perches) if perches else 0

        if acres < 0:
            return False, "Acres cannot be negative"

        if roods < 0:
            return False, "Roods cannot be negative"

        if perches < 0:
            return False, "Perches cannot be negative"

        # Check if total extent is zero (might be intentional, so just warn)
        total = calculate_total_perches(acres, roods, perches)
        if total == 0:
            return True, None  # Valid but zero extent

        # Check for unusually large values (> 1000 acres might be a data entry error)
        normalized = normalize_extent(acres, roods, perches)
        if normalized["acres"] > 1000:
            return True, None  # Valid but large - frontend can show warning

        return True, None

    except Exception as e:
        return False, f"Invalid extent values: {str(e)}"
