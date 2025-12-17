"""
Database migration to add check constraints, defaults, and column comments for data integrity.

This migration adds:
1. Check constraints for coordinates, land extent values
2. Server-side defaults for status, report_type, has_electricity
3. Column comments for better documentation

Benefits:
- Database-level validation ensures data integrity
- Defaults prevent NULL values in critical fields
- Comments improve maintainability
"""

from app.database import engine
from sqlalchemy import text


def migrate():
    """Add constraints, defaults, and column comments to reports table"""
    print("[MIGRATION] Adding database constraints, defaults, and comments...")

    try:
        with engine.connect() as conn:
            # 1. Add check constraints
            print("[1/5] Adding check constraints...")

            # Latitude constraint (-90 to 90 degrees)
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_property_latitude_range
                    CHECK (property_latitude IS NULL OR (property_latitude >= -90 AND property_latitude <= 90))
                """))
                print("  ✓ Added latitude range constraint (-90 to 90)")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Latitude constraint already exists")
                else:
                    raise

            # Longitude constraint (-180 to 180 degrees)
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_property_longitude_range
                    CHECK (property_longitude IS NULL OR (property_longitude >= -180 AND property_longitude <= 180))
                """))
                print("  ✓ Added longitude range constraint (-180 to 180)")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Longitude constraint already exists")
                else:
                    raise

            # Access point latitude constraint
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_access_latitude_range
                    CHECK (access_starting_point_latitude IS NULL OR (access_starting_point_latitude >= -90 AND access_starting_point_latitude <= 90))
                """))
                print("  ✓ Added access point latitude range constraint")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Access latitude constraint already exists")
                else:
                    raise

            # Access point longitude constraint
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_access_longitude_range
                    CHECK (access_starting_point_longitude IS NULL OR (access_starting_point_longitude >= -180 AND access_starting_point_longitude <= 180))
                """))
                print("  ✓ Added access point longitude range constraint")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Access longitude constraint already exists")
                else:
                    raise

            # Land extent acres constraint (non-negative)
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_land_extent_acres_nonnegative
                    CHECK (land_extent_acres IS NULL OR land_extent_acres >= 0)
                """))
                print("  ✓ Added land extent acres non-negative constraint")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Land extent acres constraint already exists")
                else:
                    raise

            # Land extent roods constraint (0-3, since 1 acre = 4 roods)
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_land_extent_roods_range
                    CHECK (land_extent_roods IS NULL OR (land_extent_roods >= 0 AND land_extent_roods <= 3))
                """))
                print("  ✓ Added land extent roods range constraint (0-3)")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Land extent roods constraint already exists")
                else:
                    raise

            # Land extent perches constraint (0-39.99, since 1 rood = 40 perches)
            try:
                conn.execute(text("""
                    ALTER TABLE reports
                    ADD CONSTRAINT check_land_extent_perches_range
                    CHECK (land_extent_perches IS NULL OR (land_extent_perches >= 0 AND land_extent_perches < 40))
                """))
                print("  ✓ Added land extent perches range constraint (0-39.99)")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  ⊕ Land extent perches constraint already exists")
                else:
                    raise

            conn.commit()
            print("[OK] Check constraints added successfully")

            # 2. Add/update server defaults
            print("\n[2/5] Setting server defaults...")

            # Note: In PostgreSQL, changing default doesn't affect existing rows
            conn.execute(text("""
                ALTER TABLE reports
                ALTER COLUMN status SET DEFAULT 'draft'
            """))
            print("  ✓ Set status default to 'draft'")

            conn.execute(text("""
                ALTER TABLE reports
                ALTER COLUMN report_type SET DEFAULT 'residential_property'
            """))
            print("  ✓ Set report_type default to 'residential_property'")

            conn.execute(text("""
                ALTER TABLE reports
                ALTER COLUMN has_electricity SET DEFAULT TRUE
            """))
            print("  ✓ Set has_electricity default to TRUE")

            conn.execute(text("""
                ALTER TABLE reports
                ALTER COLUMN applicant_country SET DEFAULT 'Sri Lanka'
            """))
            print("  ✓ Set applicant_country default to 'Sri Lanka'")

            conn.commit()
            print("[OK] Server defaults configured successfully")

            # 3. Add column comments (PostgreSQL)
            print("\n[3/5] Adding column comments...")

            conn.execute(text("""
                COMMENT ON COLUMN reports.property_latitude IS 'GPS latitude of property location (-90 to 90 degrees)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.property_longitude IS 'GPS longitude of property location (-180 to 180 degrees)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.land_extent_acres IS 'Land extent in acres (must be non-negative)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.land_extent_roods IS 'Land extent in roods (0-3, where 1 acre = 4 roods)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.land_extent_perches IS 'Land extent in perches (0-39.99, where 1 rood = 40 perches)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.status IS 'Report status (draft or completed)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.report_type IS 'Type of property report (e.g., residential_property)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN reports.has_electricity IS 'Whether property has electricity connection'
            """))
            conn.commit()
            print("  ✓ Added column comments for documentation")
            print("[OK] Column comments added successfully")

            # 4. Update existing NULL values to defaults (optional but recommended)
            print("\n[4/5] Updating existing NULL values...")

            result = conn.execute(text("""
                UPDATE reports
                SET status = 'draft'
                WHERE status IS NULL
            """))
            updated_status = result.rowcount
            print(f"  ✓ Updated {updated_status} rows with NULL status to 'draft'")

            result = conn.execute(text("""
                UPDATE reports
                SET report_type = 'residential_property'
                WHERE report_type IS NULL
            """))
            updated_type = result.rowcount
            print(f"  ✓ Updated {updated_type} rows with NULL report_type to 'residential_property'")

            result = conn.execute(text("""
                UPDATE reports
                SET has_electricity = TRUE
                WHERE has_electricity IS NULL
            """))
            updated_electricity = result.rowcount
            print(f"  ✓ Updated {updated_electricity} rows with NULL has_electricity to TRUE")

            result = conn.execute(text("""
                UPDATE reports
                SET applicant_country = 'Sri Lanka'
                WHERE applicant_country IS NULL
            """))
            updated_country = result.rowcount
            print(f"  ✓ Updated {updated_country} rows with NULL applicant_country to 'Sri Lanka'")

            conn.commit()
            print("[OK] NULL values updated successfully")

            # 5. Verify constraints
            print("\n[5/5] Verifying constraints...")
            result = conn.execute(text("""
                SELECT conname, contype, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'reports'::regclass
                AND contype = 'c'
                ORDER BY conname
            """))
            constraints = result.fetchall()
            print(f"  ✓ Found {len(constraints)} check constraints on reports table:")
            for name, type_, definition in constraints:
                if 'check_' in name:
                    print(f"    - {name}")

            print("\n[MIGRATION COMPLETE] ✅")
            print("Summary:")
            print("  - Added 7 check constraints for data validation")
            print("  - Set 4 server defaults")
            print("  - Added 8 column comments")
            print(f"  - Updated {updated_status + updated_type + updated_electricity + updated_country} existing NULL values")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Remove constraints, defaults, and comments added by migration"""
    print("[ROLLBACK] Removing database constraints, defaults, and comments...")

    try:
        with engine.connect() as conn:
            # Remove check constraints
            print("[1/3] Dropping check constraints...")

            constraints_to_drop = [
                "check_property_latitude_range",
                "check_property_longitude_range",
                "check_access_latitude_range",
                "check_access_longitude_range",
                "check_land_extent_acres_nonnegative",
                "check_land_extent_roods_range",
                "check_land_extent_perches_range"
            ]

            for constraint in constraints_to_drop:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE reports
                        DROP CONSTRAINT IF EXISTS {constraint}
                    """))
                    print(f"  ✓ Dropped constraint: {constraint}")
                except Exception as e:
                    print(f"  ⚠ Could not drop {constraint}: {e}")

            conn.commit()
            print("[OK] Check constraints removed")

            # Remove defaults (set to NULL)
            print("\n[2/3] Removing server defaults...")

            conn.execute(text("ALTER TABLE reports ALTER COLUMN status DROP DEFAULT"))
            conn.execute(text("ALTER TABLE reports ALTER COLUMN report_type DROP DEFAULT"))
            conn.execute(text("ALTER TABLE reports ALTER COLUMN has_electricity DROP DEFAULT"))
            conn.execute(text("ALTER TABLE reports ALTER COLUMN applicant_country DROP DEFAULT"))

            conn.commit()
            print("[OK] Server defaults removed")

            # Remove column comments
            print("\n[3/3] Removing column comments...")

            columns = [
                "property_latitude", "property_longitude", "land_extent_acres",
                "land_extent_roods", "land_extent_perches", "status",
                "report_type", "has_electricity"
            ]

            for column in columns:
                conn.execute(text(f"COMMENT ON COLUMN reports.{column} IS NULL"))

            conn.commit()
            print("[OK] Column comments removed")

            print("\n[ROLLBACK COMPLETE] ✅")

    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
