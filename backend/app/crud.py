from sqlalchemy.orm import Session
from sqlalchemy import inspect
import copy
from . import models, schemas
from .auth import get_password_hash
from typing import List, Optional, Set, Dict, Any, Type

# Validation Functions
def verify_ownership(db: Session, entity_type: type, entity_id: int,
                     user_id: int, entity_name: str = "Entity"):
    """
    Generic ownership verification helper.

    Queries for entity by ID and user_id, raises ValueError if not found.

    Args:
        db: Database session
        entity_type: SQLAlchemy model class (e.g., models.Report)
        entity_id: ID of the entity to verify
        user_id: User ID that must own the entity
        entity_name: Human-readable name for error messages

    Returns:
        The entity if found and owned by user

    Raises:
        ValueError: If entity not found or not owned by user
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

    Args:
        buildings: List of Building objects or dicts, or None

    Returns:
        List of validated building dicts, or None if input is empty
    """
    if not buildings:
        return None

    # Convert Building objects to dicts if needed
    buildings_dicts = [
        b.model_dump() if hasattr(b, 'model_dump') else b
        for b in buildings
    ]

    # Validate the buildings
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

    Args:
        entity: SQLAlchemy model instance to duplicate
        exclude_fields: Set of field names to exclude (default: id, created_at, updated_at)
        override_fields: Dict of field values to override after copying

    Returns:
        Dictionary of field values ready to create a new entity

    Example:
        data = _duplicate_entity_data(
            db_property,
            exclude_fields={'id', 'created_at', 'updated_at'},
            override_fields={'status': 'draft', 'is_template': False}
        )
        new_property = models.Property(**data, user_id=user_id)
    """
    # Default excluded fields
    default_exclude = {'id', 'created_at', 'updated_at'}
    exclude = default_exclude | (exclude_fields or set())

    # Get all column names from the model using inspection
    mapper = inspect(entity.__class__)

    # Build dictionary of fields to copy
    data = {}
    for column in mapper.columns:
        if column.key not in exclude:
            value = getattr(entity, column.key)

            # Deep copy mutable types (dict, list) to avoid reference issues
            if isinstance(value, (dict, list)):
                data[column.key] = copy.deepcopy(value)
            else:
                data[column.key] = value

    # Apply overrides
    if override_fields:
        data.update(override_fields)

    return data


def validate_report_buildings(buildings: List[dict]):
    """Validate building data including photos"""
    if not buildings:
        return

    for idx, building in enumerate(buildings):
        photos = building.get('building_photos', [])

        # Max 5 photos per building
        if len(photos) > 5:
            raise ValueError(
                f"Building {idx + 1} ('{building.get('building_name', 'Unnamed')}') "
                f"has {len(photos)} photos. Maximum is 5 per building."
            )

        # Validate photo structure
        for photo_idx, photo in enumerate(photos):
            required = ['id', 'image_data', 'order']
            missing = [f for f in required if f not in photo]
            if missing:
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: Missing required fields: {', '.join(missing)}"
                )

            # Validate image data format
            if not isinstance(photo['image_data'], str):
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: image_data must be a string (base64)"
                )

            if not photo['image_data'].startswith('data:image/'):
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: Invalid image data format (must be data:image/...)"
                )

# User CRUD Operations
def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with hashed password"""
    hashed_password = get_password_hash(user.password)

    # Convert user data to dict and remove password field
    user_data = user.model_dump(exclude={"password"})

    # Create user with all fields from schema
    db_user = models.User(
        password_hash=hashed_password,
        **user_data
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    """Update user information"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# Bank Account CRUD Operations
def add_bank_account(db: Session, user_id: int, account: schemas.BankAccountCreate):
    """Add a new bank account to user profile"""
    import uuid

    db_user = get_user(db, user_id)
    if not db_user:
        return None

    # Initialize bank_accounts if None
    if db_user.bank_accounts is None:
        db_user.bank_accounts = []

    # Create new account with UUID
    new_account = {
        "id": str(uuid.uuid4()),
        "bank_name": account.bank_name,
        "account_number": account.account_number,
        "branch_name": account.branch_name
    }

    # Append to existing accounts
    accounts = db_user.bank_accounts.copy() if db_user.bank_accounts else []
    accounts.append(new_account)
    db_user.bank_accounts = accounts

    db.commit()
    db.refresh(db_user)
    return new_account

def update_bank_account(db: Session, user_id: int, account_id: str, account_update: schemas.BankAccountUpdate):
    """Update an existing bank account"""
    db_user = get_user(db, user_id)
    if not db_user or not db_user.bank_accounts:
        return None

    accounts = db_user.bank_accounts.copy()
    account_found = False

    for account in accounts:
        if account["id"] == account_id:
            # Update only provided fields
            update_data = account_update.model_dump(exclude_unset=True)
            account.update(update_data)
            account_found = True
            break

    if not account_found:
        return None

    db_user.bank_accounts = accounts
    db.commit()
    db.refresh(db_user)

    return next(acc for acc in accounts if acc["id"] == account_id)

def delete_bank_account(db: Session, user_id: int, account_id: str):
    """Delete a bank account"""
    db_user = get_user(db, user_id)
    if not db_user or not db_user.bank_accounts:
        return False

    accounts = [acc for acc in db_user.bank_accounts if acc["id"] != account_id]

    if len(accounts) == len(db_user.bank_accounts):
        return False  # Account not found

    db_user.bank_accounts = accounts
    db.commit()
    return True

def get_bank_accounts(db: Session, user_id: int):
    """Get all bank accounts for a user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    return db_user.bank_accounts or []

# Report CRUD Operations
def create_report(db: Session, report: schemas.ReportCreate, user_id: int):
    """Create a new report for a user"""
    # Validate building photos before creating report
    _normalize_and_validate_buildings(report.buildings)

    db_report = models.Report(**report.model_dump(), user_id=user_id)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report(db: Session, report_id: int, user_id: int = None):
    """Get report by ID, optionally filtered by user_id"""
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)
    return query.first()

