"""
Migration: Rename property_lot_description to lot_number

This migration copies property_lot_description to lot_number for all reports and properties
where lot_number is empty but property_lot_description exists.

After running this migration:
1. All reports and properties will use lot_number field
2. property_lot_description is deprecated but kept for backward compatibility
3. Full audit trail is logged for all changes

Usage:
    Run via admin endpoint: POST /api/admin/migrate-lot-description
    Or run directly: python -m backend.migrations.migrate_lot_description_to_lot_number
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def migrate_report_lot_field(report_data: Dict) -> tuple[Dict, bool]:
    """
    Migrate lot field from property_lot_description to lot_number for a report.

    Logic:
    - If lot_number is empty but property_lot_description exists, copy it
    - Preserve original property_lot_description for backward compatibility

    Args:
        report_data: Report dict with lot fields

    Returns:
        Tuple of (updated report dict, whether changes were made)
    """
    updates_made = False
    old_value = None

    # Migrate lot_number
    if not report_data.get('lot_number') and report_data.get('property_lot_description'):
        old_value = report_data.get('property_lot_description')
        report_data['lot_number'] = old_value
        updates_made = True
        logger.info(
            f"Report {report_data.get('id')}: "
            f"Migrated property_lot_description '{old_value}' to lot_number"
        )

    return report_data, updates_made


def migrate_property_lot_field(property_data: Dict) -> tuple[Dict, bool]:
    """
    Migrate lot field from property_lot_description to lot_number for a property.

    Logic:
    - If lot_number is empty but property_lot_description exists, copy it
    - Preserve original property_lot_description for backward compatibility

    Args:
        property_data: Property dict with lot fields

    Returns:
        Tuple of (updated property dict, whether changes were made)
    """
    updates_made = False
    old_value = None

    # Migrate lot_number
    if not property_data.get('lot_number') and property_data.get('property_lot_description'):
        old_value = property_data.get('property_lot_description')
        property_data['lot_number'] = old_value
        updates_made = True
        logger.info(
            f"Property {property_data.get('id')}: "
            f"Migrated property_lot_description '{old_value}' to lot_number"
        )

    return property_data, updates_made


def get_migration_stats(item_data: Dict) -> Dict:
    """
    Get statistics about what would be migrated for a report or property.

    Args:
        item_data: Report or Property dict

    Returns:
        Dict with migration statistics
    """
    stats = {
        'has_property_lot_description': bool(item_data.get('property_lot_description')),
        'has_lot_number': bool(item_data.get('lot_number')),
        'needs_lot_migration': (
            not item_data.get('lot_number') and
            bool(item_data.get('property_lot_description'))
        ),
        'property_lot_description_value': item_data.get('property_lot_description'),
        'lot_number_value': item_data.get('lot_number'),
    }

    return stats


def migrate_all_reports(db_session) -> Dict:
    """
    Migrate all reports in the database.

    This function copies property_lot_description to lot_number for all reports.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        Dict with migration statistics, audit trail, and success status
    """
    from app.models import Report

    reports = db_session.query(Report).all()
    total = len(reports)
    migrated = 0
    skipped = 0
    audit_trail = []

    logger.info(f"Starting migration of {total} reports...")

    for report in reports:
        # Convert to dict for migration function
        report_dict = {
            'id': report.id,
            'property_lot_description': report.property_lot_description,
            'lot_number': report.lot_number if hasattr(report, 'lot_number') else None,
        }

        stats = get_migration_stats(report_dict)

        if stats['needs_lot_migration']:
            old_value = report.property_lot_description

            # Perform migration
            migrated_dict, updates_made = migrate_report_lot_field(report_dict)

            if updates_made:
                # Apply changes to database
                report.lot_number = migrated_dict['lot_number']

                # Record in audit trail
                audit_trail.append({
                    'type': 'report',
                    'id': report.id,
                    'field': 'lot_number',
                    'old_value': None,
                    'new_value': migrated_dict['lot_number'],
                    'source_field': 'property_lot_description',
                    'source_value': old_value,
                    'timestamp': datetime.now().isoformat()
                })

                migrated += 1
        else:
            skipped += 1

    db_session.commit()

    logger.info(f"Reports migration complete: {migrated}/{total} updated, {skipped} skipped")

    return {
        'total_reports': total,
        'migrated_reports': migrated,
        'skipped_reports': skipped,
        'audit_trail': audit_trail,
        'success': True
    }


def migrate_all_properties(db_session) -> Dict:
    """
    Migrate all properties in the database.

    This function copies property_lot_description to lot_number for all properties
    in multi-property reports.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        Dict with migration statistics, audit trail, and success status
    """
    from app.models import Property

    properties = db_session.query(Property).all()
    total = len(properties)
    migrated = 0
    skipped = 0
    audit_trail = []

    logger.info(f"Starting migration of {total} properties...")

    for prop in properties:
        # Convert to dict for migration function
        property_dict = {
            'id': prop.id,
            'property_lot_description': prop.property_lot_description,
            'lot_number': prop.lot_number if hasattr(prop, 'lot_number') else None,
        }

        stats = get_migration_stats(property_dict)

        if stats['needs_lot_migration']:
            old_value = prop.property_lot_description

            # Perform migration
            migrated_dict, updates_made = migrate_property_lot_field(property_dict)

            if updates_made:
                # Apply changes to database
                prop.lot_number = migrated_dict['lot_number']

                # Record in audit trail
                audit_trail.append({
                    'type': 'property',
                    'id': prop.id,
                    'field': 'lot_number',
                    'old_value': None,
                    'new_value': migrated_dict['lot_number'],
                    'source_field': 'property_lot_description',
                    'source_value': old_value,
                    'timestamp': datetime.now().isoformat()
                })

                migrated += 1
        else:
            skipped += 1

    db_session.commit()

    logger.info(f"Properties migration complete: {migrated}/{total} updated, {skipped} skipped")

    return {
        'total_properties': total,
        'migrated_properties': migrated,
        'skipped_properties': skipped,
        'audit_trail': audit_trail,
        'success': True
    }


def migrate_all(db_session) -> Dict:
    """
    Migrate all reports and properties in the database.

    This is the main entry point for the migration.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        Dict with combined migration statistics and audit trail
    """
    logger.info("=" * 80)
    logger.info("Starting lot_description -> lot_number migration")
    logger.info("=" * 80)

    # Migrate reports
    reports_result = migrate_all_reports(db_session)

    # Migrate properties
    properties_result = migrate_all_properties(db_session)

    # Combine audit trails
    combined_audit_trail = (
        reports_result.get('audit_trail', []) +
        properties_result.get('audit_trail', [])
    )

    # Log audit summary
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION AUDIT TRAIL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total items migrated: {len(combined_audit_trail)}")
    logger.info(f"  - Reports: {reports_result['migrated_reports']}")
    logger.info(f"  - Properties: {properties_result['migrated_properties']}")
    logger.info("=" * 80)

    # Write audit trail to file
    audit_file_path = f"migration_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(audit_file_path, 'w') as f:
        f.write("LOT_DESCRIPTION -> LOT_NUMBER MIGRATION AUDIT TRAIL\n")
        f.write("=" * 80 + "\n")
        f.write(f"Migration Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Records Migrated: {len(combined_audit_trail)}\n")
        f.write("=" * 80 + "\n\n")

        for entry in combined_audit_trail:
            f.write(f"Type: {entry['type'].upper()}\n")
            f.write(f"ID: {entry['id']}\n")
            f.write(f"Field: {entry['field']}\n")
            f.write(f"Source: {entry['source_field']} = '{entry['source_value']}'\n")
            f.write(f"New Value: {entry['new_value']}\n")
            f.write(f"Timestamp: {entry['timestamp']}\n")
            f.write("-" * 80 + "\n")

    logger.info(f"Audit trail written to: {audit_file_path}")

    return {
        'success': True,
        'reports': reports_result,
        'properties': properties_result,
        'total_migrated': len(combined_audit_trail),
        'audit_trail': combined_audit_trail,
        'audit_file': audit_file_path
    }


if __name__ == '__main__':
    """
    Run migration directly from command line.

    Usage:
        python -m backend.migrations.migrate_lot_description_to_lot_number
    """
    import sys
    from pathlib import Path

    # Add backend directory to path
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))

    from app.database import SessionLocal

    print("=" * 80)
    print("LOT_DESCRIPTION -> LOT_NUMBER MIGRATION")
    print("=" * 80)
    print("\nThis migration will:")
    print("1. Copy property_lot_description -> lot_number for all reports")
    print("2. Copy property_lot_description -> lot_number for all properties")
    print("3. Keep property_lot_description for backward compatibility")
    print("4. Create a full audit trail of all changes")
    print("\n" + "=" * 80)

    confirm = input("\nProceed with migration? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    db = SessionLocal()
    try:
        result = migrate_all(db)

        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"Reports migrated: {result['reports']['migrated_reports']}/{result['reports']['total_reports']}")
        print(f"Properties migrated: {result['properties']['migrated_properties']}/{result['properties']['total_properties']}")
        print(f"Total records updated: {result['total_migrated']}")
        print(f"Audit file: {result['audit_file']}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"\nERROR: Migration failed - {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
