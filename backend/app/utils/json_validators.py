"""
JSON Schema validators for complex JSON fields in the database.

Provides schema validation for:
- Boundaries (north, south, east, west with descriptions)
- Buildings (array of building objects with photos)
- Comparable properties (property comparison data)

Benefits:
- Data structure consistency
- Early error detection
- Clear validation error messages
"""

from typing import Any, Dict, Optional
from jsonschema import validate, ValidationError as JSONSchemaValidationError
from pydantic import ValidationError

# ===== BOUNDARIES SCHEMA =====

BOUNDARIES_SCHEMA = {
    "type": "object",
    "properties": {
        "north": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        },
        "south": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        },
        "east": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        },
        "west": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        }
    },
    "required": ["north", "south", "east", "west"]
}

# ===== BUILDINGS SCHEMA =====

BUILDING_PHOTO_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string"},
        "caption": {"type": ["string", "null"]},
        "filename": {"type": ["string", "null"]},
        "uploaded_at": {"type": ["string", "null"]}
    },
    "required": ["url"]
}

BUILDING_SCHEMA = {
    "type": "object",
    "properties": {
        "building_type": {"type": "string"},
        "building_name": {"type": ["string", "null"]},
        "building_purpose": {"type": ["string", "null"]},
        "plinth_area": {"type": ["number", "null"]},
        "plinth_area_unit": {"type": ["string", "null"]},
        "floor_area": {"type": ["number", "null"]},
        "floor_area_unit": {"type": ["string", "null"]},
        "num_floors": {"type": ["integer", "null"]},
        "construction_year": {"type": ["integer", "string", "null"]},
        "building_age_years": {"type": ["integer", "null"]},
        "building_condition": {"type": ["string", "null"]},
        "construction_quality": {"type": ["string", "null"]},
        "roof_type": {"type": ["string", "null"]},
        "wall_type": {"type": ["string", "null"]},
        "floor_type": {"type": ["string", "null"]},
        "foundation_type": {"type": ["string", "null"]},
        "num_bedrooms": {"type": ["integer", "null"]},
        "num_bathrooms": {"type": ["integer", "null"]},
        "num_living_rooms": {"type": ["integer", "null"]},
        "num_kitchens": {"type": ["integer", "null"]},
        "has_attached_bathroom": {"type": ["boolean", "null"]},
        "amenities": {
            "type": ["array", "null"],
            "items": {"type": "string"}
        },
        "description_text": {"type": ["string", "null"]},
        "photos": {
            "type": ["array", "null"],
            "items": BUILDING_PHOTO_SCHEMA,
            "maxItems": 20  # Limit to 20 photos per building
        }
    },
    "required": ["building_type"]
}

BUILDINGS_SCHEMA = {
    "type": "array",
    "items": BUILDING_SCHEMA,
    "maxItems": 10  # Limit to 10 buildings per property
}

# ===== COMPARABLE PROPERTIES SCHEMA =====

COMPARABLE_PROPERTY_SCHEMA = {
    "type": "object",
    "properties": {
        "property_address": {"type": "string"},
        "property_type": {"type": ["string", "null"]},
        "land_extent_acres": {"type": ["number", "null"], "minimum": 0},
        "sale_price": {"type": ["number", "null"], "minimum": 0},
        "sale_date": {"type": ["string", "null"]},
        "sale_year": {"type": ["integer", "null"]},
        "price_per_perch": {"type": ["number", "null"]},
        "distance_km": {"type": ["number", "null"], "minimum": 0},
        "location": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "source": {"type": ["string", "null"]},
        "adjustments": {"type": ["string", "null"]}
    },
    "required": ["property_address"]
}

COMPARABLE_PROPERTIES_SCHEMA = {
    "type": "array",
    "items": COMPARABLE_PROPERTY_SCHEMA,
    "maxItems": 10  # Limit to 10 comparable properties
}

# ===== VALIDATION FUNCTIONS =====

def validate_boundaries(boundaries: Any) -> tuple[bool, Optional[str]]:
    """
    Validate boundaries JSON structure.

    Args:
        boundaries: Boundaries data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if boundaries is None:
        return True, None

    try:
        validate(instance=boundaries, schema=BOUNDARIES_SCHEMA)
        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid boundaries structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


def validate_buildings(buildings: Any) -> tuple[bool, Optional[str]]:
    """
    Validate buildings JSON structure.

    Args:
        buildings: Buildings array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if buildings is None:
        return True, None

    try:
        validate(instance=buildings, schema=BUILDINGS_SCHEMA)

        # Additional validation: check photo limits
        for i, building in enumerate(buildings):
            photos = building.get('photos', [])
            if photos and len(photos) > 20:
                return False, f"Building {i+1} has {len(photos)} photos (max 20 allowed)"

        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid buildings structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


def validate_comparable_properties(comparable_properties: Any) -> tuple[bool, Optional[str]]:
    """
    Validate comparable properties JSON structure.

    Args:
        comparable_properties: Comparable properties array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if comparable_properties is None:
        return True, None

    try:
        validate(instance=comparable_properties, schema=COMPARABLE_PROPERTIES_SCHEMA)
        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid comparable properties structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


# ===== HELPER: VALIDATE ANY JSON FIELD =====

def validate_json_field(field_name: str, data: Any) -> tuple[bool, Optional[str]]:
    """
    Route validation to appropriate schema based on field name.

    Args:
        field_name: Name of the JSON field
        data: Data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validators = {
        'boundaries': validate_boundaries,
        'buildings': validate_buildings,
        'comparable_properties': validate_comparable_properties,
    }

    validator = validators.get(field_name)
    if not validator:
        # No validator for this field, consider it valid
        return True, None

    return validator(data)


# ===== EXPORT ALL =====

__all__ = [
    'BOUNDARIES_SCHEMA',
    'BUILDINGS_SCHEMA',
    'COMPARABLE_PROPERTIES_SCHEMA',
    'validate_boundaries',
    'validate_buildings',
    'validate_comparable_properties',
    'validate_json_field',
]
