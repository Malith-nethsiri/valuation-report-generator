"""
Shared utilities for CRUD operations across domains.

Contains:
- BaseCRUD instance declarations for common entities
- Ownership verification helper
- Building data normalization and validation
- Generic entity duplication via SQLAlchemy reflection
"""
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import copy
from typing import List, Optional, Set, Dict, Any

from .. import models
from ..base_crud import BaseCRUD


# BaseCRUD instances — used by vehicle_crud and available for future use
_base_report_crud = BaseCRUD(models.Report, "Report")
_base_property_crud = BaseCRUD(models.Property, "Property")
_base_vehicle_crud = BaseCRUD(models.Vehicle, "Vehicle")


def verify_ownership(db: Session, entity_type: type, entity_id: int,
                     user_id: int, entity_name: str = "Entity"):
    """
    Generic ownership verification helper.

    Queries for entity by ID and user_id, raises ValueError if not found.
    """
    entity = db.query(entity_type).filter(
        entity_type.id == entity_id,
        entity_type.user_id == user_id
    ).first()
    if not entity:
        raise ValueError(f"{entity_name} not found or access denied")
    return entity


def _normalize_and_validate_buildings(buildings) -> Optional[List[dict]]:
    """
    Convert buildings to dicts and validate in one step.

    Handles both Pydantic Building objects and raw dicts.
    Returns None if buildings is empty/None.
    """
    if not buildings:
        return None

    buildings_dicts = [
        b.model_dump() if hasattr(b, 'model_dump') else b
        for b in buildings
    ]

    validate_report_buildings(buildings_dicts)
    return buildings_dicts


def _duplicate_entity_data(
    entity,
    exclude_fields: Set[str] = None,
    override_fields: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract all column data from a SQLAlchemy entity for duplication.

    Uses SQLAlchemy inspection to automatically copy all columns,
    eliminating manual field mappings that can become outdated.
    """
    default_exclude = {'id', 'created_at', 'updated_at'}
    exclude = default_exclude | (exclude_fields or set())

    mapper = inspect(entity.__class__)

    data = {}
    for column in mapper.columns:
        if column.key not in exclude:
            value = getattr(entity, column.key)
            if isinstance(value, (dict, list)):
                data[column.key] = copy.deepcopy(value)
            else:
                data[column.key] = value

    if override_fields:
        data.update(override_fields)

    return data


def validate_report_buildings(buildings: List[dict]):
    """Validate building data including photos"""
    if not buildings:
        return

    for idx, building in enumerate(buildings):
        photos = building.get('building_photos', [])

        if len(photos) > 5:
            raise ValueError(
                f"Building {idx + 1} ('{building.get('building_name', 'Unnamed')}') "
                f"has {len(photos)} photos. Maximum is 5 per building."
            )

        for photo_idx, photo in enumerate(photos):
            required = ['id', 'image_data', 'order']
            missing = [f for f in required if f not in photo]
            if missing:
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: Missing required fields: {', '.join(missing)}"
                )

            if not isinstance(photo['image_data'], str):
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: image_data must be a string (base64)"
                )

            if not photo['image_data'].startswith('data:image/'):
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: Invalid image data format (must be data:image/...)"
                )
