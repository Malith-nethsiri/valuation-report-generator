"""
Migration script to add access_road_classes_detected column to the reports table.
This column stores auto-detected road classifications for analytics.

Run this script once to add the new column.

Usage: cd backend && python migrations/add_access_road_classes_detected.py
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
        ADD COLUMN IF NOT EXISTS access_road_classes_detected JSON;
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
    print("  - access_road_classes_detected JSON (nullable)")
    print("\nThis column stores auto-detected road classifications for analytics:")
    print("  - Main road classification, number, name, and confidence")
    print("  - Secondary roads information")

if __name__ == "__main__":
    run_migration()
