"""
Migration: Remove property_address_full column from reports table

This migration safely removes the property_address_full column as addresses
will now be generated from component fields.

Run with: python migrations/remove_property_address_full.py
Rollback: python migrations/remove_property_address_full.py downgrade
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def upgrade():
    """Remove property_address_full column"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if column exists first
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='reports'
            AND column_name='property_address_full'
        """)

        result = conn.execute(check_query).fetchone()

        if result:
            print("Removing property_address_full column...")
            conn.execute(text("""
                ALTER TABLE reports DROP COLUMN property_address_full
            """))
            conn.commit()
            print("✓ Column removed successfully")
        else:
            print("Column property_address_full does not exist, skipping")

def downgrade():
    """Restore property_address_full column (for rollback)"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Restoring property_address_full column...")
        conn.execute(text("""
            ALTER TABLE reports
            ADD COLUMN property_address_full TEXT
        """))
        conn.commit()
        print("✓ Column restored")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