def get_user_reports(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all reports for a specific user"""
    return db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_all_reports(db: Session, skip: int = 0, limit: int = 100):
    """Get all reports (admin function)"""
    return db.query(models.Report).offset(skip).limit(limit).all()

def update_report(db: Session, report_id: int, report_update: schemas.ReportUpdate, user_id: int = None):
    """Update a report"""
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)

    db_report = query.first()
    if not db_report:
        return None

    update_data = report_update.model_dump(exclude_unset=True)

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[UPDATE_REPORT] Report ID: {report_id}, Fields in update: {list(update_data.keys())}")
    if 'buildings' in update_data:
        logger.info(f"[UPDATE_REPORT] Buildings data present: {len(update_data['buildings']) if update_data['buildings'] else 0} buildings")
    else:
        logger.info(f"[UPDATE_REPORT] Buildings data NOT in update")

    if 'valuation_buildings_data' in update_data:
        logger.info(f"[UPDATE_REPORT] Valuation buildings data present: {len(update_data['valuation_buildings_data']) if update_data['valuation_buildings_data'] else 0} items")
    else:
        logger.info(f"[UPDATE_REPORT] Valuation buildings data NOT in update")

    # Validate building photos if buildings are being updated
    if 'buildings' in update_data and update_data['buildings']:
        _normalize_and_validate_buildings(update_data['buildings'])

    for field, value in update_data.items():
        setattr(db_report, field, value)

    db.commit()
    db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: int, user_id: int = None):
    """Delete a report"""
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)

    db_report = query.first()
    if db_report:
        db.delete(db_report)
        db.commit()
        return True
    return False

def duplicate_report(db: Session, report_id: int, user_id: int):
    """
    Duplicate an existing report as a new draft.

    Uses SQLAlchemy reflection to automatically copy all fields,
    ensuring new fields added to the Report model are included.
    """
    # Get original report
    original_report = get_report(db, report_id, user_id)
    if not original_report:
        return None

    # Use reflection-based duplication to copy all fields automatically
    report_data = _duplicate_entity_data(
        original_report,
        exclude_fields={'id', 'created_at', 'updated_at'},
        override_fields={
            # Reset draft-specific fields
            'status': 'draft',
            'report_reference': None,
            'report_date': None,
            'certification_text': None,
            'certification_date': None,
            'certification_valuer_name': None,
            'certification_valuer_designation': None,
            'certificate_survey_plan_ref': None,
            'certificate_survey_plan_date': None,
            'certificate_identity_confirmed': False,
        }
    )

    # Create new report
    new_report = models.Report(**report_data)
    db.add(new_report)
    db.flush()  # Get the new report ID

    # If multi-property report, duplicate the property associations
    if original_report.is_multi_property:
        original_associations = get_report_properties(db, report_id)
        for assoc in original_associations:
            new_assoc = models.ReportProperty(
                report_id=new_report.id,
                property_id=assoc.property_id,
                property_order=assoc.property_order
            )
            db.add(new_assoc)

    db.commit()
    db.refresh(new_report)
    return new_report

# Property CRUD Operations
def create_property(db: Session, property: schemas.PropertyCreate, user_id: int):
    """Create a new property for a user"""
    # Validate building photos if present
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

def update_property(db: Session, property_id: int, property_update: schemas.PropertyUpdate, user_id: int = None):
    """Update a property"""
    query = db.query(models.Property).filter(models.Property.id == property_id)
    if user_id:
        query = query.filter(models.Property.user_id == user_id)

    db_property = query.first()
    if not db_property:
        return None

    update_data = property_update.model_dump(exclude_unset=True)

    # Validate building photos if buildings are being updated
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

    # Check if property is used in any reports
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
    """
    Update the status of a property ('draft' or 'completed')

    Args:
        db: Database session
        property_id: ID of the property to update
        status: New status value ('draft' or 'completed')
        user_id: Optional user ID for ownership verification

    Returns:
        Updated property or None if not found

    Raises:
        ValueError: If status is not 'draft' or 'completed'
    """
    # Validate status
    if status not in ['draft', 'completed']:
        raise ValueError(f"Invalid status: {status}. Must be 'draft' or 'completed'")

    # Get property
    query = db.query(models.Property).filter(models.Property.id == property_id)
    if user_id:
        query = query.filter(models.Property.user_id == user_id)

    db_property = query.first()
    if not db_property:
        return None

    # Update status
    db_property.status = status
    db.commit()
    db.refresh(db_property)
    return db_property

def duplicate_property(db: Session, report_id: int, property_id: int, user_id: int):
    """
    Duplicate a property within a report (deep copy including images).

    Uses SQLAlchemy reflection to automatically copy all fields,
    ensuring new fields added to the Property model are included.

    Args:
        db: Database session
        report_id: ID of the report containing the property
        property_id: ID of the property to duplicate
        user_id: User ID for ownership verification

    Returns:
        Newly created property

    Raises:
        ValueError: If property or report not found or access denied
    """
    # Verify user owns the report
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    # Get the property to duplicate
    db_property = get_property(db, property_id, user_id)
    if not db_property:
        raise ValueError("Property not found or access denied")

    # Verify property is in this report
    report_property = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id,
        models.ReportProperty.property_id == property_id
    ).first()

    if not report_property:
        raise ValueError("Property is not in this report")

    # Use reflection-based duplication to copy all fields automatically
    # This ensures new fields added to the model are always included
    property_dict = _duplicate_entity_data(
        db_property,
        exclude_fields={'id', 'created_at', 'updated_at', 'user_id'},
        override_fields={
            'status': 'draft',        # Duplicates start as draft
            'is_template': False,     # Duplicates are not templates
            'template_name': None,    # Clear template name
        }
    )

    # Create new property
    new_property = models.Property(**property_dict, user_id=user_id)
    db.add(new_property)
    db.flush()  # Get the new property ID

    # Add new property to the report with incremented order
    # Find the maximum property_order value (not count)
    from sqlalchemy import func
    max_order_result = db.query(func.max(models.ReportProperty.property_order)).filter(
        models.ReportProperty.report_id == report_id
    ).scalar()

    # If no properties exist, start at 0; otherwise increment max
    max_order = max_order_result if max_order_result is not None else -1

    new_report_property = models.ReportProperty(
        report_id=report_id,
        property_id=new_property.id,
        property_order=max_order + 1
    )
    db.add(new_report_property)
    db.flush()  # Ensure the new ReportProperty is in the session

    # Update report metadata (count actual properties including the new one)
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
    Get only completed properties for a report, ordered by property_order

    Used for report generation to filter out draft properties.

    Args:
        db: Database session
        report_id: ID of the report

    Returns:
        List of completed Property objects, ordered by property_order
    """
    return db.query(models.Property).join(
        models.ReportProperty,
        models.ReportProperty.property_id == models.Property.id
    ).filter(
        models.ReportProperty.report_id == report_id,
        models.Property.status == 'completed'
    ).order_by(models.ReportProperty.property_order).all()

# ReportProperty Junction Operations
def create_report_property(db: Session, report_property: schemas.ReportPropertyCreate):
    """Create a report-property association"""
    db_report_property = models.ReportProperty(**report_property.model_dump())
    db.add(db_report_property)
    db.commit()
    db.refresh(db_report_property)
    return db_report_property

def get_report_properties(db: Session, report_id: int):
    """Get all properties for a report, ordered by property_order"""
    return db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).order_by(models.ReportProperty.property_order).all()

