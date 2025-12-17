"""
Quick migration script to add missing database columns
"""
from app.database import engine
from sqlalchemy import text

def add_missing_columns():
    with engine.connect() as conn:
        # Add elevation_changes column if it doesn't exist
        try:
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS elevation_changes VARCHAR(50)
            """))
            conn.commit()
            print("[OK] elevation_changes column added successfully")
        except Exception as e:
            print(f"Error adding elevation_changes column: {e}")
            conn.rollback()

        # Add any other missing columns here if needed
        # Add drainage_pattern if missing
        try:
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS drainage_pattern VARCHAR(50)
            """))
            conn.commit()
            print("[OK] drainage_pattern column checked/added")
        except Exception as e:
            print(f"Error with drainage_pattern column: {e}")
            conn.rollback()

        # Add vegetation_type if missing
        try:
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS vegetation_type VARCHAR(50)
            """))
            conn.commit()
            print("[OK] vegetation_type column checked/added")
        except Exception as e:
            print(f"Error with vegetation_type column: {e}")
            conn.rollback()

        # Add natural_features if missing
        try:
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS natural_features TEXT
            """))
            conn.commit()
            print("[OK] natural_features column checked/added")
        except Exception as e:
            print(f"Error with natural_features column: {e}")
            conn.rollback()

if __name__ == "__main__":
    print("Adding missing database columns...")
    add_missing_columns()
    print("Migration complete!")
