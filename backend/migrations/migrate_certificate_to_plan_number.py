"""
Migration: Consolidate certificate_survey_plan_ref to plan_number

This migration copies certificate_survey_plan_ref to plan_number for all reports
where plan_number is empty but certificate_survey_plan_ref exists.

After running this migration:
1. All reports will use plan_number for Certificate of Identity
2. certificate_survey_plan_ref fields can be safely removed from database

Usage:
    Run via admin endpoint: POST /api/admin/migrate-certificate-fields
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def migrate_report_certificate_fields(report_data: Dict) -> Dict:
    """
    Migrate certificate fields from report-level to property-level plan fields.

    Logic:
    - If plan_number is empty but certificate_survey_plan_ref exists, copy it
    - If plan_date is empty but certificate_survey_plan_date exists, copy it
    - Preserve original certificate_survey_plan_ref for safety (will be removed in schema later)

    Args:
        report_data: Report dict with certificate and plan fields

    Returns:
        Updated report dict with migrated fields
    """
    updates_made = False

    # Migrate plan_number
    if not report_data.get('plan_number') and report_data.get('certificate_survey_plan_ref'):
        report_data['plan_number'] = report_data['certificate_survey_plan_ref']
        updates_made = True
        logger.info(f"Migrated certificate_survey_plan_ref to plan_number: {report_data['plan_number']}")

    # Migrate plan_date
    if not report_data.get('plan_date') and report_data.get('certificate_survey_plan_date'):
        report_data['plan_date'] = report_data['certificate_survey_plan_date']
        updates_made = True
        logger.info(f"Migrated certificate_survey_plan_date to plan_date: {report_data['plan_date']}")

    if updates_made:
        logger.info(f"Successfully migrated certificate fields for report")

    return report_data


def get_migration_stats(report_data: Dict) -> Dict:
    """
    Get statistics about what would be migrated.

    Args:
        report_data: Report dict

    Returns:
        Dict with migration statistics
    """
    stats = {
        'has_certificate_survey_plan_ref': bool(report_data.get('certificate_survey_plan_ref')),
        'has_plan_number': bool(report_data.get('plan_number')),
        'needs_plan_number_migration': (
            not report_data.get('plan_number') and
            bool(report_data.get('certificate_survey_plan_ref'))
        ),
        'has_certificate_survey_plan_date': bool(report_data.get('certificate_survey_plan_date')),
        'has_plan_date': bool(report_data.get('plan_date')),
        'needs_plan_date_migration': (
            not report_data.get('plan_date') and
            bool(report_data.get('certificate_survey_plan_date'))
        ),
    }

    return stats


def migrate_all_reports(db_session):
    """
    Migrate all reports in the database.

    This function should be called from an admin endpoint.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        Dict with migration statistics and success status
    """
    from ..models import Report

    reports = db_session.query(Report).all()
    total = len(reports)
    migrated = 0

    logger.info(f"Starting migration of {total} reports...")

    for report in reports:
        # Convert to dict for migration function
        report_dict = {
            'id': report.id,
            'certificate_survey_plan_ref': report.certificate_survey_plan_ref,
            'certificate_survey_plan_date': report.certificate_survey_plan_date,
            'plan_number': report.plan_number,
            'plan_date': report.plan_date,
        }

        stats = get_migration_stats(report_dict)

        if stats['needs_plan_number_migration'] or stats['needs_plan_date_migration']:
            migrated_dict = migrate_report_certificate_fields(report_dict)

            # Apply changes to database
            if migrated_dict['plan_number'] != report.plan_number:
                report.plan_number = migrated_dict['plan_number']
            if migrated_dict['plan_date'] != report.plan_date:
                report.plan_date = migrated_dict['plan_date']

            migrated += 1

    db_session.commit()

    logger.info(f"Migration complete: {migrated}/{total} reports updated")

    return {
        'total_reports': total,
        'migrated_reports': migrated,
        'skipped_reports': total - migrated,
        'success': True
    }
