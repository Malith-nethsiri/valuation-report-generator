"""
Database migration to add missing columns and tables.

This migration adds:
1. Vehicle-related columns to the reports table
2. The vehicles table
3. The report_vehicles junction table
4. The audit_logs table
5. Missing indexes

Run with: python -m migrations.add_missing_columns
"""

import os
from dotenv import load_dotenv

# Load .env.local first if it exists, then fall back to .env
env_local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

if os.path.exists(env_local_path):
    load_dotenv(env_local_path)
    print(f"[CONFIG] Loaded environment from .env.local")
else:
    load_dotenv(env_path)
    print(f"[CONFIG] Loaded environment from .env")

from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add missing columns and tables to the database."""
    print("[MIGRATION] Adding missing columns and tables...")
    print("=" * 80)

    with engine.connect() as conn:
        # ===== STEP 1: Add vehicle-related columns to reports table =====
        print("\n[STEP 1] Adding vehicle-related columns to reports table...")

        vehicle_columns = [
            ("primary_vehicle_id", "INTEGER REFERENCES vehicles(id) ON DELETE SET NULL"),
            ("is_office_use", "BOOLEAN DEFAULT FALSE"),
            ("vehicle_count", "INTEGER DEFAULT 0"),
            ("folio_number", "VARCHAR(100)"),
            ("inspection_place", "TEXT"),
        ]

        for col_name, col_type in vehicle_columns:
            try:
                conn.execute(text(f"ALTER TABLE reports ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                print(f"  [OK] Added column: reports.{col_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Column already exists: reports.{col_name}")
                else:
                    print(f"  [ERROR] Could not add reports.{col_name}: {e}")

        conn.commit()

        # ===== STEP 2: Create vehicles table =====
        print("\n[STEP 2] Creating vehicles table...")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    vehicle_type VARCHAR(50),
                    is_template BOOLEAN DEFAULT FALSE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    original_vehicle_id INTEGER REFERENCES vehicles(id),
                    registration_number VARCHAR(50),
                    provincial_council VARCHAR(100),
                    class_of_vehicle VARCHAR(100),
                    body_colour VARCHAR(100),
                    chassis_number VARCHAR(100),
                    engine_number VARCHAR(100),
                    vehicle_status VARCHAR(100),
                    country_of_origin VARCHAR(100),
                    make VARCHAR(100),
                    model VARCHAR(200),
                    date_of_first_registration VARCHAR(50),
                    year_of_manufacture INTEGER,
                    cylinder_capacity INTEGER,
                    fuel_type VARCHAR(50),
                    mileage INTEGER,
                    mileage_unit VARCHAR(20) DEFAULT 'km',
                    engine_type VARCHAR(100),
                    transmission VARCHAR(50),
                    wheel_drive VARCHAR(20),
                    running_condition VARCHAR(50),
                    clutch_status VARCHAR(100),
                    engine_condition VARCHAR(50),
                    gear_box_condition VARCHAR(50),
                    differential_status VARCHAR(100),
                    gear_selection VARCHAR(50),
                    body_condition VARCHAR(50),
                    chassis_condition VARCHAR(50),
                    upholstery_condition VARCHAR(50),
                    underside_condition VARCHAR(50),
                    body_parts_status VARCHAR(100),
                    engine_parts_status VARCHAR(100),
                    accessories_status VARCHAR(100),
                    fuel_consumption NUMERIC(6, 2),
                    fuel_consumption_unit VARCHAR(20),
                    foot_brake_condition VARCHAR(50),
                    disc_brake_available BOOLEAN,
                    parking_brake_condition VARCHAR(50),
                    abs_available BOOLEAN,
                    features JSONB,
                    suspension JSONB,
                    tyres JSONB,
                    electrical JSONB,
                    lights JSONB,
                    has_accidents BOOLEAN,
                    has_repairs BOOLEAN,
                    needs_repairs_within_year BOOLEAN,
                    body_parts_replaced BOOLEAN,
                    purchase_price NUMERIC(15, 2),
                    brand_new_price NUMERIC(15, 2),
                    market_value NUMERIC(15, 2),
                    forced_sale_value NUMERIC(15, 2),
                    valuation_summary TEXT,
                    office_data JSONB,
                    past_valuations JSONB,
                    vehicle_photos JSONB,
                    book_images JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    CONSTRAINT uq_vehicle_user_registration UNIQUE (user_id, registration_number)
                )
            """))
            print("  [OK] Created vehicles table")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  [SKIP] Table already exists: vehicles")
            else:
                print(f"  [ERROR] Could not create vehicles table: {e}")

        conn.commit()

        # ===== STEP 3: Create report_vehicles junction table =====
        print("\n[STEP 3] Creating report_vehicles table...")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS report_vehicles (
                    id SERIAL PRIMARY KEY,
                    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                    vehicle_order INTEGER NOT NULL DEFAULT 1,
                    report_specific_notes TEXT,
                    override_market_value NUMERIC(15, 2),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            print("  [OK] Created report_vehicles table")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  [SKIP] Table already exists: report_vehicles")
            else:
                print(f"  [ERROR] Could not create report_vehicles table: {e}")

        conn.commit()

        # ===== STEP 4: Create audit_logs table =====
        print("\n[STEP 4] Creating audit_logs table...")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(50) NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    resource_id INTEGER,
                    description TEXT,
                    details JSONB,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(500),
                    request_id VARCHAR(36),
                    success BOOLEAN NOT NULL DEFAULT TRUE,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            print("  [OK] Created audit_logs table")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  [SKIP] Table already exists: audit_logs")
            else:
                print(f"  [ERROR] Could not create audit_logs table: {e}")

        conn.commit()

        # ===== STEP 5: Create jobs table =====
        print("\n[STEP 5] Creating jobs table...")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
                    job_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    result_url VARCHAR(500),
                    result_filename VARCHAR(255),
                    error_message TEXT,
                    progress_percent INTEGER DEFAULT 0,
                    progress_message VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE
                )
            """))
            print("  [OK] Created jobs table")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  [SKIP] Table already exists: jobs")
            else:
                print(f"  [ERROR] Could not create jobs table: {e}")

        conn.commit()

        # ===== STEP 6: Add indexes =====
        print("\n[STEP 6] Adding indexes...")

        indexes = [
            ("idx_reports_user_id", "reports", "user_id"),
            ("idx_properties_user_id", "properties", "user_id"),
            ("idx_report_properties_report_id", "report_properties", "report_id"),
            ("idx_report_properties_property_id", "report_properties", "property_id"),
            ("idx_vehicles_user_id", "vehicles", "user_id"),
            ("idx_vehicles_registration", "vehicles", "registration_number"),
            ("idx_vehicles_make", "vehicles", "make"),
            ("idx_report_vehicles_report_id", "report_vehicles", "report_id"),
            ("idx_report_vehicles_vehicle_id", "report_vehicles", "vehicle_id"),
            ("idx_audit_logs_user_id", "audit_logs", "user_id"),
            ("idx_audit_logs_action", "audit_logs", "action"),
            ("idx_audit_logs_resource_type", "audit_logs", "resource_type"),
            ("idx_audit_logs_created_at", "audit_logs", "created_at"),
        ]

        for idx_name, table_name, column_name in indexes:
            try:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})"))
                print(f"  [OK] Created index: {idx_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Index already exists: {idx_name}")
                else:
                    print(f"  [ERROR] Could not create index {idx_name}: {e}")

        conn.commit()

        print("\n" + "=" * 80)
        print("[MIGRATION] Completed successfully!")
        print("=" * 80)


def rollback():
    """Remove the added columns and tables."""
    print("[ROLLBACK] Removing added columns and tables...")

    with engine.connect() as conn:
        # Drop tables in reverse order (respecting foreign keys)
        tables_to_drop = ["audit_logs", "report_vehicles", "jobs"]

        for table in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  [OK] Dropped table: {table}")
            except Exception as e:
                print(f"  [ERROR] Could not drop {table}: {e}")

        # Remove vehicle columns from reports
        vehicle_columns = [
            "primary_vehicle_id",
            "is_office_use",
            "vehicle_count",
            "folio_number",
            "inspection_place",
        ]

        for col in vehicle_columns:
            try:
                conn.execute(text(f"ALTER TABLE reports DROP COLUMN IF EXISTS {col}"))
                print(f"  [OK] Dropped column: reports.{col}")
            except Exception as e:
                print(f"  [ERROR] Could not drop reports.{col}: {e}")

        # Drop vehicles table last (after foreign keys are removed)
        try:
            conn.execute(text("DROP TABLE IF EXISTS vehicles CASCADE"))
            print("  [OK] Dropped table: vehicles")
        except Exception as e:
            print(f"  [ERROR] Could not drop vehicles: {e}")

        conn.commit()
        print("[ROLLBACK] Completed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
