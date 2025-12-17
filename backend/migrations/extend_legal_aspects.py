"""
Migration script to extend legal aspects fields in the reports table.
Adds 16 new optional fields to support professional paragraph-format legal aspects.

Usage: cd backend && python migrations/extend_legal_aspects.py
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
        # Ownership-related fields (6 fields)
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS title_search_conducted VARCHAR(3);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS pedigree_search_conducted VARCHAR(3);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS valuation_basis_note TEXT;
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS property_encumbered VARCHAR(3);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS encumbrance_type VARCHAR(100);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS encumbrance_details TEXT;
        """,

        # Street Lines-related fields (3 fields)
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS street_lines_gazette_ref VARCHAR(100);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS street_lines_gazette_date VARCHAR(20);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS street_lines_impact_description TEXT;
        """,

        # Building Limits-related fields (5 fields)
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS building_distance_from_road VARCHAR(50);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS building_plan_approved VARCHAR(20);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS building_plan_reference VARCHAR(200);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS building_approval_authority VARCHAR(200);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS building_within_limits VARCHAR(3);
        """,

        # Local Authority-related fields (2 fields)
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS local_authority_rated VARCHAR(3);
        """,
        """
        ALTER TABLE reports
        ADD COLUMN IF NOT EXISTS local_authority_tax_levy TEXT;
        """,
    ]

    print("Starting Legal Aspects Extension Migration...")
    print(f"Total statements to execute: {len(migration_statements)}")
    print("-" * 60)

    with engine.connect() as conn:
        success_count = 0
        for i, stmt in enumerate(migration_statements, 1):
            try:
                conn.execute(text(stmt))
                conn.commit()
                # Extract column name for better output
                column_name = stmt.split("ADD COLUMN IF NOT EXISTS")[1].split()[0] if "ADD COLUMN" in stmt else "unknown"
                print(f"[{i}/{len(migration_statements)}] Added: {column_name}")
                success_count += 1
            except Exception as e:
                print(f"[{i}/{len(migration_statements)}] Warning: {str(e)[:100]}")

    print("-" * 60)
    print(f"\nMigration completed! Successfully added {success_count}/{len(migration_statements)} columns.")
    print("\nAdded Legal Aspects Extended Fields:")
    print("\nOwnership & Title (6 fields):")
    print("  - title_search_conducted (VARCHAR 3)")
    print("  - pedigree_search_conducted (VARCHAR 3)")
    print("  - valuation_basis_note (TEXT)")
    print("  - property_encumbered (VARCHAR 3)")
    print("  - encumbrance_type (VARCHAR 100)")
    print("  - encumbrance_details (TEXT)")
    print("\nStreet Lines (3 fields):")
    print("  - street_lines_gazette_ref (VARCHAR 100)")
    print("  - street_lines_gazette_date (VARCHAR 20)")
    print("  - street_lines_impact_description (TEXT)")
    print("\nBuilding Limits (5 fields):")
    print("  - building_distance_from_road (VARCHAR 50)")
    print("  - building_plan_approved (VARCHAR 20)")
    print("  - building_plan_reference (VARCHAR 200)")
    print("  - building_approval_authority (VARCHAR 200)")
    print("  - building_within_limits (VARCHAR 3)")
    print("\nLocal Authority (2 fields):")
    print("  - local_authority_rated (VARCHAR 3)")
    print("  - local_authority_tax_levy (TEXT)")
    print("\nAll fields are nullable and backward compatible with existing reports.")

if __name__ == "__main__":
    run_migration()
