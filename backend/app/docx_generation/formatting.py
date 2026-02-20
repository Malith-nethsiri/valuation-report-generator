from typing import Dict, List, Optional

def format_material_list(materials: List[str], labels_dict: Dict[str, str]) -> str:
    """
    Format a list of materials intelligently with proper grammar (Oxford comma).

    Args:
        materials: List of material keys (e.g., ['asbestos', 'tile', 'metal'])
        labels_dict: Dictionary mapping keys to display labels

    Returns:
        Formatted string with proper grammar

    Examples:
        - 1 item: "asbestos sheets"
        - 2 items: "asbestos sheets and tiles"
        - 3+ items: "asbestos sheets, tiles and metal sheets" (Oxford comma)
    """
    if not materials:
        return ""

    # Get display labels for all materials
    labeled_materials = [labels_dict.get(m, m) for m in materials]

    if len(labeled_materials) == 1:
        return labeled_materials[0]
    elif len(labeled_materials) == 2:
        return f"{labeled_materials[0]} and {labeled_materials[1]}"
    else:
        # Oxford comma format: "A, B, C and D"
        return ", ".join(labeled_materials[:-1]) + f" and {labeled_materials[-1]}"




def format_currency(value: Optional[float]) -> str:
    """
    Format currency with thousand separators and 2 decimal places.

    Args:
        value: Numeric value to format

    Returns:
        Formatted string like "Rs. 10,000,000.00"
    """
    if value is None:
        return "N/A"
    return f"Rs. {value:,.2f}"


def format_currency_words(value: Optional[float]) -> str:
    """
    Convert numeric currency to words in Sri Lankan English format.

    Args:
        value: Numeric value (e.g., 122300000.00)

    Returns:
        String like "One Hundred Twenty Two Million Three Hundred Thousand"

    Examples:
        >>> format_currency_words(122300000.00)
        'One Hundred Twenty Two Million Three Hundred Thousand'
        >>> format_currency_words(50000.00)
        'Fifty Thousand'
        >>> format_currency_words(1500000.00)
        'One Million Five Hundred Thousand'
    """
    if value is None or value == 0:
        return "Zero"

    # Round to nearest whole number (ignore cents)
    value = int(round(abs(value)))

    if value == 0:
        return "Zero"

    # Number words
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
             "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def convert_group(n: int) -> str:
        """Convert a number group (1-999) to words"""
        if n == 0:
            return ""
        elif n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
        else:
            return ones[n // 100] + " Hundred" + (" " + convert_group(n % 100) if n % 100 != 0 else "")

    # Split into groups
    billion = value // 1000000000
    million = (value % 1000000000) // 1000000
    thousand = (value % 1000000) // 1000
    hundred = value % 1000

    parts: list[str] = []
    if billion > 0:
        parts.append(convert_group(billion) + " Billion")
    if million > 0:
        parts.append(convert_group(million) + " Million")
    if thousand > 0:
        parts.append(convert_group(thousand) + " Thousand")
    if hundred > 0:
        parts.append(convert_group(hundred))

    return " ".join(parts)


def format_currency_aligned(value: Optional[float], min_width: int = 13) -> str:
    """
    Format currency with right-padding for digit alignment at tab stops.

    When used with right-aligned tab stops, this ensures that currency values
    align properly by padding the numeric portion to a consistent width.

    Args:
        value: Numeric value to format
        min_width: Minimum width for the numeric portion (default 13)

    Returns:
        Formatted string like "Rs.   50,000.00" or "Rs. 12,750,000.00"

    Examples:
        format_currency_aligned(50000) -> "Rs.   50,000.00"
        format_currency_aligned(12750000) -> "Rs. 12,750,000.00"
    """
    if value is None:
        return "N/A"

    formatted_number = f"{value:,.2f}"
    # Pad to minimum width, but allow larger numbers to exceed it
    actual_width = max(min_width, len(formatted_number))
    padded_number = formatted_number.rjust(actual_width)

    return f"Rs. {padded_number}"


def format_room_count(count: int, singular: str, plural: str| None = None) -> str:
    """
    Format room count with conditional number word display.

    Rules:
    - count == 1: Return singular form only (e.g., "bedroom")
    - count >= 2: Return number word + plural form (e.g., "two bedrooms")

    Args:
        count: Number of rooms
        singular: Singular form of room name (e.g., "bedroom")
        plural: Plural form (optional, defaults to singular + 's')

    Returns:
        Formatted string

    Examples:
        format_room_count(1, "bedroom") -> "bedroom"
        format_room_count(2, "bedroom") -> "two bedrooms"
        format_room_count(3, "pantry", "pantries") -> "three pantries"
    """
    if plural is None:
        plural = f"{singular}s"

    if count == 1:
        return singular
    else:
        number_words = {
            2: 'two', 3: 'three', 4: 'four', 5: 'five',
            6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'
        }
        number_word = number_words.get(count, str(count))
        return f"{number_word} {plural}"


def round_for_say(value: float) -> float:
    """
    Round value for 'Say' convention in professional valuations.

    Professional valuations often round the final value to a reasonable amount:
    - 10M+: Round to nearest 100K
    - 1M - 10M: Round to nearest 50K
    - 100K - 1M: Round to nearest 10K
    - Below 100K: Round to nearest 1K

    Args:
        value: Value to round

    Returns:
        Rounded value
    """
    if value >= 10_000_000:  # 10M+
        return round(value / 100_000) * 100_000  # Round to nearest 100K
    elif value >= 1_000_000:  # 1M - 10M
        return round(value / 50_000) * 50_000  # Round to nearest 50K
    elif value >= 100_000:  # 100K - 1M
        return round(value / 10_000) * 10_000  # Round to nearest 10K
    else:
        return round(value / 1_000) * 1_000  # Round to nearest 1K

