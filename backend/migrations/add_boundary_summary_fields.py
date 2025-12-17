"""
Migration script to add boundary summary fields to the reports table.
Run this script once to add the new columns.

Usage: cd backend && ./venv/Scripts/python.exe migrations/add_boundary_summary_fields.py
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
        ADD COLUMN IF NOT EXISTS boundary_types_per_direction JSON;
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS entrance_type VARCHAR(100);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS boundaries_summary_text TEXT;
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

    print("\nMigration completed!")

if __name__ == "__main__":
    run_migration()
