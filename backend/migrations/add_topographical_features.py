"""
Migration script to add topographical feature fields to the reports table.
Run this script once to add the new columns.

Usage: cd backend && ./venv/Scripts/python.exe migrations/add_topographical_features.py
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
        ADD COLUMN IF NOT EXISTS elevation_changes VARCHAR(50);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS drainage_pattern VARCHAR(50);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS vegetation_type VARCHAR(50);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS natural_features TEXT;
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

    print("\nMigration completed! Added topographical feature fields:")
    print("- elevation_changes (VARCHAR 50)")
    print("- drainage_pattern (VARCHAR 50)")
    print("- vegetation_type (VARCHAR 50)")
    print("- natural_features (TEXT)")

if __name__ == "__main__":
    run_migration()
