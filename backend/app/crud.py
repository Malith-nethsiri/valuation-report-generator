from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from typing import List

# Validation Functions
def validate_report_buildings(buildings: List[dict]):
    """Validate building data including photos"""
    if not buildings:
        return

    for idx, building in enumerate(buildings):
        photos = building.get('building_photos', [])

        # Max 5 photos per building
        if len(photos) > 5:
            raise ValueError(
                f"Building {idx + 1} ('{building.get('building_name', 'Unnamed')}') "
                f"has {len(photos)} photos. Maximum is 5 per building."
            )

        # Validate photo structure
        for photo_idx, photo in enumerate(photos):
            required = ['id', 'image_data', 'order']
            missing = [f for f in required if f not in photo]
            if missing:
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: Missing required fields: {', '.join(missing)}"
                )

            # Validate image data format
            if not isinstance(photo['image_data'], str):
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: image_data must be a string (base64)"
                )

            if not photo['image_data'].startswith('data:image/'):
                raise ValueError(
                    f"Building {idx + 1}, Photo {photo_idx + 1}: Invalid image data format (must be data:image/...)"
                )

# User CRUD Operations
def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with hashed password"""
    hashed_password = get_password_hash(user.password)

    # Convert user data to dict and remove password field
    user_data = user.model_dump(exclude={"password"})

    # Create user with all fields from schema
    db_user = models.User(
        password_hash=hashed_password,
        **user_data
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    """Update user information"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# Report CRUD Operations
def create_report(db: Session, report: schemas.ReportCreate, user_id: int):
    """Create a new report for a user"""
    # Validate building photos before creating report
    if report.buildings:
        # Convert Building objects to dicts for validation
        buildings_dicts = [b.model_dump() for b in report.buildings]
        validate_report_buildings(buildings_dicts)

    db_report = models.Report(**report.model_dump(), user_id=user_id)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report(db: Session, report_id: int, user_id: int = None):
    """Get report by ID, optionally filtered by user_id"""
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)
    return query.first()

def get_user_reports(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all reports for a specific user"""
    return db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_all_reports(db: Session, skip: int = 0, limit: int = 100):
    """Get all reports (admin function)"""
    return db.query(models.Report).offset(skip).limit(limit).all()

def update_report(db: Session, report_id: int, report_update: schemas.ReportUpdate, user_id: int = None):
    """Update a report"""
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)

    db_report = query.first()
    if not db_report:
        return None

    update_data = report_update.model_dump(exclude_unset=True)

    # Validate building photos if buildings are being updated
    if 'buildings' in update_data and update_data['buildings']:
        # Convert Building objects to dicts for validation if needed
        buildings = update_data['buildings']
        if buildings and hasattr(buildings[0], 'model_dump'):
            buildings_dicts = [b.model_dump() for b in buildings]
        else:
            buildings_dicts = buildings
        validate_report_buildings(buildings_dicts)

    for field, value in update_data.items():
        setattr(db_report, field, value)

    db.commit()
    db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: int, user_id: int = None):
    """Delete a report"""
    query = db.query(models.Report).filter(models.Report.id == report_id)
    if user_id:
        query = query.filter(models.Report.user_id == user_id)

    db_report = query.first()
    if db_report:
        db.delete(db_report)
        db.commit()
        return True
    return False

# Legacy functions removed for clean v0.1 implementation
# All functionality moved to authenticated user + report system
