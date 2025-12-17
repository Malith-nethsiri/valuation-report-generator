"""
Database migration to add performance indexes on frequently queried fields.

This migration adds indexes to improve query performance for common operations:
- Filtering reports by status, type, date
- Searching reports by user and status
- Location-based queries

Benefits:
- Faster query execution for filtered searches
- Improved dashboard loading times
- Better performance for location-based features
"""

from app.database import engine
from sqlalchemy import text


def migrate():
    """Add performance indexes to reports table"""
    print("[MIGRATION] Adding performance indexes to reports table...")

    try:
        with engine.connect() as conn:
            # 1. Single-column indexes
            print("[1/2] Creating single-column indexes...")

            # Index on report_type (for filtering by type)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_report_type
                    ON reports(report_type)
                """))
                print("  ✓ Created index: ix_reports_report_type")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_report_type: {e}")

            # Index on status (for filtering draft/completed)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_status
                    ON reports(status)
                """))
                print("  ✓ Created index: ix_reports_status")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_status: {e}")

            # Index on inspection_date (for date-based searches)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_inspection_date
                    ON reports(inspection_date)
                """))
                print("  ✓ Created index: ix_reports_inspection_date")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_inspection_date: {e}")

            # Index on created_at (for sorting by creation date)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_created_at
                    ON reports(created_at DESC)
                """))
                print("  ✓ Created index: ix_reports_created_at (DESC)")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_created_at: {e}")

            conn.commit()
            print("[OK] Single-column indexes created")

            # 2. Composite indexes
            print("\n[2/2] Creating composite indexes...")

            # Index on (user_id, status) for user's reports filtered by status
            # Most common query: "Get all draft/completed reports for user X"
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_user_status
                    ON reports(user_id, status)
                """))
                print("  ✓ Created composite index: ix_reports_user_status")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_user_status: {e}")

            # Index on (property_latitude, property_longitude) for location searches
            # Useful for: finding nearby properties, location-based analytics
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_property_location
                    ON reports(property_latitude, property_longitude)
                    WHERE property_latitude IS NOT NULL AND property_longitude IS NOT NULL
                """))
                print("  ✓ Created composite index: ix_reports_property_location (partial)")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_property_location: {e}")

            # Index on (user_id, created_at DESC) for user's recent reports
            # Useful for: dashboard "my recent reports"
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_reports_user_recent
                    ON reports(user_id, created_at DESC)
                """))
                print("  ✓ Created composite index: ix_reports_user_recent")
            except Exception as e:
                print(f"  ⊕ Index ix_reports_user_recent: {e}")

            conn.commit()
            print("[OK] Composite indexes created")

            # 3. Verify indexes
            print("\n[3/3] Verifying created indexes...")

            result = conn.execute(text("""
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = 'reports'
                AND indexname LIKE 'ix_reports_%'
                ORDER BY indexname
            """))

            indexes = result.fetchall()
            print(f"  ✓ Found {len(indexes)} performance indexes on reports table:")
            for name, definition in indexes:
                # Show index name and size
                size_result = conn.execute(text(f"""
                    SELECT pg_size_pretty(pg_relation_size('{name}'))
                """))
                size = size_result.fetchone()[0]
                print(f"    - {name} ({size})")

            # Calculate total indexes size
            result = conn.execute(text("""
                SELECT pg_size_pretty(SUM(pg_relation_size(indexname::regclass))::bigint)
                FROM pg_indexes
                WHERE tablename = 'reports'
                AND indexname LIKE 'ix_reports_%'
            """))
            total_size = result.fetchone()[0]

            print(f"\n  Total indexes size: {total_size}")

            print("\n[MIGRATION COMPLETE] ✅")
            print("Summary:")
            print("  - Created 4 single-column indexes (report_type, status, inspection_date, created_at)")
            print("  - Created 3 composite indexes (user_status, property_location, user_recent)")
            print("  - Queries filtering by these fields will be significantly faster")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Remove performance indexes from reports table"""
    print("[ROLLBACK] Removing performance indexes from reports table...")

    try:
        with engine.connect() as conn:
            indexes_to_drop = [
                "ix_reports_report_type",
                "ix_reports_status",
                "ix_reports_inspection_date",
                "ix_reports_created_at",
                "ix_reports_user_status",
                "ix_reports_property_location",
                "ix_reports_user_recent"
            ]

            for index_name in indexes_to_drop:
                try:
                    conn.execute(text(f"""
                        DROP INDEX IF EXISTS {index_name}
                    """))
                    print(f"  ✓ Dropped index: {index_name}")
                except Exception as e:
                    print(f"  ⚠ Could not drop {index_name}: {e}")

            conn.commit()
            print("\n[ROLLBACK COMPLETE] ✅")
            print("Warning: Queries will be slower without these indexes")

    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
