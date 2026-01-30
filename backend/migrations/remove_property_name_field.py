"""
Database migration to remove redundant property_name field.

This migration:
1. Migrates any existing property_name data to land_traditional_name (if land_traditional_name is empty)
2. Drops the property_name column from both reports and properties tables

Reason: property_name and land_traditional_name serve the same purpose (identifying the property/land name),
causing duplicate data entry. We're standardizing on land_traditional_name.
"""

from app.database import engine
from sqlalchemy import text
from datetime import datetime


def migrate():
    """Remove property_name field and migrate data to land_traditional_name"""
    print("[MIGRATION] Removing redundant property_name field...")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            # ===== STEP 1: Check current data =====
            print("\n[STEP 1/4] Analyzing existing data...")

            # Check reports table
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN property_name IS NOT NULL AND property_name != '' THEN 1 ELSE 0 END) as with_property_name,
                       SUM(CASE WHEN land_traditional_name IS NOT NULL AND land_traditional_name != '' THEN 1 ELSE 0 END) as with_land_name
                FROM reports
            """))
            row = result.fetchone()
            print(f"  Reports table: {row[0]} total, {row[1]} with property_name, {row[2]} with land_traditional_name")

            # Check properties table
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN property_name IS NOT NULL AND property_name != '' THEN 1 ELSE 0 END) as with_property_name,
                       SUM(CASE WHEN land_traditional_name IS NOT NULL AND land_traditional_name != '' THEN 1 ELSE 0 END) as with_land_name
                FROM properties
            """))
            row = result.fetchone()
            print(f"  Properties table: {row[0]} total, {row[1]} with property_name, {row[2]} with land_traditional_name")

            # ===== STEP 2: Migrate data from property_name to land_traditional_name =====
            print("\n[STEP 2/4] Migrating property_name data to land_traditional_name...")

            # Migrate reports table - only where land_traditional_name is empty
            result = conn.execute(text("""
                UPDATE reports
                SET land_traditional_name = property_name
                WHERE property_name IS NOT NULL
                  AND property_name != ''
                  AND (land_traditional_name IS NULL OR land_traditional_name = '')
            """))
            print(f"  Migrated {result.rowcount} records in reports table")

            # Migrate properties table - only where land_traditional_name is empty
            result = conn.execute(text("""
                UPDATE properties
                SET land_traditional_name = property_name
                WHERE property_name IS NOT NULL
                  AND property_name != ''
                  AND (land_traditional_name IS NULL OR land_traditional_name = '')
            """))
            print(f"  Migrated {result.rowcount} records in properties table")

            conn.commit()

            # ===== STEP 3: Show any records that had both fields populated =====
            print("\n[STEP 3/4] Checking for records with both fields populated...")

            result = conn.execute(text("""
                SELECT id, property_name, land_traditional_name
                FROM reports
                WHERE property_name IS NOT NULL
                  AND property_name != ''
                  AND land_traditional_name IS NOT NULL
                  AND land_traditional_name != ''
                LIMIT 10
            """))
            conflicts = result.fetchall()
            if conflicts:
                print(f"  Found {len(conflicts)} reports with both fields (land_traditional_name kept):")
                for row in conflicts:
                    print(f"    Report {row[0]}: property_name='{row[1]}', land_traditional_name='{row[2]}'")
            else:
                print("  No conflicts found - all data migrated cleanly")

            # ===== STEP 4: Create backup tables before destructive operations =====
            print("\n[STEP 4/6] Creating backup tables before column drop...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Backup reports table
            try:
                backup_table_reports = f"reports_backup_{timestamp}"
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {backup_table_reports} AS
                    SELECT id, property_name, land_traditional_name
                    FROM reports
                    WHERE property_name IS NOT NULL
                """))
                result = conn.execute(text(f"SELECT COUNT(*) FROM {backup_table_reports}"))
                count = result.fetchone()[0]
                print(f"  [OK] Created backup table '{backup_table_reports}' with {count} rows")
            except Exception as e:
                print(f"  [WARNING] Could not create reports backup: {e}")

            # Backup properties table
            try:
                backup_table_props = f"properties_backup_{timestamp}"
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {backup_table_props} AS
                    SELECT id, property_name, land_traditional_name
                    FROM properties
                    WHERE property_name IS NOT NULL
                """))
                result = conn.execute(text(f"SELECT COUNT(*) FROM {backup_table_props}"))
                count = result.fetchone()[0]
                print(f"  [OK] Created backup table '{backup_table_props}' with {count} rows")
            except Exception as e:
                print(f"  [WARNING] Could not create properties backup: {e}")

            conn.commit()

            # ===== STEP 5: Drop the property_name column =====
            print("\n[STEP 5/6] Dropping property_name column...")

            # Drop from reports table
            try:
                conn.execute(text("ALTER TABLE reports DROP COLUMN IF EXISTS property_name"))
                print("  [OK] Dropped property_name from reports table")
            except Exception as e:
                print(f"  [ERROR] Could not drop from reports: {e}")

            # Drop from properties table
            try:
                conn.execute(text("ALTER TABLE properties DROP COLUMN IF EXISTS property_name"))
                print("  [OK] Dropped property_name from properties table")
            except Exception as e:
                print(f"  [ERROR] Could not drop from properties: {e}")

            conn.commit()

            # ===== STEP 6: Verify and log backup information =====
            print(f"\n[STEP 6/6] Migration complete. Backup tables created:")
            print(f"  - {backup_table_reports}")
            print(f"  - {backup_table_props}")
            print(f"  To restore data, run: python remove_property_name_field.py rollback {timestamp}")

            print("\n" + "=" * 80)
            print("[MIGRATION] property_name removal completed successfully!")
            print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        raise


