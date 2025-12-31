"""Test script to debug database fetch issues"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, engine
from app import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fetch_reports():
    """Test fetching reports from database"""
    db = SessionLocal()
    try:
        logger.info("Fetching all reports...")
        reports = db.query(models.Report).all()
        logger.info(f"Found {len(reports)} reports")

        if reports:
            for report in reports:
                logger.info(f"\nReport ID: {report.id}")
                logger.info(f"  User ID: {report.user_id}")
                logger.info(f"  Report Type: {report.report_type}")
                logger.info(f"  Status: {report.status}")
                logger.info(f"  Created: {report.created_at}")

                # Check for potential serialization issues
                try:
                    # Test JSON fields
                    if report.buildings:
                        logger.info(f"  Buildings: {type(report.buildings)} - {len(report.buildings) if isinstance(report.buildings, list) else 'Not a list'}")
                    if report.property_photos:
                        logger.info(f"  Property Photos: {type(report.property_photos)} - {len(report.property_photos) if isinstance(report.property_photos, list) else 'Not a list'}")
                except Exception as e:
                    logger.error(f"  ERROR accessing fields: {e}")
        else:
            logger.info("No reports found in database")

    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_fetch_reports()
