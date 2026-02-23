"""
Property CRUD operations, report-property junction, and multi-property report creation.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from .. import models, schemas
from .building_helpers import _normalize_and_validate_buildings, _duplicate_entity_data
from .report_crud import get_report


def create_property(db: Session, property: schemas.PropertyCreate, user_id: int):
    """Create a new property for a user"""
    _normalize_and_validate_buildings(property.buildings)
    db_property = models.Property(**property.model_dump(), user_id=user_id)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


def get_property(db: Session, property_id: int, user_id: int = None):
    """Get property by ID, optionally filtered by user_id"""
    query = db.query(models.Property).filter(models.Property.id == property_id)
    if user_id:
        query = query.filter(models.Property.user_id == user_id)
    return query.first()


def get_user_properties(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all properties for a specific user"""
    return db.query(models.Property).filter(
        models.Property.user_id == user_id
    ).order_by(models.Property.created_at.desc()).offset(skip).limit(limit).all()


def get_property_templates(db: Session, user_id: int):
    """Get all property templates (Property Library) for a user"""
    return db.query(models.Property).filter(
        models.Property.user_id == user_id,
        models.Property.is_template == True
    ).order_by(models.Property.template_name).all()


def update_property(db: Session, property_id: int, property_update: schemas.PropertyUpdate,
                    user_id: int = None):
    """Update a property"""
    query = db.query(models.Property).filter(models.Property.id == property_id)
    if user_id:
        query = query.filter(models.Property.user_id == user_id)

    db_property = query.first()
    if not db_property:
        return None

    update_data = property_update.model_dump(exclude_unset=True)

    if 'buildings' in update_data and update_data['buildings']:
        _normalize_and_validate_buildings(update_data['buildings'])

    for field, value in update_data.items():
        setattr(db_property, field, value)

    db.commit()
    db.refresh(db_property)
    return db_property


def delete_property(db: Session, property_id: int, user_id: int = None):
    """Delete a property - only if not used in any reports"""
    query = db.query(models.Property).filter(models.Property.id == property_id)
    if user_id:
        query = query.filter(models.Property.user_id == user_id)

    db_property = query.first()
    if not db_property:
        return False

    usage_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.property_id == property_id
    ).count()

    if usage_count > 0:
        raise ValueError(
            f"Cannot delete property. It is used in {usage_count} report(s). "
            "Remove it from all reports first."
        )

    db.delete(db_property)
    db.commit()
    return True


def update_property_status(db: Session, property_id: int, status: str, user_id: int = None):
    """Update the status of a property ('draft' or 'completed')"""
    if status not in ['draft', 'completed']:
        raise ValueError(f"Invalid status: {status}. Must be 'draft' or 'completed'")

    query = db.query(models.Property).filter(models.Property.id == property_id)
    if user_id:
        query = query.filter(models.Property.user_id == user_id)

    db_property = query.first()
    if not db_property:
        return None

    db_property.status = status
    db.commit()
    db.refresh(db_property)
    return db_property


def duplicate_property(db: Session, report_id: int, property_id: int, user_id: int):
    """
    Duplicate a property within a report (deep copy including images).

    Uses SQLAlchemy reflection to automatically copy all fields.
    """
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    db_property = get_property(db, property_id, user_id)
    if not db_property:
        raise ValueError("Property not found or access denied")

    report_property = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id,
        models.ReportProperty.property_id == property_id
    ).first()

    if not report_property:
        raise ValueError("Property is not in this report")

    property_dict = _duplicate_entity_data(
        db_property,
        exclude_fields={'id', 'created_at', 'updated_at', 'user_id'},
        override_fields={
            'status': 'draft',
            'is_template': False,
            'template_name': None,
        }
    )

    new_property = models.Property(**property_dict, user_id=user_id)
    db.add(new_property)
    db.flush()

    max_order_result = db.query(func.max(models.ReportProperty.property_order)).filter(
        models.ReportProperty.report_id == report_id
    ).scalar()

    max_order = max_order_result if max_order_result is not None else -1

    new_report_property = models.ReportProperty(
        report_id=report_id,
        property_id=new_property.id,
        property_order=max_order + 1
    )
    db.add(new_report_property)
    db.flush()

    property_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()

    db_report.property_count = property_count
    db_report.is_multi_property = property_count > 1

    db.commit()
    db.refresh(new_property)
    return new_property


def get_report_completed_properties(db: Session, report_id: int):
    """
    Get only completed properties for a report, ordered by property_order.
    Used for report generation to filter out draft properties.
    """
    return db.query(models.Property).join(
        models.ReportProperty,
        models.ReportProperty.property_id == models.Property.id
    ).filter(
        models.ReportProperty.report_id == report_id,
        models.Property.status == 'completed'
    ).order_by(models.ReportProperty.property_order).all()