def rollback(timestamp: str = None):
    """
    Rollback: Re-add property_name column and restore data from backup.

    Args:
        timestamp: The timestamp suffix of backup tables (e.g., '20240115_120000').
                   If not provided, will list available backups.
    """
    print("[ROLLBACK] Re-adding property_name column...")

    try:
        with engine.connect() as conn:
            # List available backup tables if no timestamp provided
            if not timestamp:
                print("\n  Available backup tables:")
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name LIKE 'reports_backup_%' OR table_name LIKE 'properties_backup_%'
                    ORDER BY table_name DESC
                """))
                tables = result.fetchall()
                if tables:
                    for row in tables:
                        print(f"    - {row[0]}")
                    print("\n  To restore, run: python remove_property_name_field.py rollback <timestamp>")
                    print("  Example: python remove_property_name_field.py rollback 20240115_120000")
                else:
                    print("    No backup tables found")
                return

            backup_table_reports = f"reports_backup_{timestamp}"
            backup_table_props = f"properties_backup_{timestamp}"

            # Add back to reports table
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS property_name VARCHAR(200)
            """))
            print("  [OK] Re-added property_name to reports table")

            # Add back to properties table
            conn.execute(text("""
                ALTER TABLE properties
                ADD COLUMN IF NOT EXISTS property_name VARCHAR(200)
            """))
            print("  [OK] Re-added property_name to properties table")

            # Restore data from backup tables
            try:
                conn.execute(text(f"""
                    UPDATE reports r
                    SET property_name = b.property_name
                    FROM {backup_table_reports} b
                    WHERE r.id = b.id
                """))
                print(f"  [OK] Restored property_name data to reports from {backup_table_reports}")
            except Exception as e:
                print(f"  [WARNING] Could not restore reports data: {e}")

            try:
                conn.execute(text(f"""
                    UPDATE properties p
                    SET property_name = b.property_name
                    FROM {backup_table_props} b
                    WHERE p.id = b.id
                """))
                print(f"  [OK] Restored property_name data to properties from {backup_table_props}")
            except Exception as e:
                print(f"  [WARNING] Could not restore properties data: {e}")

            conn.commit()
            print("[ROLLBACK] Completed successfully with data restored")

    except Exception as e:
        print(f"[ROLLBACK ERROR] {str(e)}")
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        timestamp = sys.argv[2] if len(sys.argv) > 2 else None
        rollback(timestamp)
    else:
        migrate()