def add_property_to_report(db: Session, report_id: int, property_id: int, user_id: int, property_order: int = None):
    """Add an existing property to a report"""
    # Verify user owns both report and property
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    db_property = get_property(db, property_id, user_id)
    if not db_property:
        raise ValueError("Property not found or access denied")

    # Check if property is already in this report
    existing = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id,
        models.ReportProperty.property_id == property_id
    ).first()
    if existing:
        raise ValueError("Property is already in this report")

    # Determine property order
    if property_order is None:
        max_order = db.query(models.ReportProperty).filter(
            models.ReportProperty.report_id == report_id
        ).count()
        property_order = max_order + 1

    # Create association
    report_property = models.ReportProperty(
        report_id=report_id,
        property_id=property_id,
        property_order=property_order
    )
    db.add(report_property)
    db.flush()  # Ensure association is in database before counting

    # Update report metadata
    new_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()
    db_report.property_count = new_count
    db_report.is_multi_property = new_count > 1

    # Recalculate total valuation
    _update_report_total_valuation(db, db_report)

    db.commit()
    db.refresh(report_property)
    return report_property

def remove_property_from_report(db: Session, report_id: int, property_id: int, user_id: int):
    """Remove a property from a report"""
    # Verify user owns the report
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    # Find the association
    report_property = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id,
        models.ReportProperty.property_id == property_id
    ).first()

    if not report_property:
        raise ValueError("Property is not in this report")

    # Prevent removing the last property
    property_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()

    if property_count <= 1:
        raise ValueError("Cannot remove the last property from a report")

    db.delete(report_property)
    db.flush()  # Ensure deletion is in database before counting

    # Update report metadata
    new_count = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).count()
    db_report.property_count = new_count
    db_report.is_multi_property = new_count > 1

    # Recalculate total valuation
    _update_report_total_valuation(db, db_report)

    db.commit()
    return True

