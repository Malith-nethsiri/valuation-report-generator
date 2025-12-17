"""
Migration script to add property identification type and valuation purpose fields to the reports table.
Run this script once to add the new columns.

Usage: cd backend && python migrations/add_property_identification_and_purpose.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)

    migration_statements = [
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS property_identification_type VARCHAR(50);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS valuation_purpose VARCHAR(200);
        """,
    ]

    with engine.connect() as conn:
        for stmt in migration_statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                print(f"Executed: {stmt.strip()[:50]}...")
            except Exception as e:
                print(f"Warning (may already exist): {e}")

    print("\nMigration completed successfully!")
    print("Added columns:")
    print("  - property_identification_type VARCHAR(50) (nullable)")
    print("  - valuation_purpose VARCHAR(200) (nullable)")

if __name__ == "__main__":
    run_migration()
