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


def get_user_reports_filtered(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 8,
    reference: str = None,
    applicant_name: str = None,
    village: str = None,
    report_date: str = None  # YYYY-MM-DD format
):
    """
    Get filtered and paginated reports for a user.
    Returns tuple: (reports, total_count, stats)

    Filter behaviors:
    - reference: Exact match (normalized - spaces removed, case insensitive)
    - applicant_name: Partial match (ILIKE, case insensitive)
    - village: Partial match (ILIKE, case insensitive)
    - report_date: Exact date match on created_at
    """
    from sqlalchemy import func, and_, cast, Date
    from datetime import datetime, date

    # Base query for user's reports
    base_query = db.query(models.Report).filter(models.Report.user_id == user_id)

    # Apply filters
    filters = []

    # Reference number - partial match, case insensitive
    if reference:
        # Use ILIKE for partial matching (contains)
        filters.append(
            models.Report.report_reference.ilike(f"%{reference}%")
        )

    # Applicant name - partial match, case insensitive
    if applicant_name:
        filters.append(
            models.Report.applicant_full_name.ilike(f"%{applicant_name}%")
        )

    # Village - partial match, case insensitive
    if village:
        filters.append(
            models.Report.property_village.ilike(f"%{village}%")
        )

    # Report date - exact date match on created_at
    if report_date:
        try:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
            filters.append(
                cast(models.Report.created_at, Date) == target_date
            )
        except ValueError:
            pass  # Invalid date format, ignore filter

    # Apply all filters with AND logic
    filtered_query = base_query
    if filters:
        filtered_query = base_query.filter(and_(*filters))

    # Get total count of filtered results
    total_count = filtered_query.count()

    # Get paginated reports (sorted by created_at descending)
    reports = filtered_query.order_by(
        models.Report.created_at.desc()
    ).offset(skip).limit(limit).all()

    # Calculate stats (based on filtered results)
    current_month = date.today().replace(day=1)

    # Stats for filtered results
    stats_query = filtered_query

    this_month_count = stats_query.filter(
        models.Report.created_at >= current_month
    ).count()

    completed_count = stats_query.filter(
        models.Report.status == 'completed'
    ).count()

    draft_count = stats_query.filter(
        models.Report.status == 'draft'
    ).count()

    stats = {
        "total_count": total_count,
        "this_month_count": this_month_count,
        "completed_count": completed_count,
        "draft_count": draft_count
    }

    return reports, total_count, stats


