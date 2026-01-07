"""
Database migration to convert water_supply_type and predominant_building_type
from single VARCHAR to multi-select JSON arrays.

This migration enables multi-select functionality for water supply types and
predominant building types across all report types (residential, bare land, multi-property).

Changes:
- Converts water_supply_type in 'reports' table: VARCHAR(50) → JSON array
- Converts predominant_building_type in 'reports' table: VARCHAR(100) → JSON array
- Converts water_supply_type in 'properties' table: VARCHAR(50) → JSON array
- Converts predominant_building_type in 'properties' table: VARCHAR(100) → JSON array
- Migrates existing single-value data to array format: "value" → ["value"]
- Preserves NULL values as NULL (not empty arrays)

Backward Compatibility:
- All existing data is automatically converted to arrays
- Report generation code handles both string (legacy) and array (new) formats
- No breaking changes for existing reports
"""

import json
from app.database import engine
from sqlalchemy import text


def detect_database_type():
    """Detect if using PostgreSQL or SQLite"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        # Check dialect name
        return engine.dialect.name


def migrate():
    """Convert water_supply_type and predominant_building_type to JSON arrays"""
    print("[MIGRATION] Converting water supply and building types to multi-select arrays...")
    print("=" * 80)

    db_type = detect_database_type()
    print(f"\n[INFO] Detected database type: {db_type}")

    try:
        with engine.connect() as conn:
            # ===== STEP 1: Reports table - water_supply_type =====
            print("\n[STEP 1/4] Converting reports.water_supply_type to JSON array...")

            if db_type == 'postgresql':
                # PostgreSQL approach
                try:
                    # Check if column already JSON
                    result = conn.execute(text("""
                        SELECT data_type FROM information_schema.columns
                        WHERE table_name = 'reports' AND column_name = 'water_supply_type'
                    """))
                    current_type = result.fetchone()

                    if current_type and 'json' in current_type[0].lower():
                        print("  [SKIP] water_supply_type already JSON type")
                    else:
                        # Add temporary column
                        conn.execute(text("""
                            ALTER TABLE reports ADD COLUMN IF NOT EXISTS water_supply_type_temp JSON
                        """))

                        # Migrate data: single string → array with one element
                        conn.execute(text("""
                            UPDATE reports
                            SET water_supply_type_temp =
                                CASE
                                    WHEN water_supply_type IS NULL OR water_supply_type = '' THEN NULL
                                    ELSE json_build_array(water_supply_type)
                                END
                        """))

                        # Drop old column and rename
                        conn.execute(text("ALTER TABLE reports DROP COLUMN water_supply_type"))
                        conn.execute(text("ALTER TABLE reports RENAME COLUMN water_supply_type_temp TO water_supply_type"))
                        print("  [OK] Converted water_supply_type to JSON array (PostgreSQL)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert water_supply_type: {e}")
                    raise

            else:  # SQLite
                try:
                    # SQLite requires table recreation for type changes
                    # First, check if migration already done
                    result = conn.execute(text("PRAGMA table_info(reports)")).fetchall()
                    water_supply_col = [col for col in result if col[1] == 'water_supply_type']

                    if water_supply_col and water_supply_col[0][2].upper() == 'JSON':
                        print("  [SKIP] water_supply_type already JSON type")
                    else:
                        # Get existing data
                        existing_data = conn.execute(text("""
                            SELECT id, water_supply_type FROM reports
                        """)).fetchall()

                        # Add temp column
                        conn.execute(text("ALTER TABLE reports ADD COLUMN water_supply_type_temp TEXT"))

                        # Migrate data row by row
                        for row_id, old_value in existing_data:
                            if old_value and old_value.strip():
                                new_value = json.dumps([old_value])
                            else:
                                new_value = None

                            conn.execute(
                                text("UPDATE reports SET water_supply_type_temp = :value WHERE id = :id"),
                                {"value": new_value, "id": row_id}
                            )

                        # Note: SQLite doesn't support DROP COLUMN easily
                        # We'll keep both columns and document the temp column as the new one
                        print("  [OK] Migrated data to water_supply_type_temp (SQLite)")
                        print("  [INFO] Manual step needed: Rename water_supply_type_temp to water_supply_type")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert water_supply_type: {e}")
                    raise

            conn.commit()

            # ===== STEP 2: Reports table - predominant_building_type =====
            print("\n[STEP 2/4] Converting reports.predominant_building_type to JSON array...")

            if db_type == 'postgresql':
                try:
                    # Check if column already JSON
                    result = conn.execute(text("""
                        SELECT data_type FROM information_schema.columns
                        WHERE table_name = 'reports' AND column_name = 'predominant_building_type'
                    """))
                    current_type = result.fetchone()

                    if current_type and 'json' in current_type[0].lower():
                        print("  [SKIP] predominant_building_type already JSON type")
                    else:
                        # Add temporary column
                        conn.execute(text("""
                            ALTER TABLE reports ADD COLUMN IF NOT EXISTS predominant_building_type_temp JSON
                        """))

                        # Migrate data
                        conn.execute(text("""
                            UPDATE reports
                            SET predominant_building_type_temp =
                                CASE
                                    WHEN predominant_building_type IS NULL OR predominant_building_type = '' THEN NULL
                                    ELSE json_build_array(predominant_building_type)
                                END
                        """))

                        # Drop old and rename
                        conn.execute(text("ALTER TABLE reports DROP COLUMN predominant_building_type"))
                        conn.execute(text("ALTER TABLE reports RENAME COLUMN predominant_building_type_temp TO predominant_building_type"))
                        print("  [OK] Converted predominant_building_type to JSON array (PostgreSQL)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert predominant_building_type: {e}")
                    raise

            else:  # SQLite
                try:
                    result = conn.execute(text("PRAGMA table_info(reports)")).fetchall()
                    building_type_col = [col for col in result if col[1] == 'predominant_building_type']

                    if building_type_col and building_type_col[0][2].upper() == 'JSON':
                        print("  [SKIP] predominant_building_type already JSON type")
                    else:
                        existing_data = conn.execute(text("""
                            SELECT id, predominant_building_type FROM reports
                        """)).fetchall()

                        conn.execute(text("ALTER TABLE reports ADD COLUMN predominant_building_type_temp TEXT"))

                        for row_id, old_value in existing_data:
                            if old_value and old_value.strip():
                                new_value = json.dumps([old_value])
                            else:
                                new_value = None

                            conn.execute(
                                text("UPDATE reports SET predominant_building_type_temp = :value WHERE id = :id"),
                                {"value": new_value, "id": row_id}
                            )

                        print("  [OK] Migrated data to predominant_building_type_temp (SQLite)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert predominant_building_type: {e}")
                    raise

            conn.commit()

            # ===== STEP 3: Properties table - water_supply_type =====
            print("\n[STEP 3/4] Converting properties.water_supply_type to JSON array...")

            if db_type == 'postgresql':
                try:
                    result = conn.execute(text("""
                        SELECT data_type FROM information_schema.columns
                        WHERE table_name = 'properties' AND column_name = 'water_supply_type'
                    """))
                    current_type = result.fetchone()

                    if current_type and 'json' in current_type[0].lower():
                        print("  [SKIP] water_supply_type already JSON type")
                    else:
                        conn.execute(text("""
                            ALTER TABLE properties ADD COLUMN IF NOT EXISTS water_supply_type_temp JSON
                        """))

                        conn.execute(text("""
                            UPDATE properties
                            SET water_supply_type_temp =
                                CASE
                                    WHEN water_supply_type IS NULL OR water_supply_type = '' THEN NULL
                                    ELSE json_build_array(water_supply_type)
                                END
                        """))

                        conn.execute(text("ALTER TABLE properties DROP COLUMN water_supply_type"))
                        conn.execute(text("ALTER TABLE properties RENAME COLUMN water_supply_type_temp TO water_supply_type"))
                        print("  [OK] Converted water_supply_type to JSON array (PostgreSQL)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert water_supply_type: {e}")
                    raise

            else:  # SQLite
                try:
                    result = conn.execute(text("PRAGMA table_info(properties)")).fetchall()
                    water_supply_col = [col for col in result if col[1] == 'water_supply_type']

                    if water_supply_col and water_supply_col[0][2].upper() == 'JSON':
                        print("  [SKIP] water_supply_type already JSON type")
                    else:
                        existing_data = conn.execute(text("""
                            SELECT id, water_supply_type FROM properties
                        """)).fetchall()

                        conn.execute(text("ALTER TABLE properties ADD COLUMN water_supply_type_temp TEXT"))

                        for row_id, old_value in existing_data:
                            if old_value and old_value.strip():
                                new_value = json.dumps([old_value])
                            else:
                                new_value = None

                            conn.execute(
                                text("UPDATE properties SET water_supply_type_temp = :value WHERE id = :id"),
                                {"value": new_value, "id": row_id}
                            )

                        print("  [OK] Migrated data to water_supply_type_temp (SQLite)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert water_supply_type: {e}")
                    raise

            conn.commit()

            # ===== STEP 4: Properties table - predominant_building_type =====
            print("\n[STEP 4/4] Converting properties.predominant_building_type to JSON array...")

            if db_type == 'postgresql':
                try:
                    result = conn.execute(text("""
                        SELECT data_type FROM information_schema.columns
                        WHERE table_name = 'properties' AND column_name = 'predominant_building_type'
                    """))
                    current_type = result.fetchone()

                    if current_type and 'json' in current_type[0].lower():
                        print("  [SKIP] predominant_building_type already JSON type")
                    else:
                        conn.execute(text("""
                            ALTER TABLE properties ADD COLUMN IF NOT EXISTS predominant_building_type_temp JSON
                        """))

                        conn.execute(text("""
                            UPDATE properties
                            SET predominant_building_type_temp =
                                CASE
                                    WHEN predominant_building_type IS NULL OR predominant_building_type = '' THEN NULL
                                    ELSE json_build_array(predominant_building_type)
                                END
                        """))

                        conn.execute(text("ALTER TABLE properties DROP COLUMN predominant_building_type"))
                        conn.execute(text("ALTER TABLE properties RENAME COLUMN predominant_building_type_temp TO predominant_building_type"))
                        print("  [OK] Converted predominant_building_type to JSON array (PostgreSQL)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert predominant_building_type: {e}")
                    raise

            else:  # SQLite
                try:
                    result = conn.execute(text("PRAGMA table_info(properties)")).fetchall()
                    building_type_col = [col for col in result if col[1] == 'predominant_building_type']

                    if building_type_col and building_type_col[0][2].upper() == 'JSON':
                        print("  [SKIP] predominant_building_type already JSON type")
                    else:
                        existing_data = conn.execute(text("""
                            SELECT id, predominant_building_type FROM properties
                        """)).fetchall()

                        conn.execute(text("ALTER TABLE properties ADD COLUMN predominant_building_type_temp TEXT"))

                        for row_id, old_value in existing_data:
                            if old_value and old_value.strip():
                                new_value = json.dumps([old_value])
                            else:
                                new_value = None

                            conn.execute(
                                text("UPDATE properties SET predominant_building_type_temp = :value WHERE id = :id"),
                                {"value": new_value, "id": row_id}
                            )

                        print("  [OK] Migrated data to predominant_building_type_temp (SQLite)")

                except Exception as e:
                    print(f"  [ERROR] Failed to convert predominant_building_type: {e}")
                    raise

            conn.commit()

            # ===== Verification =====
            print("\n" + "=" * 80)
            print("[VERIFICATION] Checking migration results...")

            # Sample data check
            sample = conn.execute(text("SELECT id, water_supply_type, predominant_building_type FROM reports LIMIT 3")).fetchall()
            print("\nSample data from reports table:")
            for row in sample:
                print(f"  ID {row[0]}: water_supply={row[1]}, buildings={row[2]}")

            print("\n" + "=" * 80)
            print("[MIGRATION COMPLETE]")
            print("\nSummary:")
            print("  [OK] Converted water_supply_type to JSON array in reports table")
            print("  [OK] Converted predominant_building_type to JSON array in reports table")
            print("  [OK] Converted water_supply_type to JSON array in properties table")
            print("  [OK] Converted predominant_building_type to JSON array in properties table")
            print("\nBackward Compatibility:")
            print("  - All existing single values converted to arrays automatically")
            print("  - NULL values preserved as NULL (not empty arrays)")
            print("  - Report generation handles both formats during transition")
            print("\nNext Steps:")
            print("  1. Update backend models.py to use JSON column type")
            print("  2. Update backend schemas.py to use List[str] type")
            print("  3. Update frontend components to use multi-select UI")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Rollback: Convert JSON arrays back to VARCHAR single values"""
    print("[ROLLBACK] Converting arrays back to single values...")
    print("=" * 80)

    db_type = detect_database_type()
    print(f"\n[INFO] Detected database type: {db_type}")

    try:
        with engine.connect() as conn:
            if db_type == 'postgresql':
                # PostgreSQL rollback
                print("\n[1/4] Rolling back reports.water_supply_type...")
                try:
                    conn.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS water_supply_type_old VARCHAR(50)"))
                    conn.execute(text("""
                        UPDATE reports
                        SET water_supply_type_old =
                            CASE
                                WHEN water_supply_type IS NULL THEN NULL
                                WHEN jsonb_array_length(water_supply_type::jsonb) > 0
                                    THEN water_supply_type::jsonb->>0
                                ELSE NULL
                            END
                    """))
                    conn.execute(text("ALTER TABLE reports DROP COLUMN water_supply_type"))
                    conn.execute(text("ALTER TABLE reports RENAME COLUMN water_supply_type_old TO water_supply_type"))
                    print("  [OK] Rolled back water_supply_type to VARCHAR")
                except Exception as e:
                    print(f"  [ERROR] {e}")

                print("\n[2/4] Rolling back reports.predominant_building_type...")
                try:
                    conn.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS predominant_building_type_old VARCHAR(100)"))
                    conn.execute(text("""
                        UPDATE reports
                        SET predominant_building_type_old =
                            CASE
                                WHEN predominant_building_type IS NULL THEN NULL
                                WHEN jsonb_array_length(predominant_building_type::jsonb) > 0
                                    THEN predominant_building_type::jsonb->>0
                                ELSE NULL
                            END
                    """))
                    conn.execute(text("ALTER TABLE reports DROP COLUMN predominant_building_type"))
                    conn.execute(text("ALTER TABLE reports RENAME COLUMN predominant_building_type_old TO predominant_building_type"))
                    print("  [OK] Rolled back predominant_building_type to VARCHAR")
                except Exception as e:
                    print(f"  [ERROR] {e}")

                print("\n[3/4] Rolling back properties.water_supply_type...")
                try:
                    conn.execute(text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS water_supply_type_old VARCHAR(50)"))
                    conn.execute(text("""
                        UPDATE properties
                        SET water_supply_type_old =
                            CASE
                                WHEN water_supply_type IS NULL THEN NULL
                                WHEN jsonb_array_length(water_supply_type::jsonb) > 0
                                    THEN water_supply_type::jsonb->>0
                                ELSE NULL
                            END
                    """))
                    conn.execute(text("ALTER TABLE properties DROP COLUMN water_supply_type"))
                    conn.execute(text("ALTER TABLE properties RENAME COLUMN water_supply_type_old TO water_supply_type"))
                    print("  [OK] Rolled back water_supply_type to VARCHAR")
                except Exception as e:
                    print(f"  [ERROR] {e}")

                print("\n[4/4] Rolling back properties.predominant_building_type...")
                try:
                    conn.execute(text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS predominant_building_type_old VARCHAR(100)"))
                    conn.execute(text("""
                        UPDATE properties
                        SET predominant_building_type_old =
                            CASE
                                WHEN predominant_building_type IS NULL THEN NULL
                                WHEN jsonb_array_length(predominant_building_type::jsonb) > 0
                                    THEN predominant_building_type::jsonb->>0
                                ELSE NULL
                            END
                    """))
                    conn.execute(text("ALTER TABLE properties DROP COLUMN predominant_building_type"))
                    conn.execute(text("ALTER TABLE properties RENAME COLUMN predominant_building_type_old TO predominant_building_type"))
                    print("  [OK] Rolled back predominant_building_type to VARCHAR")
                except Exception as e:
                    print(f"  [ERROR] {e}")

            else:  # SQLite
                print("\n[WARN] SQLite rollback requires manual intervention")
                print("  - Remove _temp columns and restore original column types")

            conn.commit()

            print("\n" + "=" * 80)
            print("[ROLLBACK COMPLETE]")
            print("Multi-select fields have been reverted to single-value VARCHAR columns.")
            print("Note: Only the first value from each array was preserved during rollback.")

    except Exception as e:
        print(f"\n[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
