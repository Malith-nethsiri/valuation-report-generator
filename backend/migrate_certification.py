"""
Migration script to add certification fields to the reports table.
This script can be run to add the certification columns if they don't exist.

Usage:
    python migrate_certification.py
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable is not set")
    print("Please create a .env file with your DATABASE_URL")
    sys.exit(1)

# Create engine
try:
    engine = create_engine(DATABASE_URL)
    print("✓ Connected to database")
except Exception as e:
    print(f"❌ Failed to connect to database: {e}")
    sys.exit(1)

# Check which columns need to be added
certification_columns = {
    'certification_text': 'TEXT',
    'certificate_survey_plan_ref': 'VARCHAR(200)',
    'certificate_survey_plan_date': 'VARCHAR(50)',
    'certificate_identity_confirmed': 'BOOLEAN DEFAULT FALSE',
    'certification_valuer_name': 'VARCHAR(300)',
    'certification_valuer_designation': 'VARCHAR(200)',
    'certification_date': 'VARCHAR(50)'
}

print("\n🔍 Checking existing columns in reports table...")

# Get existing columns
inspector = inspect(engine)
existing_columns = [col['name'] for col in inspector.get_columns('reports')]

print(f"Found {len(existing_columns)} existing columns in reports table")

# Determine which columns need to be added
columns_to_add = {
    name: sql_type
    for name, sql_type in certification_columns.items()
    if name not in existing_columns
}

if not columns_to_add:
    print("\n✅ All certification columns already exist!")
    print("No migration needed.")
    sys.exit(0)

print(f"\n📝 Need to add {len(columns_to_add)} certification columns:")
for col_name in columns_to_add.keys():
    print(f"  - {col_name}")

# Add the missing columns
with engine.connect() as conn:
    for col_name, sql_type in columns_to_add.items():
        try:
            sql = f"ALTER TABLE reports ADD COLUMN {col_name} {sql_type}"
            conn.execute(text(sql))
            conn.commit()
            print(f"  ✓ Added column: {col_name}")
        except Exception as e:
            print(f"  ❌ Failed to add column {col_name}: {e}")
            conn.rollback()

# Verify the columns were added
print("\n🔍 Verifying certification columns...")
inspector = inspect(engine)
current_columns = [col['name'] for col in inspector.get_columns('reports')]
certification_cols = [col for col in current_columns if col.startswith('certif')]

print(f"\nCertification columns in reports table ({len(certification_cols)}):")
for col in certification_cols:
    print(f"  ✓ {col}")

print("\n✅ Migration completed successfully!")
print("You can now restart your backend server to use the certification feature.")