def get_adjacent_report_date(
    db: Session,
    user_id: int,
    current_date: str,  # YYYY-MM-DD format
    direction: str  # "next" or "previous"
) -> str:
    """
    Get the next or previous date that has reports for the user.
    Used for date filter navigation when reports for current date are exhausted.
    Returns date string (YYYY-MM-DD) or None if no adjacent date found.
    """
    from sqlalchemy import func, cast, Date
    from datetime import datetime

    try:
        target_date = datetime.strptime(current_date, "%Y-%m-%d").date()
    except ValueError:
        return None

    # Get distinct dates with reports
    if direction == "next":
        # Find the next date after current_date that has reports
        result = db.query(
            cast(models.Report.created_at, Date)
        ).filter(
            models.Report.user_id == user_id,
            cast(models.Report.created_at, Date) > target_date
        ).order_by(
            cast(models.Report.created_at, Date).asc()
        ).first()
    else:  # previous
        # Find the previous date before current_date that has reports
        result = db.query(
            cast(models.Report.created_at, Date)
        ).filter(
            models.Report.user_id == user_id,
            cast(models.Report.created_at, Date) < target_date
        ).order_by(
            cast(models.Report.created_at, Date).desc()
        ).first()

    if result and result[0]:
        return result[0].strftime("%Y-%m-%d")
    return None


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
        "access_road_segments": db_property.access_road_segments,
        "access_road_conditions": db_property.access_road_conditions,
        "access_entry_mode": db_property.access_entry_mode,
        "access_road_classes_detected": db_property.access_road_classes_detected,
        "land_extent_acres": db_property.land_extent_acres,
        "land_extent_roods": db_property.land_extent_roods,
        "land_extent_perches": db_property.land_extent_perches,
        "land_extent_hectares": db_property.land_extent_hectares,
        "land_extent_square_meters": db_property.land_extent_square_meters,
        "land_extent_formatted": db_property.land_extent_formatted,
        "land_traditional_name": db_property.land_traditional_name,
        "boundaries": db_property.boundaries,
        "physical_boundaries_types": db_property.physical_boundaries_types,
        "physical_boundaries_description": db_property.physical_boundaries_description,
        "boundary_types_per_direction": db_property.boundary_types_per_direction,
        "entrance_type": db_property.entrance_type,
        "boundaries_summary_text": db_property.boundaries_summary_text,
        "has_multiple_lots": db_property.has_multiple_lots,
        "lots_data": db_property.lots_data,
        "land_shape": db_property.land_shape,
        "land_type": db_property.land_type,
        "land_frontage_type": db_property.land_frontage_type,
        "land_frontage_width": db_property.land_frontage_width,
        "land_frontage_description": db_property.land_frontage_description,
        "land_level": db_property.land_level,
        "land_level_difference": db_property.land_level_difference,
        "soil_type": db_property.soil_type,
        "water_table_depth": db_property.water_table_depth,
        "flood_risk": db_property.flood_risk,
        "inundation_risk": db_property.inundation_risk,
        "earth_slip_risk": db_property.earth_slip_risk,
        "land_condition": db_property.land_condition,
        "land_condition_description": db_property.land_condition_description,
        "land_description_text": db_property.land_description_text,
        "elevation_changes": db_property.elevation_changes,
        "drainage_pattern": db_property.drainage_pattern,
        "vegetation_type": db_property.vegetation_type,
        "natural_features": db_property.natural_features,
        "buildings": db_property.buildings,  # Includes building photos (Base64)
        "occupier_name": db_property.occupier_name,
        "occupier_relationship": db_property.occupier_relationship,
        "property_photos": db_property.property_photos,  # Includes property photos (Base64)
        "distance_to_major_town_km": db_property.distance_to_major_town_km,
        "major_town_name": db_property.major_town_name,
        "nearby_facilities": db_property.nearby_facilities,
        "has_electricity": db_property.has_electricity,
        "water_supply_type": db_property.water_supply_type,
        "telecommunication_types": db_property.telecommunication_types,
        "internet_types": db_property.internet_types,
        "has_public_transport": db_property.has_public_transport,
        "public_transport_routes": db_property.public_transport_routes,
        "public_transport_frequency": db_property.public_transport_frequency,
        "nearest_bus_stop_distance_km": db_property.nearest_bus_stop_distance_km,
        "nearest_bus_stop_name": db_property.nearest_bus_stop_name,
        "nearest_railway_station": db_property.nearest_railway_station,
        "nearest_railway_distance_km": db_property.nearest_railway_distance_km,
        "area_type": db_property.area_type,
        "development_level": db_property.development_level,
        "predominant_building_type": db_property.predominant_building_type,
        "is_tourist_area": db_property.is_tourist_area,
        "tourist_attractions_nearby": db_property.tourist_attractions_nearby,
        "locality_description_text": db_property.locality_description_text,
        "ownership_type": db_property.ownership_type,
        "street_lines_status": db_property.street_lines_status,
        "street_lines_gazette_ref": db_property.street_lines_gazette_ref,
        "street_lines_gazette_date": db_property.street_lines_gazette_date,
        "street_lines_impact_description": db_property.street_lines_impact_description,
        "building_limits_status": db_property.building_limits_status,
        "building_distance_from_road": db_property.building_distance_from_road,
        "building_plan_approved": db_property.building_plan_approved,
        "building_plan_reference": db_property.building_plan_reference,
        "building_approval_authority": db_property.building_approval_authority,
        "building_within_limits": db_property.building_within_limits,
        "local_authority_data": db_property.local_authority_data,
        "local_authority_rated": db_property.local_authority_rated,
        "local_authority_tax_levy": db_property.local_authority_tax_levy,
        "rent_act_effectiveness": db_property.rent_act_effectiveness,
        "title_search_conducted": db_property.title_search_conducted,
        "pedigree_search_conducted": db_property.pedigree_search_conducted,
        "valuation_basis_note": db_property.valuation_basis_note,
        "property_encumbered": db_property.property_encumbered,
        "encumbrance_type": db_property.encumbrance_type,
        "encumbrance_details": db_property.encumbrance_details,
        "comparable_properties": db_property.comparable_properties,
        "land_market_analysis": db_property.land_market_analysis,
        "valuation_land_extent": db_property.valuation_land_extent,
        "valuation_rate_per_perch": db_property.valuation_rate_per_perch,
        "valuation_total_land_value": db_property.valuation_total_land_value,
        "valuation_buildings_data": db_property.valuation_buildings_data,
        "valuation_total_buildings_value": db_property.valuation_total_buildings_value,
        "valuation_addons": db_property.valuation_addons,
        "valuation_total_addons_value": db_property.valuation_total_addons_value,
        "valuation_market_value": db_property.valuation_market_value,
        "valuation_forced_sale_percentage": db_property.valuation_forced_sale_percentage,
        "valuation_forced_sale_value": db_property.valuation_forced_sale_value,
        "valuation_insurance_value": db_property.valuation_insurance_value,
        "valuation_manual_overrides": db_property.valuation_manual_overrides,
        "property_owner_title": db_property.property_owner_title,
        "property_owner_full_name": db_property.property_owner_full_name,
        "property_owner_id_type": db_property.property_owner_id_type,
        "property_owner_id_number": db_property.property_owner_id_number,
        "has_additional_owner": db_property.has_additional_owner,
        "additional_owner_names": db_property.additional_owner_names,
        "inspection_date": db_property.inspection_date,
        "uploaded_documents": db_property.uploaded_documents,
        "field_sources": db_property.field_sources,
        "survey_plan_scale": db_property.survey_plan_scale,
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
    Create a multi-property report with proper transaction handling.

    Can either link to existing properties (property_ids) or create new ones (properties).

    Transaction Safety: The entire operation is wrapped in try/except with proper
    rollback to ensure atomic operation - either all changes succeed or none do.
    """
    try:
        # Extract property-related data
        property_ids = list(report_data.property_ids or [])  # Copy to avoid modifying original
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

    except Exception as e:
        # Rollback entire transaction on any error to prevent partial state
        db.rollback()
        raise

def _update_report_total_valuation(db: Session, db_report: models.Report):
    """
    Recalculate total valuation for a report.

    Uses joinedload to efficiently load property data in a single query,
    avoiding N+1 query performance issues.
    Uses SELECT FOR UPDATE to prevent race conditions when concurrent
    updates modify property valuations.
    """
    from sqlalchemy.orm import joinedload

    # Query report properties with joined property data (single query)
    # Lock rows to prevent race conditions
    report_properties = (
        db.query(models.ReportProperty)
        .options(joinedload(models.ReportProperty.property))
        .filter(models.ReportProperty.report_id == db_report.id)
        .with_for_update()
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

# ===== VEHICLE CRUD OPERATIONS =====

def create_vehicle(db: Session, vehicle: schemas.VehicleCreate, user_id: int):
    """Create a new vehicle for a user"""
    db_vehicle = models.Vehicle(**vehicle.model_dump(), user_id=user_id)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def get_vehicle(db: Session, vehicle_id: int, user_id: int = None):
    """Get vehicle by ID, optionally filtered by user_id"""
    query = db.query(models.Vehicle).filter(
        models.Vehicle.id == vehicle_id,
        models.Vehicle.is_deleted == False
    )
    if user_id:
        query = query.filter(models.Vehicle.user_id == user_id)
    return query.first()


def get_user_vehicles(db: Session, user_id: int, skip: int = 0, limit: int = 100, include_deleted: bool = False):
    """Get all vehicles for a specific user"""
    query = db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id)
    if not include_deleted:
        query = query.filter(models.Vehicle.is_deleted == False)
    return query.order_by(models.Vehicle.created_at.desc()).offset(skip).limit(limit).all()


def get_vehicle_templates(db: Session, user_id: int):
    """Get all vehicle templates (Vehicle Library) for a user"""
    return db.query(models.Vehicle).filter(
        models.Vehicle.user_id == user_id,
        models.Vehicle.is_template == True,
        models.Vehicle.is_deleted == False
    ).order_by(models.Vehicle.make, models.Vehicle.model).all()


def update_vehicle(db: Session, vehicle_id: int, vehicle_update: schemas.VehicleUpdate, user_id: int = None):
    """Update a vehicle"""
    query = db.query(models.Vehicle).filter(
        models.Vehicle.id == vehicle_id,
        models.Vehicle.is_deleted == False
    )
    if user_id:
        query = query.filter(models.Vehicle.user_id == user_id)

    db_vehicle = query.first()
    if not db_vehicle:
        return None

    update_data = vehicle_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)

    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def delete_vehicle(db: Session, vehicle_id: int, user_id: int = None, soft_delete: bool = True):
    """Delete a vehicle (soft delete by default)"""
    query = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id)
    if user_id:
        query = query.filter(models.Vehicle.user_id == user_id)

    db_vehicle = query.first()
    if not db_vehicle:
        return False

    # Check if vehicle is used in any reports
    usage_count = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.vehicle_id == vehicle_id
    ).count()

    if usage_count > 0 and not soft_delete:
        raise ValueError(
            f"Cannot permanently delete vehicle. It is used in {usage_count} report(s). "
            "Use soft delete instead."
        )

    if soft_delete:
        db_vehicle.is_deleted = True
        db.commit()
    else:
        db.delete(db_vehicle)
        db.commit()

    return True


def duplicate_vehicle(db: Session, vehicle_id: int, user_id: int):
    """Duplicate a vehicle (create a copy)"""
    original = get_vehicle(db, vehicle_id, user_id)
    if not original:
        return None

    # Create a copy with key fields
    vehicle_data = {
        'status': 'draft',
        'vehicle_type': original.vehicle_type,
        'is_template': False,  # Copies are not templates
        'registration_number': original.registration_number,
        'provincial_council': original.provincial_council,
        'class_of_vehicle': original.class_of_vehicle,
        'body_colour': original.body_colour,
        'chassis_number': original.chassis_number,
        'engine_number': original.engine_number,
        'vehicle_status': original.vehicle_status,
        'country_of_origin': original.country_of_origin,
        'make': original.make,
        'model': original.model,
        'date_of_first_registration': original.date_of_first_registration,
        'year_of_manufacture': original.year_of_manufacture,
        'cylinder_capacity': original.cylinder_capacity,
        'fuel_type': original.fuel_type,
        'mileage': original.mileage,
        'mileage_unit': original.mileage_unit,
        'engine_type': original.engine_type,
        'transmission': original.transmission,
        'wheel_drive': original.wheel_drive,
        'running_condition': original.running_condition,
        'clutch_status': original.clutch_status,
        'engine_condition': original.engine_condition,
        'gear_box_condition': original.gear_box_condition,
        'differential_status': original.differential_status,
        'gear_selection': original.gear_selection,
        'body_condition': original.body_condition,
        'chassis_condition': original.chassis_condition,
        'upholstery_condition': original.upholstery_condition,
        'underside_condition': original.underside_condition,
        'body_parts_status': original.body_parts_status,
        'engine_parts_status': original.engine_parts_status,
        'accessories_status': original.accessories_status,
        'fuel_consumption': original.fuel_consumption,
        'fuel_consumption_unit': original.fuel_consumption_unit,
        'foot_brake_condition': original.foot_brake_condition,
        'disc_brake_available': original.disc_brake_available,
        'parking_brake_condition': original.parking_brake_condition,
        'abs_available': original.abs_available,
        'features': original.features,
        'suspension': original.suspension,
        'tyres': original.tyres,
        'electrical': original.electrical,
        'lights': original.lights,
        'has_accidents': original.has_accidents,
        'has_repairs': original.has_repairs,
        'needs_repairs_within_year': original.needs_repairs_within_year,
        'body_parts_replaced': original.body_parts_replaced,
        'purchase_price': original.purchase_price,
        'brand_new_price': original.brand_new_price,
        'market_value': original.market_value,
        'forced_sale_value': original.forced_sale_value,
        'valuation_summary': original.valuation_summary,
        'office_data': original.office_data,
        'past_valuations': original.past_valuations,
        'vehicle_photos': original.vehicle_photos,
        'book_images': original.book_images,
        'original_vehicle_id': original.id,  # Track original
    }

    new_vehicle = models.Vehicle(**vehicle_data, user_id=user_id)
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


# ===== REPORT-VEHICLE JUNCTION OPERATIONS =====

def add_vehicle_to_report(db: Session, report_id: int, vehicle_id: int, user_id: int, vehicle_order: int = None):
    """Add an existing vehicle to a report"""
    # Verify user owns both report and vehicle
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    db_vehicle = get_vehicle(db, vehicle_id, user_id)
    if not db_vehicle:
        raise ValueError("Vehicle not found or access denied")

    # Check if vehicle is already in this report
    existing = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id,
        models.ReportVehicle.vehicle_id == vehicle_id
    ).first()
    if existing:
        raise ValueError("Vehicle is already in this report")

    # Determine vehicle order
    if vehicle_order is None:
        max_order = db.query(models.ReportVehicle).filter(
            models.ReportVehicle.report_id == report_id
        ).count()
        vehicle_order = max_order + 1

    # Create association
    report_vehicle = models.ReportVehicle(
        report_id=report_id,
        vehicle_id=vehicle_id,
        vehicle_order=vehicle_order
    )
    db.add(report_vehicle)
    db.flush()

    # Update report metadata
    new_count = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id
    ).count()
    db_report.vehicle_count = new_count

    # Recalculate total valuation including vehicles
    _update_report_total_valuation_with_vehicles(db, db_report)

    db.commit()
    db.refresh(report_vehicle)
    return report_vehicle


def remove_vehicle_from_report(db: Session, report_id: int, vehicle_id: int, user_id: int):
    """Remove a vehicle from a report"""
    # Verify user owns the report
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    # Find the association
    report_vehicle = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id,
        models.ReportVehicle.vehicle_id == vehicle_id
    ).first()

    if not report_vehicle:
        raise ValueError("Vehicle is not in this report")

    db.delete(report_vehicle)
    db.flush()

    # Update report metadata
    new_count = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id
    ).count()
    db_report.vehicle_count = new_count

    # Recalculate total valuation
    _update_report_total_valuation_with_vehicles(db, db_report)

    db.commit()
    return True


def reorder_report_vehicles(db: Session, report_id: int, vehicle_order_map: dict, user_id: int):
    """
    Reorder vehicles in a report
    vehicle_order_map: {vehicle_id: new_order, ...}
    """
    # Verify user owns the report
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    # Update each vehicle's order
    for vehicle_id, new_order in vehicle_order_map.items():
        report_vehicle = db.query(models.ReportVehicle).filter(
            models.ReportVehicle.report_id == report_id,
            models.ReportVehicle.vehicle_id == vehicle_id
        ).first()

        if report_vehicle:
            report_vehicle.vehicle_order = new_order

    db.commit()
    return True


def get_report_vehicles(db: Session, report_id: int):
    """Get all vehicles for a report, ordered by vehicle_order"""
    return db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id
    ).order_by(models.ReportVehicle.vehicle_order).all()


def _update_report_total_valuation_with_vehicles(db: Session, db_report: models.Report):
    """Helper function to recalculate total valuation including vehicles"""
    total = 0

    # Sum property values
    report_properties = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == db_report.id
    ).all()

    for rp in report_properties:
        if rp.override_market_value is not None:
            total += float(rp.override_market_value)
        else:
            prop = db.query(models.Property).filter(
                models.Property.id == rp.property_id
            ).first()
            if prop and prop.valuation_market_value is not None:
                total += float(prop.valuation_market_value)

    # Sum vehicle values
    report_vehicles = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == db_report.id
    ).all()

    for rv in report_vehicles:
        if rv.override_market_value is not None:
            total += float(rv.override_market_value)
        else:
            vehicle = db.query(models.Vehicle).filter(
                models.Vehicle.id == rv.vehicle_id
            ).first()
            if vehicle and vehicle.market_value is not None:
                total += float(vehicle.market_value)

    db_report.total_valuation_amount = total if total > 0 else None


# Legacy functions removed for clean v0.1 implementation
# All functionality moved to authenticated user + report system
