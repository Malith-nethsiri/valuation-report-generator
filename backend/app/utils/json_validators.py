"""
JSON Schema validators for complex JSON fields in the database.

Provides schema validation for:
- Boundaries (4 main directions required + 4 diagonal directions optional)
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
        },
        "northeast": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        },
        "southeast": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        },
        "southwest": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "length": {"type": ["string", "null"]},
                "adjoins": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["description"]
        },
        "northwest": {
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
        "id": {"type": "string"},
        "image_data": {"type": "string"},
        "caption": {"type": ["string", "null"]},
        "order": {"type": "integer", "minimum": 0}
    },
    "required": ["id", "image_data", "order"]
}

# New format schemas
FLOOR_SCHEMA = {
    "type": "object",
    "properties": {
        "floor_name": {"type": "string"},
        "floor_area": {"type": ["number", "null"], "minimum": 0}
    },
    "required": ["floor_name"]
}

ROOM_SCHEMA = {
    "type": "object",
    "properties": {
        "room_type": {"type": "string"},
        "count": {"type": ["integer", "null"], "minimum": 0},
        "has_attached_bathroom": {"type": ["boolean", "null"]}
    }
}

ACCOMMODATION_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "bedrooms": {"type": ["integer", "null"], "minimum": 0},
        "bathrooms": {"type": ["integer", "null"], "minimum": 0},
        "living_rooms": {"type": ["integer", "null"], "minimum": 0},
        "dining_rooms": {"type": ["integer", "null"], "minimum": 0},
        "kitchens": {"type": ["integer", "null"], "minimum": 0},
        "pantries": {"type": ["integer", "null"], "minimum": 0},
        "verandahs": {"type": ["integer", "null"], "minimum": 0},
        "balconies": {"type": ["integer", "null"], "minimum": 0},
        "garages": {"type": ["integer", "null"], "minimum": 0},
        "store_rooms": {"type": ["integer", "null"], "minimum": 0},
        "other_rooms": {"type": ["integer", "null"], "minimum": 0}
    }
}

BUILDING_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "building_name": {"type": ["string", "null"]},
        "building_type": {"type": "string"},
        "stories": {"type": ["integer", "null"], "minimum": 1},
        "building_age": {"type": ["integer", "null"], "minimum": 0, "maximum": 200},
        "condition": {"type": ["string", "null"]},
        "occupier_name": {"type": ["string", "null"], "maxLength": 300},
        "occupier_relationship": {
            "type": ["string", "null"],
            "enum": [None, "", "owner", "tenant", "caretaker", "family_member", "vacant"]
        },
        "roof_types": {"type": ["array", "null"], "items": {"type": "string"}},
        "roof_description": {"type": ["string", "null"]},
        "wall_types": {"type": ["array", "null"], "items": {"type": "string"}},
        "wall_description": {"type": ["string", "null"]},
        "floor_types": {"type": ["array", "null"], "items": {"type": "string"}},
        "floor_description": {"type": ["string", "null"]},
        "total_floor_area": {"type": ["number", "null"], "minimum": 0},
        "floors": {"type": ["array", "null"], "items": FLOOR_SCHEMA},
        "rooms": {"type": ["array", "null"], "items": ROOM_SCHEMA},
        "accommodation_summary": {"anyOf": [ACCOMMODATION_SUMMARY_SCHEMA, {"type": "null"}]},
        "construction_materials": {"type": ["object", "null"]},
        "utilities_services": {"type": ["object", "null"]},
        "conveniences": {"type": ["array", "null"], "items": {"type": "string"}},
        "building_description_text": {"type": ["string", "null"]},
        "building_photos": {
            "type": ["array", "null"],
            "items": BUILDING_PHOTO_SCHEMA,
            "maxItems": 5
        },
        "additional_structures_description": {"type": ["string", "null"]},

        # Legacy fields (keep for backward compatibility)
        "plinth_area": {"type": ["number", "null"]},
        "floor_area": {"type": ["number", "null"]},
        "num_floors": {"type": ["integer", "null"]},
        "num_bedrooms": {"type": ["integer", "null"]},
        "num_bathrooms": {"type": ["integer", "null"]},
        "amenities": {"type": ["array", "null"], "items": {"type": "string"}},
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
