"""
Report CRUD operations.

Includes report-property association reads used by duplicate_report.
"""
import logging
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, schemas
from .building_helpers import _normalize_and_validate_buildings, _duplicate_entity_data

logger = logging.getLogger(__name__)


def create_report(db: Session, report: schemas.ReportCreate, user_id: int):
    """Create a new report for a user"""
    _normalize_and_validate_buildings(report.buildings)
    db_report = models.Report(**report.model_dump(), user_id=user_id)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def get_report(db: Session, report_id: int, user_id: int = None,
               eager_load_for_docx: bool = False):
    """Get report by ID, optionally filtered by user_id.

    Args:
        eager_load_for_docx: If True, eagerly loads relationships needed for DOCX generation
    """
    from sqlalchemy.orm import joinedload

    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)

    if eager_load_for_docx:
        query = query.options(
            joinedload(models.Report.user),
            joinedload(models.Report.primary_vehicle),
            joinedload(models.Report.property_associations).joinedload(models.ReportProperty.property),
            joinedload(models.Report.vehicle_associations).joinedload(models.ReportVehicle.vehicle),
        )

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
    """
    from sqlalchemy import func, and_, cast, Date
    from datetime import datetime, date

    base_query = db.query(models.Report).filter(models.Report.user_id == user_id)

    filters = []

    if reference:
        filters.append(models.Report.report_reference.ilike(f"%{reference}%"))

    if applicant_name:
        filters.append(models.Report.applicant_full_name.ilike(f"%{applicant_name}%"))

    if village:
        filters.append(models.Report.property_village.ilike(f"%{village}%"))

    if report_date:
        try:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
            filters.append(cast(models.Report.created_at, Date) == target_date)
        except ValueError:
            pass  # Invalid date format, ignore filter

    filtered_query = base_query
    if filters:
        filtered_query = base_query.filter(and_(*filters))

    total_count = filtered_query.count()

    reports = filtered_query.order_by(
        models.Report.created_at.desc()
    ).offset(skip).limit(limit).all()

    current_month = date.today().replace(day=1)
    stats_query = filtered_query

    this_month_count = stats_query.filter(models.Report.created_at >= current_month).count()
    completed_count = stats_query.filter(models.Report.status == 'completed').count()
    draft_count = stats_query.filter(models.Report.status == 'draft').count()

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
    Returns date string (YYYY-MM-DD) or None if no adjacent date found.
    """
    from sqlalchemy import cast, Date
    from datetime import datetime

    try:
        target_date = datetime.strptime(current_date, "%Y-%m-%d").date()
    except ValueError:
        return None

    if direction == "next":
        result = db.query(
            cast(models.Report.created_at, Date)
        ).filter(
            models.Report.user_id == user_id,
            cast(models.Report.created_at, Date) > target_date
        ).order_by(cast(models.Report.created_at, Date).asc()).first()
    else:  # previous
        result = db.query(
            cast(models.Report.created_at, Date)
        ).filter(
            models.Report.user_id == user_id,
            cast(models.Report.created_at, Date) < target_date
        ).order_by(cast(models.Report.created_at, Date).desc()).first()

    if result and result[0]:
        return result[0].strftime("%Y-%m-%d")
    return None


def get_all_reports(db: Session, skip: int = 0, limit: int = 100):
    """Get all reports (admin function)"""
    return db.query(models.Report).offset(skip).limit(limit).all()


def update_report(db: Session, report_id: int, report_update: schemas.ReportUpdate,
                  user_id: int = None, use_locking: bool = False):
    """Update a report.

    Args:
        use_locking: If True, uses SELECT FOR UPDATE to prevent race conditions.
                     When True, caller is responsible for committing the transaction.
    """
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)

    if use_locking:
        query = query.with_for_update()

    db_report = query.first()
    if not db_report:
        return None

    update_data = report_update.model_dump(exclude_unset=True)

    logger.info(f"[UPDATE_REPORT] Report ID: {report_id}, Fields in update: {list(update_data.keys())}")
    if 'buildings' in update_data:
        logger.info(f"[UPDATE_REPORT] Buildings data present: {len(update_data['buildings']) if update_data['buildings'] else 0} buildings")
    else:
        logger.info(f"[UPDATE_REPORT] Buildings data NOT in update")

    if 'valuation_buildings_data' in update_data:
        logger.info(f"[UPDATE_REPORT] Valuation buildings data present: {len(update_data['valuation_buildings_data']) if update_data['valuation_buildings_data'] else 0} items")
    else:
        logger.info(f"[UPDATE_REPORT] Valuation buildings data NOT in update")

    if 'buildings' in update_data and update_data['buildings']:
        _normalize_and_validate_buildings(update_data['buildings'])

    for field, value in update_data.items():
        setattr(db_report, field, value)

    if use_locking:
        db.flush()
    else:
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


def get_report_properties(db: Session, report_id: int):
    """Get all properties for a report, ordered by property_order"""
    return db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == report_id
    ).order_by(models.ReportProperty.property_order).all()


def duplicate_report(db: Session, report_id: int, user_id: int):
    """
    Duplicate an existing report as a new draft.

    Uses SQLAlchemy reflection to automatically copy all fields,
    ensuring new fields added to the Report model are included.
    """
    original_report = get_report(db, report_id, user_id)
    if not original_report:
        return None

    report_data = _duplicate_entity_data(
        original_report,
        exclude_fields={'id', 'created_at', 'updated_at'},
        override_fields={
            'status': 'draft',
            'report_reference': None,
            'report_date': None,
            'certification_text': None,
            'certification_date': None,
            'certification_valuer_name': None,
            'certification_valuer_designation': None,
            'certificate_identity_confirmed': False,
        }
    )

    new_report = models.Report(**report_data)
    db.add(new_report)
    db.flush()

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
