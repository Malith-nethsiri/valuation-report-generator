import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

# Check reports
with engine.connect() as conn:
    # Count total reports
    result = conn.execute(text("SELECT COUNT(*) FROM reports"))
    total_reports = result.scalar()
    print(f"Total reports in database: {total_reports}")

    # Get sample reports with user info
    result = conn.execute(text("""
        SELECT r.id, r.user_id, r.status, r.created_at, u.email
        FROM reports r
        LEFT JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        LIMIT 5
    """))

    print("\nRecent reports:")
    for row in result:
        print(f"  ID: {row[0]}, User: {row[4]}, Status: {row[2]}, Created: {row[3]}")

    # Check users
    result = conn.execute(text("SELECT id, email FROM users"))
    print("\nUsers in database:")
    for row in result:
        print(f"  ID: {row[0]}, Email: {row[1]}")
