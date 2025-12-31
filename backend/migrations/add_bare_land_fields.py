"""
Migration to add bare land related fields to the reports table.
This adds fields for:
- Development feasibility
- Topographical features (elevation, drainage, vegetation)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add bare land fields to reports table"""

    # Get database connection from environment
    logger.info(f"Connecting to database...")

    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    logger.info(f"Connecting to Neon database...")

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        logger.info("Starting migration: add_bare_land_fields")

        # Check if columns already exist
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'reports'
            AND column_name IN (
                'ongoing_construction_notes',
                'elevation_changes',
                'drainage_pattern',
                'vegetation_type',
                'natural_features'
            )
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"Existing columns: {existing_columns}")

        # Add missing columns
        columns_to_add = {
            'ongoing_construction_notes': 'TEXT',
            'elevation_changes': 'VARCHAR(50)',
            'drainage_pattern': 'VARCHAR(50)',
            'vegetation_type': 'VARCHAR(50)',
            'natural_features': 'TEXT'
        }

        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name} ({column_type})")
                cursor.execute(f"""
                    ALTER TABLE reports
                    ADD COLUMN {column_name} {column_type}
                """)
                logger.info(f"✓ Added column: {column_name}")
            else:
                logger.info(f"⊘ Column {column_name} already exists, skipping")

        # Commit the transaction
        conn.commit()
        logger.info("✓ Migration completed successfully")

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
