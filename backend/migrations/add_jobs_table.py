"""
Migration: Add jobs table for async document generation

This migration creates the jobs table used for tracking background
document generation tasks.
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
    """Run the migration to add jobs table."""
    database_url = get_database_url()

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'jobs'
            )
        """))
        exists = result.scalar()

        if exists:
            print("Table 'jobs' already exists, skipping creation")
            return True

        # Create the jobs table
        print("Creating 'jobs' table...")

        conn.execute(text("""
            CREATE TABLE jobs (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
                job_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                result_url VARCHAR(500),
                result_filename VARCHAR(255),
                error_message TEXT,
                progress_percent INTEGER DEFAULT 0,
                progress_message VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Create indexes for common queries
        print("Creating indexes...")

        conn.execute(text("""
            CREATE INDEX idx_jobs_user_id ON jobs(user_id)
        """))

        conn.execute(text("""
            CREATE INDEX idx_jobs_report_id ON jobs(report_id)
        """))

        conn.execute(text("""
            CREATE INDEX idx_jobs_status ON jobs(status)
        """))

        conn.execute(text("""
            CREATE INDEX idx_jobs_created_at ON jobs(created_at)
        """))

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
        print("Dropping 'jobs' table...")
        conn.execute(text("DROP TABLE IF EXISTS jobs CASCADE"))
        conn.commit()
        print("Rollback completed successfully!")
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Jobs table migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
