from ast import Dict
import json
import logging
from typing import Any, Optional, Sequence, cast, TypeVar, Union


logger = logging.getLogger(__name__)

T = TypeVar('T')

# ===== NUMERIC TYPE CONVERTER =====
def to_float(value: Any) -> float:
    """
    Safely convert numeric-like types to float, defaulting to 0.0 on failure.
    """
    if value is None:
        return 0.0

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# ===== DEFENSIVE DATA ACCESS HELPERS =====
# These functions prevent crashes from None/missing data in report generation

def safe_get_json_field(obj: Any, field_name: str, default: T) -> T:
    """
    Safely get JSON field from model object with None check.

    Args:
        obj: SQLAlchemy model object
        field_name: Name of the field to retrieve
        default: Default value if field is None or doesn't exist

    Returns:
        Field value or default
    """
    try:
        value = getattr(obj, field_name, default)
        return value if value is not None else default
    except Exception as e:
        logger.warning(f"Error accessing field '{field_name}': {e}")
        return default



def safe_get_array_item(arr: Optional[Sequence[T]], index: int, default: Any = None) -> Union[T, Any]:
    """
    Safely get array item with bounds checking.

    Args:
        arr: Array/list to access
        index: Index to retrieve
        default: Default value if index out of bounds or arr is None

    Returns:
        Array item or default
    """

    if not arr or not isinstance(arr, (list, tuple)):
        return default
    if 0 <= index < len(arr):
        item = arr[index]
        return item if item is not None else default
    return default


def safe_parse_json_string(json_str: Any, default: Any = None) -> Any:
    """
    Safely parse JSON string with error handling.

    Args:
        json_str: JSON string or already-parsed object
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default
    """
    if not json_str:
        return default
    try:
        return json.loads(json_str) if isinstance(json_str, str) else json_str
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON parse error: {e}")
        return default


def safe_get_nested(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely traverse nested dict/object structure.

    Args:
        obj: Object to traverse
        *keys: Keys to traverse (can be dict keys or object attributes)
        default: Default value if any key is missing or None

    Returns:
        Nested value or default

    Example:
        safe_get_nested(report, 'boundaries', 'north', 'description', default='')
    """
    current: Optional[Any] = obj
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = cast(Dict, current).get(key)
        else:
            current = getattr(current, key, None)
        if current is None:
            return default
    return current
