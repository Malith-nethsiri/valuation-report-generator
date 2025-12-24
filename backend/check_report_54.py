import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

# Check report 54
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            id,
            status,
            buildings,
            valuation_buildings_data,
            property_photos,
            comparable_properties,
            deeds
        FROM reports
        WHERE id = 54
    """))

    row = result.fetchone()
    if row:
        print(f"Report ID: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"\nBuildings data:")
        if row[2]:
            print(json.dumps(row[2], indent=2))
        else:
            print("  NULL or empty")

        print(f"\nValuation buildings data:")
        if row[3]:
            print(json.dumps(row[3], indent=2))
        else:
            print("  NULL or empty")

        print(f"\nProperty photos:")
        if row[4]:
            print(f"  Count: {len(row[4])}")
        else:
            print("  NULL or empty")

        print(f"\nComparable properties:")
        if row[5]:
            print(f"  Count: {len(row[5])}")
        else:
            print("  NULL or empty")

        print(f"\nDeeds:")
        if row[6]:
            print(f"  Count: {len(row[6])}")
        else:
            print("  NULL or empty")
    else:
        print("Report 54 not found")
