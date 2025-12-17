"""
Database migration to add preferred_letterhead_template column to users table.

This migration adds support for users to select their preferred letterhead template.
Default value is 'classic' to preserve existing behavior.
"""

from app.database import engine
from sqlalchemy import text


def migrate():
    """Add preferred_letterhead_template column to users table"""
    print("[MIGRATION] Adding preferred_letterhead_template column to users table...")

    try:
        with engine.connect() as conn:
            # Add column with default value
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS preferred_letterhead_template VARCHAR(50) DEFAULT 'classic'
            """))
            conn.commit()
            print("[OK] preferred_letterhead_template column added successfully")
            print("[INFO] Existing users will default to 'classic' template")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Remove preferred_letterhead_template column from users table"""
    print("[ROLLBACK] Removing preferred_letterhead_template column from users table...")

    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users
                DROP COLUMN IF EXISTS preferred_letterhead_template
            """))
            conn.commit()
            print("[OK] preferred_letterhead_template column removed successfully")
    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