def create_report_property(db: Session, report_property: schemas.ReportPropertyCreate):
    """Create a report-property association"""
    db_report_property = models.ReportProperty(**report_property.model_dump())
    db.add(db_report_property)
    db.commit()
    db.refresh(db_report_property)
    return db_report_property


def add_property_to_report(db: Session, report_id: int, property_id: int,
                           user_id: int, property_order: int = None):
    """Add an existing property to a report"""
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    db_property = get_property(db, property_id, user_id)
    if not db_property:
        raise ValueError("Property not found or access denied")

    existing = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id,
        models.ReportProperty.property_id == property_id
    ).first()
    if existing:
        raise ValueError("Property is already in this report")

    if property_order is None:
        max_order = db.query(models.ReportProperty).filter(
            models.ReportProperty.report_id == report_id
        ).count()
        property_order = max_order + 1

    report_property = models.ReportProperty(
        report_id=report_id,
        property_id=property_id,
        property_order=property_order
    )
    db.add(report_property)
    db.flush()

    new_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()
    db_report.property_count = new_count
    db_report.is_multi_property = new_count > 1

    _update_report_total_valuation(db, db_report)

    db.commit()
    db.refresh(report_property)
    return report_property


def remove_property_from_report(db: Session, report_id: int, property_id: int, user_id: int):
    """Remove a property from a report"""
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    report_property = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id,
        models.ReportProperty.property_id == property_id
    ).first()

    if not report_property:
        raise ValueError("Property is not in this report")

    property_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()

    if property_count <= 1:
        raise ValueError("Cannot remove the last property from a report")

    db.delete(report_property)
    db.flush()

    new_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()
    db_report.property_count = new_count
    db_report.is_multi_property = new_count > 1

    _update_report_total_valuation(db, db_report)

    db.commit()
    return True


def reorder_report_properties(db: Session, report_id: int, property_order_map: dict, user_id: int):
    """
    Reorder properties in a report.
    property_order_map: {property_id: new_order, ...}
    """
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    for property_id, new_order in property_order_map.items():
        report_property = db.query(models.ReportProperty).filter(
            models.ReportProperty.report_id == report_id,
            models.ReportProperty.property_id == property_id
        ).first()

        if report_property:
            report_property.property_order = new_order

    db.commit()
    return True


def create_multi_property_report(db: Session, report_data: schemas.MultiPropertyReportCreate,
                                  user_id: int):
    """
    Create a multi-property report with proper transaction handling.

    Can either link to existing properties (property_ids) or create new ones (properties).
    Atomic: all changes succeed or none do.
    """
    try:
        property_ids = list(report_data.property_ids or [])
        properties_to_create = report_data.properties or []
        invoice_data = report_data.invoice_data

        report_dict = report_data.model_dump(exclude={'property_ids', 'properties', 'invoice_data'})
        report_dict['user_id'] = user_id
        report_dict['is_multi_property'] = True
        report_dict['property_count'] = len(property_ids) + len(properties_to_create)

        if invoice_data:
            report_dict['invoice_data'] = invoice_data.model_dump() if hasattr(invoice_data, 'model_dump') else invoice_data

        db_report = models.Report(**report_dict)
        db.add(db_report)
        db.flush()

        for prop_data in properties_to_create:
            db_property = create_property(db, prop_data, user_id)
            property_ids.append(db_property.id)

        for idx, property_id in enumerate(property_ids, start=1):
            db_property = get_property(db, property_id, user_id)
            if not db_property:
                raise ValueError(f"Property {property_id} not found or access denied")

            report_property = models.ReportProperty(
                report_id=db_report.id,
                property_id=property_id,
                property_order=idx
            )
            db.add(report_property)

        db.flush()

        _update_report_total_valuation(db, db_report)

        db.commit()
        db.refresh(db_report)
        return db_report

    except Exception:
        db.rollback()
        raise


def _update_report_total_valuation(db: Session, db_report: models.Report):
    """
    Recalculate total valuation for a report.

    Uses joinedload for efficient single-query loading and SELECT FOR UPDATE
    to prevent race conditions during concurrent updates.
    """
    from sqlalchemy.orm import joinedload

    report_properties = (
        db.query(models.ReportProperty)
        .options(joinedload(models.ReportProperty.property))
        .filter(models.ReportProperty.report_id == db_report.id)
        .with_for_update()
        .all()
    )

    total = 0
    for rp in report_properties:
        if rp.override_market_value is not None:
            total += float(rp.override_market_value)
        elif rp.property and rp.property.valuation_market_value is not None:
            total += float(rp.property.valuation_market_value)

    db_report.total_valuation_amount = total if total > 0 else None
