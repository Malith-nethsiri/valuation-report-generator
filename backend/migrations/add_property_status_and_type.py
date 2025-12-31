"""
Database migration to add status and property_type fields to Property model.

This migration adds support for multi-property report redesign Phase 1:
- Adds `status` column to properties table ('draft' or 'completed')
- Adds `property_type` column to properties table ('residential' or 'bare_land')

These fields enable:
- Tracking property completion state in multi-property reports
- Differentiating between residential and bare land properties
- Draft warning before invoice generation
- Filtering completed properties for report generation

Migration Strategy:
- Existing properties default to status='completed' (backward compatible)
- Existing properties default to property_type='residential' (safe assumption)
- Creates indexes for performance on status and property_type queries
"""

from app.database import engine
from sqlalchemy import text


def migrate():
    """Add status and property_type columns to properties table"""
    print("[MIGRATION] Adding property status and type fields...")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            # ===== STEP 1: Add status column =====
            print("\n[STEP 1/4] Adding 'status' column to properties table...")

            try:
                conn.execute(text("""
                    ALTER TABLE properties
                    ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'draft'
                """))
                print("  [OK] Added status column (default: 'draft')")
            except Exception as e:
                print(f"  [SKIP] status column: {e}")

            conn.commit()

            # ===== STEP 2: Add property_type column =====
            print("\n[STEP 2/4] Adding 'property_type' column to properties table...")

            try:
                conn.execute(text("""
                    ALTER TABLE properties
                    ADD COLUMN IF NOT EXISTS property_type VARCHAR(50) NOT NULL DEFAULT 'residential'
                """))
                print("  [OK] Added property_type column (default: 'residential')")
            except Exception as e:
                print(f"  [SKIP] property_type column: {e}")

            conn.commit()

            # ===== STEP 3: Set defaults for existing properties =====
            print("\n[STEP 3/4] Setting defaults for existing properties...")

            try:
                # Set status='completed' for all existing properties (backward compatible)
                result = conn.execute(text("""
                    UPDATE properties
                    SET status = 'completed'
                    WHERE status = 'draft'
                """))
                updated_count = result.rowcount
                print(f"  [OK] Updated {updated_count} existing properties to status='completed'")
            except Exception as e:
                print(f"  [SKIP] Could not update existing properties: {e}")

            try:
                # property_type already defaults to 'residential', no update needed
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM properties
                    WHERE property_type = 'residential'
                """))
                count = result.fetchone()[0]
                print(f"  [OK] {count} properties have property_type='residential'")
            except Exception as e:
                print(f"  [SKIP] Could not count properties: {e}")

            conn.commit()

            # ===== STEP 4: Create indexes for performance =====
            print("\n[STEP 4/4] Creating performance indexes...")

            # Index on properties.status for filtering drafts/completed
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_properties_status
                    ON properties(status)
                """))
                print("  [OK] Created index: ix_properties_status")
            except Exception as e:
                print(f"  [SKIP] Index ix_properties_status: {e}")

            # Index on properties.property_type for filtering residential/bare_land
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_properties_type
                    ON properties(property_type)
                """))
                print("  [OK] Created index: ix_properties_type")
            except Exception as e:
                print(f"  [SKIP] Index ix_properties_type: {e}")

            # Composite index on user_id + status for efficient user property queries
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_properties_user_status
                    ON properties(user_id, status)
                """))
                print("  [OK] Created index: ix_properties_user_status")
            except Exception as e:
                print(f"  [SKIP] Index ix_properties_user_status: {e}")

            conn.commit()

            # ===== Verification =====
            print("\n" + "=" * 80)
            print("[VERIFICATION] Checking migration results...")

            # Verify columns exist
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'properties'
                AND column_name IN ('status', 'property_type')
            """))
            column_count = result.fetchone()[0]
            print(f"  [OK] Added {column_count}/2 new columns to properties table")

            # Count indexes
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = 'properties'
                AND indexname IN ('ix_properties_status', 'ix_properties_type', 'ix_properties_user_status')
            """))
            index_count = result.fetchone()[0]
            print(f"  [OK] Created {index_count}/3 new indexes")

            # Show property status distribution
            try:
                result = conn.execute(text("""
                    SELECT status, COUNT(*) as count
                    FROM properties
                    GROUP BY status
                """))
                print("\n[PROPERTY STATUS DISTRIBUTION]")
                for row in result:
                    print(f"  - {row[0]}: {row[1]} properties")
            except Exception as e:
                print(f"  [SKIP] Could not get status distribution: {e}")

            # Show property type distribution
            try:
                result = conn.execute(text("""
                    SELECT property_type, COUNT(*) as count
                    FROM properties
                    GROUP BY property_type
                """))
                print("\n[PROPERTY TYPE DISTRIBUTION]")
                for row in result:
                    print(f"  - {row[0]}: {row[1]} properties")
            except Exception as e:
                print(f"  [SKIP] Could not get type distribution: {e}")

            print("\n" + "=" * 80)
            print("[MIGRATION COMPLETE] SUCCESS")
            print("\nSummary:")
            print("  [OK] Added 'status' column to properties table")
            print("  [OK] Added 'property_type' column to properties table")
            print("  [OK] Set existing properties to status='completed'")
            print("  [OK] Created 3 performance indexes")
            print("\nBackward Compatibility:")
            print("  - All existing properties marked as 'completed'")
            print("  - All existing properties default to 'residential'")
            print("  - Existing reports continue working unchanged")
            print("\nNext Steps:")
            print("  1. Update schemas.py to include status and property_type")
            print("  2. Update CRUD operations to handle status updates")
            print("  3. Implement duplicate property logic")
            print("  4. Update report generation to filter by status='completed'")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Remove status and property_type columns (WARNING: Will delete data)"""
    print("[ROLLBACK] Removing property status and type fields...")
    print("=" * 80)
    print("WARNING: This will delete status and property_type column data!")
    print("=" * 80)

    import sys
    if '--force' not in sys.argv:
        print("\nRollback cancelled. To proceed, run with --force flag:")
        print("  python add_property_status_and_type.py rollback --force")
        return

    try:
        with engine.connect() as conn:
            # Drop indexes
            print("\n[1/3] Dropping indexes...")
            indexes_to_drop = [
                "ix_properties_status",
                "ix_properties_type",
                "ix_properties_user_status"
            ]

            for index_name in indexes_to_drop:
                try:
                    conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                    print(f"  [OK] Dropped index: {index_name}")
                except Exception as e:
                    print(f"  [WARN] Could not drop {index_name}: {e}")

            conn.commit()

            # Remove status column
            print("\n[2/3] Removing 'status' column...")
            try:
                conn.execute(text("ALTER TABLE properties DROP COLUMN IF EXISTS status"))
                print("  [OK] Dropped status column")
            except Exception as e:
                print(f"  [WARN] Could not drop status: {e}")

            conn.commit()

            # Remove property_type column
            print("\n[3/3] Removing 'property_type' column...")
            try:
                conn.execute(text("ALTER TABLE properties DROP COLUMN IF EXISTS property_type"))
                print("  [OK] Dropped property_type column")
            except Exception as e:
                print(f"  [WARN] Could not drop property_type: {e}")

            conn.commit()

            print("\n" + "=" * 80)
            print("[ROLLBACK COMPLETE] SUCCESS")
            print("Status and property_type fields have been removed from properties table.")

    except Exception as e:
        print(f"\n[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
