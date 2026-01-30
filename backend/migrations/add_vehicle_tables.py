"""
Vehicle Tables Migration

This migration adds:
1. vehicles table - for vehicle valuation data
2. report_vehicles table - junction table for many-to-many relationship
3. Updates to reports table - adds vehicle-related columns

Run with: python -m migrations.add_vehicle_tables
"""

import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(env_dir, '.env.local'), override=True)
load_dotenv(os.path.join(env_dir, '.env'))


def get_database_url():
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL")


def run_migration():
    """Run the vehicle tables migration"""
    database_url = get_database_url()
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False

    engine = create_engine(database_url)
    inspector = inspect(engine)

    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()

            # Check if vehicles table already exists
            existing_tables = inspector.get_table_names()

            if 'vehicles' not in existing_tables:
                logger.info("Creating vehicles table...")
                conn.execute(text("""
                    CREATE TABLE vehicles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                        -- Status & Type
                        status VARCHAR(50) NOT NULL DEFAULT 'draft',
                        vehicle_type VARCHAR(50),
                        is_template BOOLEAN DEFAULT FALSE,
                        is_deleted BOOLEAN DEFAULT FALSE,
                        original_vehicle_id INTEGER REFERENCES vehicles(id),

                        -- Vehicle Identification
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

                        -- Engine & Transmission
                        engine_type VARCHAR(100),
                        transmission VARCHAR(50),
                        wheel_drive VARCHAR(20),

                        -- Condition Fields
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

                        -- Parts Availability
                        body_parts_status VARCHAR(100),
                        engine_parts_status VARCHAR(100),
                        accessories_status VARCHAR(100),

                        -- Fuel & Performance
                        fuel_consumption NUMERIC(6, 2),
                        fuel_consumption_unit VARCHAR(20),

                        -- Brakes
                        foot_brake_condition VARCHAR(50),
                        disc_brake_available BOOLEAN,
                        parking_brake_condition VARCHAR(50),
                        abs_available BOOLEAN,

                        -- JSONB Fields
                        features JSONB,
                        suspension JSONB,
                        tyres JSONB,
                        electrical JSONB,
                        lights JSONB,

                        -- History
                        has_accidents BOOLEAN,
                        has_repairs BOOLEAN,
                        needs_repairs_within_year BOOLEAN,
                        body_parts_replaced BOOLEAN,

                        -- Valuation
                        purchase_price NUMERIC(15, 2),
                        brand_new_price NUMERIC(15, 2),
                        market_value NUMERIC(15, 2),
                        forced_sale_value NUMERIC(15, 2),
                        valuation_summary TEXT,

                        -- Office Use & Past Valuations
                        office_data JSONB,
                        past_valuations JSONB,

                        -- Photos
                        vehicle_photos JSONB,
                        book_images JSONB,

                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """))
                logger.info("vehicles table created successfully")

                # Create indexes
                logger.info("Creating indexes on vehicles table...")
                conn.execute(text("CREATE INDEX idx_vehicles_user_id ON vehicles(user_id)"))
                conn.execute(text("CREATE INDEX idx_vehicles_registration_number ON vehicles(registration_number)"))
                conn.execute(text("CREATE INDEX idx_vehicles_make ON vehicles(make)"))
                conn.execute(text("CREATE INDEX idx_vehicles_status ON vehicles(status)"))
                logger.info("Indexes created successfully")
            else:
                logger.info("vehicles table already exists, skipping creation")

            if 'report_vehicles' not in existing_tables:
                logger.info("Creating report_vehicles junction table...")
                conn.execute(text("""
                    CREATE TABLE report_vehicles (
                        id SERIAL PRIMARY KEY,
                        report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                        vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                        vehicle_order INTEGER NOT NULL DEFAULT 1,
                        report_specific_notes TEXT,
                        override_market_value NUMERIC(15, 2),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                        -- Unique constraint to prevent duplicate associations
                        UNIQUE(report_id, vehicle_id)
                    )
                """))
                logger.info("report_vehicles table created successfully")

                # Create indexes
                logger.info("Creating indexes on report_vehicles table...")
                conn.execute(text("CREATE INDEX idx_report_vehicles_report_id ON report_vehicles(report_id)"))
                conn.execute(text("CREATE INDEX idx_report_vehicles_vehicle_id ON report_vehicles(vehicle_id)"))
                logger.info("Indexes created successfully")
            else:
                logger.info("report_vehicles table already exists, skipping creation")

            # Add columns to reports table if they don't exist
            logger.info("Checking for new columns in reports table...")

            existing_columns = [col['name'] for col in inspector.get_columns('reports')]

            new_columns = [
                ("primary_vehicle_id", "INTEGER REFERENCES vehicles(id) ON DELETE SET NULL"),
                ("is_office_use", "BOOLEAN DEFAULT FALSE"),
                ("vehicle_count", "INTEGER DEFAULT 0"),
                ("folio_number", "VARCHAR(100)"),
                ("inspection_place", "TEXT"),
            ]

            for col_name, col_def in new_columns:
                if col_name not in existing_columns:
                    logger.info(f"Adding column {col_name} to reports table...")
                    conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_def}"))
                    logger.info(f"Column {col_name} added successfully")
                else:
                    logger.info(f"Column {col_name} already exists in reports table")

            # Commit transaction
            trans.commit()
            logger.info("Migration completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            trans.rollback()
            raise


def rollback_migration():
    """Rollback the vehicle tables migration"""
    database_url = get_database_url()
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            trans = conn.begin()

            logger.info("Rolling back vehicle tables migration...")

            # Remove columns from reports table
            logger.info("Removing vehicle-related columns from reports table...")
            columns_to_remove = [
                "primary_vehicle_id",
                "is_office_use",
                "vehicle_count",
                "folio_number",
                "inspection_place",
            ]

            for col_name in columns_to_remove:
                try:
                    conn.execute(text(f"ALTER TABLE reports DROP COLUMN IF EXISTS {col_name}"))
                    logger.info(f"Dropped column {col_name}")
                except Exception as e:
                    logger.warning(f"Could not drop column {col_name}: {e}")

            # Drop junction table first (due to foreign key)
            logger.info("Dropping report_vehicles table...")
            conn.execute(text("DROP TABLE IF EXISTS report_vehicles CASCADE"))

            # Drop vehicles table
            logger.info("Dropping vehicles table...")
            conn.execute(text("DROP TABLE IF EXISTS vehicles CASCADE"))

            trans.commit()
            logger.info("Rollback completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            trans.rollback()
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vehicle tables migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
