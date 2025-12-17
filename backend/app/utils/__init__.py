"""
Utility functions and helpers for the property valuation system
"""

from .extent_calculator import (
    calculate_extent_data,
    normalize_extent,
    format_extent_string_cleaned,
    parse_extent_string,
    arp_to_hectares,
    arp_to_square_meters,
    validate_extent_values
)

from .text_helpers import (
    append_label_if_missing,
    clean_spelling_errors,
    format_no_field,
    validate_administrative_division
)

__all__ = [
    "calculate_extent_data",
    "normalize_extent",
    "format_extent_string_cleaned",
    "parse_extent_string",
    "arp_to_hectares",
    "arp_to_square_meters",
    "validate_extent_values",
    "append_label_if_missing",
    "clean_spelling_errors",
    "format_no_field",
    "validate_administrative_division"
]
