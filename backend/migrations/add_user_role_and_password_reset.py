"""
Migration: Add user role and password reset fields

This migration adds:
- role column for RBAC
- password_reset_token for password reset functionality
- password_reset_expires for token expiration
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL")


def run_migration():
    """Run the migration to add user role and password reset fields."""
    database_url = get_database_url()

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if role column already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'role'
            )
        """))
        role_exists = result.scalar()

        if not role_exists:
            print("Adding 'role' column to users table...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'
            """))
            print("Added 'role' column")
        else:
            print("Column 'role' already exists, skipping")

        # Check if password_reset_token column already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'password_reset_token'
            )
        """))
        token_exists = result.scalar()

        if not token_exists:
            print("Adding 'password_reset_token' column to users table...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN password_reset_token VARCHAR(100)
            """))
            print("Added 'password_reset_token' column")
        else:
            print("Column 'password_reset_token' already exists, skipping")

        # Check if password_reset_expires column already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'password_reset_expires'
            )
        """))
        expires_exists = result.scalar()

        if not expires_exists:
            print("Adding 'password_reset_expires' column to users table...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN password_reset_expires TIMESTAMP WITH TIME ZONE
            """))
            print("Added 'password_reset_expires' column")
        else:
            print("Column 'password_reset_expires' already exists, skipping")

        # Create index on role column for efficient queries
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE indexname = 'idx_users_role'
            )
        """))
        index_exists = result.scalar()

        if not index_exists:
            print("Creating index on 'role' column...")
            conn.execute(text("""
                CREATE INDEX idx_users_role ON users(role)
            """))
            print("Created index 'idx_users_role'")
        else:
            print("Index 'idx_users_role' already exists, skipping")

        conn.commit()

        print("Migration completed successfully!")
        return True


def rollback_migration():
    """Rollback the migration."""
    database_url = get_database_url()

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("Dropping index...")
        conn.execute(text("DROP INDEX IF EXISTS idx_users_role"))

        print("Dropping password_reset_expires column...")
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS password_reset_expires"))

        print("Dropping password_reset_token column...")
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS password_reset_token"))

        print("Dropping role column...")
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS role"))

        conn.commit()
        print("Rollback completed successfully!")
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="User role and password reset migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
