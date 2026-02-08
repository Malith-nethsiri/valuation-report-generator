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
        'deeds': validate_deeds,
        'nearby_facilities': validate_nearby_facilities,
        'property_photos': validate_property_photos,
        'access_road_conditions': validate_access_road_conditions,
    }

    validator = validators.get(field_name)
    if not validator:
        # No validator for this field, consider it valid
        return True, None

    return validator(data)


# ===== DEEDS SCHEMA =====

DEED_SCHEMA = {
    "type": "object",
    "properties": {
        "deed_type": {"type": "string", "maxLength": 100},
        "deed_number": {"type": "string", "minLength": 1, "maxLength": 100},
        "deed_date": {"type": "string", "pattern": "^\\d{2}-\\d{2}-\\d{4}$"},  # DD-MM-YYYY
        "notary_name": {"type": ["string", "null"], "maxLength": 255},
        "notary_location": {"type": ["string", "null"], "maxLength": 255}
    },
    "required": ["deed_type", "deed_number", "deed_date"]
}

DEEDS_SCHEMA = {
    "type": "array",
    "items": DEED_SCHEMA,
    "maxItems": 10  # Limit to 10 deeds per property
}


# ===== NEARBY FACILITIES SCHEMA =====

NEARBY_FACILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "hospital", "school", "bank", "supermarket", "police",
                "bus_stand", "railway", "post_office", "petrol_station",
                "place_of_worship", "atm", "pharmacy", "market",
                "bus_station", "train_station", "gas_station", "lodging", "shopping"
            ]
        },
        "name": {"type": "string", "minLength": 1, "maxLength": 255},
        "distance_km": {"type": "number", "minimum": 0, "maximum": 100},
        "latitude": {"type": ["number", "null"], "minimum": -90, "maximum": 90},
        "longitude": {"type": ["number", "null"], "minimum": -180, "maximum": 180},
        "selected": {"type": "boolean"}
    },
    "required": ["type", "name", "distance_km"]
}

NEARBY_FACILITIES_SCHEMA = {
    "type": "array",
    "items": NEARBY_FACILITY_SCHEMA,
    "maxItems": 50  # Reasonable limit
}


# ===== PROPERTY PHOTOS SCHEMA =====

PROPERTY_PHOTO_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "maxLength": 50},
        "image_data": {"type": "string"},  # Base64 encoded
        "caption": {"type": ["string", "null"], "maxLength": 255},
        "order": {"type": "integer", "minimum": 0}
    },
    "required": ["id", "image_data", "order"]
}

PROPERTY_PHOTOS_SCHEMA = {
    "type": "array",
    "items": PROPERTY_PHOTO_SCHEMA,
    "maxItems": 20  # Limit to 20 photos per property
}


# ===== ACCESS ROAD CONDITIONS SCHEMA =====

ACCESS_ROAD_CONDITION_SCHEMA = {
    "type": "object",
    "properties": {
        "road_type": {
            "type": "string",
            "enum": [
                "paved_road", "concrete_road", "carpet_road", "gravel_road",
                "sand_road", "earth_road", "bitumen", "macadam"
            ]
        },
        "condition": {
            "type": ["string", "null"],
            "enum": [None, "excellent", "good", "fair", "poor", "very_poor"]
        },
        "distance_km": {"type": ["number", "null"], "minimum": 0},
        "notes": {"type": ["string", "null"], "maxLength": 500}
    },
    "required": ["road_type"]
}

ACCESS_ROAD_CONDITIONS_SCHEMA = {
    "type": "array",
    "items": ACCESS_ROAD_CONDITION_SCHEMA,
    "maxItems": 10
}


# ===== NEW VALIDATION FUNCTIONS =====

def validate_deeds(deeds: Any) -> tuple[bool, Optional[str]]:
    """
    Validate deeds JSON structure.

    Args:
        deeds: Deeds array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if deeds is None:
        return True, None

    try:
        validate(instance=deeds, schema=DEEDS_SCHEMA)
        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid deeds structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


def validate_nearby_facilities(nearby_facilities: Any) -> tuple[bool, Optional[str]]:
    """
    Validate nearby facilities JSON structure.

    Args:
        nearby_facilities: Nearby facilities array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if nearby_facilities is None:
        return True, None

    try:
        validate(instance=nearby_facilities, schema=NEARBY_FACILITIES_SCHEMA)
        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid nearby facilities structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


def validate_property_photos(property_photos: Any) -> tuple[bool, Optional[str]]:
    """
    Validate property photos JSON structure.

    Args:
        property_photos: Property photos array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if property_photos is None:
        return True, None

    try:
        validate(instance=property_photos, schema=PROPERTY_PHOTOS_SCHEMA)

        # Additional validation: check image data size (~5MB max per image)
        MAX_IMAGE_SIZE = 7_000_000  # ~5MB in base64
        for i, photo in enumerate(property_photos):
            image_data = photo.get('image_data', '')
            if len(image_data) > MAX_IMAGE_SIZE:
                return False, f"Photo {i+1} is too large (max 5MB per image)"

        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid property photos structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


def validate_access_road_conditions(access_road_conditions: Any) -> tuple[bool, Optional[str]]:
    """
    Validate access road conditions JSON structure.

    Args:
        access_road_conditions: Access road conditions array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if access_road_conditions is None:
        return True, None

    try:
        validate(instance=access_road_conditions, schema=ACCESS_ROAD_CONDITIONS_SCHEMA)
        return True, None
    except JSONSchemaValidationError as e:
        error_path = " -> ".join(str(p) for p in e.path)
        error_msg = f"Invalid access road conditions structure: {e.message}"
        if error_path:
            error_msg += f" (at {error_path})"
        return False, error_msg


# ===== EXPORT ALL =====

__all__ = [
    'BOUNDARIES_SCHEMA',
    'BUILDINGS_SCHEMA',
    'COMPARABLE_PROPERTIES_SCHEMA',
    'DEEDS_SCHEMA',
    'NEARBY_FACILITIES_SCHEMA',
    'PROPERTY_PHOTOS_SCHEMA',
    'ACCESS_ROAD_CONDITIONS_SCHEMA',
    'validate_boundaries',
    'validate_buildings',
    'validate_comparable_properties',
    'validate_deeds',
    'validate_nearby_facilities',
    'validate_property_photos',
    'validate_access_road_conditions',
    'validate_json_field',
]
