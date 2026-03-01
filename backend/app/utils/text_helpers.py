"""
Text Helper Utilities for Sri Lankan Valuation Report Generation
Handles intelligent label appending, spelling corrections, and formatting
"""

from typing import Optional, List
import re


def format_list_with_grammar(items: List[str]) -> str:
    """
    Format a list of items with proper Oxford comma grammar.

    Examples:
        ['item1'] -> 'item1'
        ['item1', 'item2'] -> 'item1 and item2'
        ['item1', 'item2', 'item3'] -> 'item1, item2, and item3'
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return ", ".join(items[:-1]) + f", and {items[-1]}"


# Common spelling corrections for Sri Lankan administrative divisions
SPELLING_CORRECTIONS = {
    # Secretariat variations
    r'\bsecratary\b': 'Secretariat',
    r'\bsecratariat\b': 'Secretariat',
    r'\bsecreatry\b': 'Secretariat',
    r'\bsecretry\b': 'Secretariat',

    # Pradeshiya Sabha variations
    r'\bpradeshiya saba\b': 'Pradeshiya Sabha',
    r'\bpradesiya sabha\b': 'Pradeshiya Sabha',

    # Grama Niladari variations
    r'\bgrama niladhari\b': 'Grama Niladari',
    r'\bgrama niladhri\b': 'Grama Niladari',

    # Common capitalization fixes
    r'\bnotary public\b': 'Notary Public',
    r'\bpublic notary\b': 'Public Notary',
}


def clean_spelling_errors(text: Optional[str]) -> str:
    """
    Fix common spelling errors in Sri Lankan administrative division names.

    This function applies case-insensitive corrections to common misspellings
    found in database entries, ensuring professional output in reports.

    Args:
        text: The text potentially containing spelling errors

    Returns:
        Cleaned text with errors fixed, or empty string if input is None/empty

    Examples:
        clean_spelling_errors("Kegalle Secratary") -> "Kegalle Secretariat"
        clean_spelling_errors("Divisional Secratariat") -> "Divisional Secretariat"
        clean_spelling_errors("notary public") -> "Notary Public"
        clean_spelling_errors(None) -> ""
        clean_spelling_errors("") -> ""

    Note:
        Uses word boundaries to avoid partial word replacements.
        Corrections are case-insensitive but output uses defined casing.
    """
    if not text or not text.strip():
        return ""

    cleaned_text = text.strip()

    # Apply each spelling correction with case-insensitive matching
    for pattern, replacement in SPELLING_CORRECTIONS.items():
        cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)

    return cleaned_text


def append_label_if_missing(
    value: Optional[str],
    label: str,
    variants: Optional[List[str]] = None,
    separator: str = " "
) -> str:
    """
    Intelligently append a label to a value only if the value doesn't already contain it.

    This prevents duplicate labels like "Beligal Korale Korale" or "Colombo District District"
    by checking if the label or any of its variants already exist in the value.

    Args:
        value: The base value (e.g., "Beligal" or "Beligal Korale")
        label: The label to append (e.g., "Korale", "District")
        variants: Alternative forms to check (e.g., ["korale", "GN Division"])
        separator: String to use between value and label (default: " ")

    Returns:
        String with label appended if needed, or original if already present.
        Returns empty string if value is None or empty.

    Examples:
        append_label_if_missing("Beligal", "Korale") -> "Beligal Korale"
        append_label_if_missing("Beligal Korale", "Korale") -> "Beligal Korale"
        append_label_if_missing("beligal korale", "Korale") -> "beligal korale"
        append_label_if_missing("Kaduwela GN Division", "Grama Niladari division",
            variants=["GN Division"]) -> "Kaduwela GN Division"
        append_label_if_missing(None, "Korale") -> ""
        append_label_if_missing("", "District") -> ""
        append_label_if_missing("  ", "Province") -> ""

    Note:
        - Uses case-insensitive matching with word boundaries to avoid false positives
        - Preserves original casing when label already exists
        - Checks main label and all variants before deciding to append
    """
    # Handle None, empty, or whitespace-only values
    if not value or not value.strip():
        return ""

    # Strip whitespace from value
    value = value.strip()

    # Build list of patterns to check (label + variants)
    patterns_to_check = [label]
    if variants:
        patterns_to_check.extend(variants)

    # Check each pattern case-insensitively with word boundaries
    for pattern in patterns_to_check:
        # Escape special regex characters in the pattern
        escaped_pattern = re.escape(pattern)
        # Use word boundaries to match whole words only
        regex_pattern = r'\b' + escaped_pattern + r'\b'

        # If pattern found (case-insensitive), return original value
        if re.search(regex_pattern, value, flags=re.IGNORECASE):
            return value

    # No match found - append the label
    return f"{value}{separator}{label}"


def format_no_field(label: str, number: Optional[str], include_label: bool = True) -> str:
    """
    Format a number field with consistent "No: " spacing.

    Standardizes formatting of fields like Assessment No, Plan No, Deed No, etc.
    throughout the valuation report system.

    Args:
        label: The field label (e.g., "Assessment", "Plan", "Deed")
        number: The number value
        include_label: Whether to include the label (default: True)

    Returns:
        Formatted string like "Assessment No: 123" or "No: 123" (if include_label=False).
        Returns empty string if number is None or empty.

    Examples:
        format_no_field("Assessment", "123") -> "Assessment No: 123"
        format_no_field("Plan", "1035") -> "Plan No: 1035"
        format_no_field("", "123", include_label=False) -> "No: 123"
        format_no_field("Deed", "456", include_label=False) -> "No: 456"
        format_no_field("Assessment", None) -> ""
        format_no_field("Plan", "") -> ""
        format_no_field("Deed", "  ") -> ""
        format_no_field("Assessment", "  123  ") -> "Assessment No: 123"

    Note:
        - Always includes space after colon: "No: " not "No:"
        - Strips whitespace from number
        - Returns empty string for None/empty/whitespace-only numbers
    """
    # Handle None, empty, or whitespace-only numbers
    if not number or not str(number).strip():
        return ""

    # Strip whitespace from number
    number = str(number).strip()

    # Format with or without label
    if include_label and label:
        return f"{label} No: {number}"
    else:
        return f"No: {number}"


def validate_administrative_division(value: Optional[str], division_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate an administrative division value for common issues.

    This function can be used to warn users about potential data quality issues
    without blocking data entry.

    Args:
        value: The administrative division value to validate
        division_type: Type of division (e.g., "District", "Korale", "Province")

    Returns:
        Tuple of (is_valid, warning_message)
        is_valid is always True (non-blocking), warning_message if issues detected

    Examples:
        validate_administrative_division("Colombo District District", "District")
            -> (True, "Warning: 'District' appears multiple times")
        validate_administrative_division("Colombo", "District") -> (True, None)
        validate_administrative_division(None, "District") -> (True, None)
    """
    if not value or not value.strip():
        return True, None

    # Check for duplicate occurrences of the division type
    escaped_type = re.escape(division_type)
    pattern = r'\b' + escaped_type + r'\b'
    matches = re.findall(pattern, value, flags=re.IGNORECASE)

    if len(matches) > 1:
        return True, f"Warning: '{division_type}' appears multiple times in '{value}'"

    return True, None
