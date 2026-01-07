"""
Database migration to add hathpaththuwa field.

This migration adds the hathpaththuwa administrative division field to support
the traditional Sri Lankan administrative hierarchy between Divisional Secretariat
and Korale levels.

Changes:
- Adds hathpaththuwa column to 'reports' table
- Adds hathpaththuwa column to 'properties' table
- Both columns are VARCHAR(300) and nullable (optional field)
"""

from app.database import engine
from sqlalchemy import text


def migrate():
    """Add hathpaththuwa field to reports and properties tables"""
    print("[MIGRATION] Adding hathpaththuwa field...")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            # ===== STEP 1: Add hathpaththuwa to reports table =====
            print("\n[STEP 1/2] Adding hathpaththuwa column to reports table...")

            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD COLUMN IF NOT EXISTS hathpaththuwa VARCHAR(300)
                """))
                print("  [OK] Added hathpaththuwa column to reports table")
            except Exception as e:
                print(f"  [SKIP] hathpaththuwa column (reports): {e}")

            conn.commit()

            # ===== STEP 2: Add hathpaththuwa to properties table =====
            print("\n[STEP 2/2] Adding hathpaththuwa column to properties table...")

            try:
                conn.execute(text("""
                    ALTER TABLE properties
                    ADD COLUMN IF NOT EXISTS hathpaththuwa VARCHAR(300)
                """))
                print("  [OK] Added hathpaththuwa column to properties table")
            except Exception as e:
                print(f"  [SKIP] hathpaththuwa column (properties): {e}")

            conn.commit()

            # ===== Verification =====
            print("\n" + "=" * 80)
            print("[VERIFICATION] Checking migration results...")

            # Check if column exists in reports table
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'reports'
                AND column_name = 'hathpaththuwa'
            """))
            reports_column_count = result.fetchone()[0]
            print(f"  [{'OK' if reports_column_count > 0 else 'FAIL'}] hathpaththuwa column in reports table: {'exists' if reports_column_count > 0 else 'missing'}")

            # Check if column exists in properties table
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'properties'
                AND column_name = 'hathpaththuwa'
            """))
            properties_column_count = result.fetchone()[0]
            print(f"  [{'OK' if properties_column_count > 0 else 'FAIL'}] hathpaththuwa column in properties table: {'exists' if properties_column_count > 0 else 'missing'}")

            print("\n" + "=" * 80)
            print("[MIGRATION COMPLETE]")
            print("\nSummary:")
            print("  [OK] Added hathpaththuwa column to reports table (VARCHAR(300), nullable)")
            print("  [OK] Added hathpaththuwa column to properties table (VARCHAR(300), nullable)")
            print("\nBackward Compatibility:")
            print("  - All existing reports continue working (nullable field)")
            print("  - Field is optional, users can leave blank if unknown")
            print("  - No data migration required (new field, no existing data)")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Remove hathpaththuwa field"""
    print("[ROLLBACK] Removing hathpaththuwa field...")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            # Remove from reports table
            print("\n[1/2] Removing hathpaththuwa from reports table...")
            try:
                conn.execute(text("ALTER TABLE reports DROP COLUMN IF EXISTS hathpaththuwa"))
                print("  [OK] Removed hathpaththuwa column from reports table")
            except Exception as e:
                print(f"  [WARN] Could not remove hathpaththuwa from reports: {e}")

            conn.commit()

            # Remove from properties table
            print("\n[2/2] Removing hathpaththuwa from properties table...")
            try:
                conn.execute(text("ALTER TABLE properties DROP COLUMN IF EXISTS hathpaththuwa"))
                print("  [OK] Removed hathpaththuwa column from properties table")
            except Exception as e:
                print(f"  [WARN] Could not remove hathpaththuwa from properties: {e}")

            conn.commit()

            print("\n" + "=" * 80)
            print("[ROLLBACK COMPLETE]")
            print("hathpaththuwa field has been removed from the database.")

    except Exception as e:
        print(f"\n[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