def reorder_report_properties(db: Session, report_id: int, property_order_map: dict, user_id: int):
    """
    Reorder properties in a report
    property_order_map: {property_id: new_order, ...}
    """
    # Verify user owns the report
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    # Update each property's order
    for property_id, new_order in property_order_map.items():
        report_property = db.query(models.ReportProperty).filter(
            models.ReportProperty.report_id == report_id,
            models.ReportProperty.property_id == property_id
        ).first()

        if report_property:
            report_property.property_order = new_order

    db.commit()
    return True

# Multi-Property Report Operations
def create_multi_property_report(db: Session, report_data: schemas.MultiPropertyReportCreate, user_id: int):
    """
    Create a multi-property report
    Can either link to existing properties (property_ids) or create new ones (properties)
    """
    # Extract property-related data
    property_ids = report_data.property_ids or []
    properties_to_create = report_data.properties or []
    invoice_data = report_data.invoice_data

    # Create the base report with common fields
    report_dict = report_data.model_dump(exclude={'property_ids', 'properties', 'invoice_data'})
    report_dict['user_id'] = user_id
    report_dict['is_multi_property'] = True
    report_dict['property_count'] = len(property_ids) + len(properties_to_create)

    if invoice_data:
        report_dict['invoice_data'] = invoice_data.model_dump() if hasattr(invoice_data, 'model_dump') else invoice_data

    db_report = models.Report(**report_dict)
    db.add(db_report)
    db.flush()  # Get report ID without committing

    # Create new properties if provided
    created_properties = []
    for prop_data in properties_to_create:
        db_property = create_property(db, prop_data, user_id)
        created_properties.append(db_property)
        property_ids.append(db_property.id)

    # Create report-property associations
    for idx, property_id in enumerate(property_ids, start=1):
        # Verify user owns the property
        db_property = get_property(db, property_id, user_id)
        if not db_property:
            db.rollback()
            raise ValueError(f"Property {property_id} not found or access denied")

        report_property = models.ReportProperty(
            report_id=db_report.id,
            property_id=property_id,
            property_order=idx
        )
        db.add(report_property)

    # Flush to ensure associations are in database
    db.flush()

    # Calculate total valuation after associations are flushed
    _update_report_total_valuation(db, db_report)

    db.commit()
    db.refresh(db_report)
    return db_report

def _update_report_total_valuation(db: Session, db_report: models.Report):
    """
    Recalculate total valuation for a report.

    Uses joinedload to efficiently load property data in a single query,
    avoiding N+1 query performance issues.
    """
    from sqlalchemy.orm import joinedload

    # Query report properties with joined property data (single query)
    report_properties = (
        db.query(models.ReportProperty)
        .options(joinedload(models.ReportProperty.property))
        .filter(models.ReportProperty.report_id == db_report.id)
        .all()
    )

    total = 0
    for rp in report_properties:
        # Use override value if set, otherwise use property's market value
        if rp.override_market_value is not None:
            total += float(rp.override_market_value)
        elif rp.property and rp.property.valuation_market_value is not None:
            total += float(rp.property.valuation_market_value)

    db_report.total_valuation_amount = total if total > 0 else None

# Legacy functions removed for clean v0.1 implementation
# All functionality moved to authenticated user + report system
