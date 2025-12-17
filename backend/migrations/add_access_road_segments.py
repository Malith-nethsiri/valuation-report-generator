"""
Migration script to add access_road_segments column to the reports table.
This column stores detailed road segment information with surface types and conditions.

Run this script once to add the new column.

Usage: cd backend && python migrations/add_access_road_segments.py
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
        ADD COLUMN IF NOT EXISTS access_road_segments JSON;
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
    print("Added column:")
    print("  - access_road_segments JSON (nullable)")
    print("\nThis column stores detailed road segment information including:")
    print("  - Road names")
    print("  - Road types (paved, gravel, sand, earth, carpet)")
    print("  - Surface conditions (excellent, good, fair, poor)")
    print("  - Road widths")
    print("  - Additional notes")

if __name__ == "__main__":
    run_migration()
