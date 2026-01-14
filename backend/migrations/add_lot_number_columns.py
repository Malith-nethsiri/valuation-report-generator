"""
Add lot_number columns to reports and properties tables.
This must be run BEFORE migrate_lot_description_to_lot_number.py
"""

from sqlalchemy import text
from app.database import engine

def add_columns():
    """Add lot_number columns to database"""
    print("Adding lot_number columns to database...")

    try:
        with engine.connect() as conn:
            # Add column to reports table
            print("Adding lot_number column to reports table...")
            conn.execute(text(
                "ALTER TABLE reports ADD COLUMN IF NOT EXISTS lot_number VARCHAR(200);"
            ))

            # Add column to properties table
            print("Adding lot_number column to properties table...")
            conn.execute(text(
                "ALTER TABLE properties ADD COLUMN IF NOT EXISTS lot_number VARCHAR(200);"
            ))

            conn.commit()
            print("\nSuccess! Columns added successfully.")
            print("You can now run: python -m migrations.migrate_lot_description_to_lot_number")

    except Exception as e:
        print(f"\nError: {e}")
        return False

    return True

if __name__ == "__main__":
    add_columns()
