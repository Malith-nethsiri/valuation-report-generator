"""
Admin router — endpoints restricted to admin role only.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, crud
from ..auth import require_admin, get_current_user
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[schemas.UserResponse])
async def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (Admin only)."""
    return db.query(models.User).offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def admin_get_user(
    user_id: int,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (Admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


@router.patch("/users/{user_id}/role", response_model=schemas.UserResponse)
async def admin_update_user_role(
    user_id: int,
    role_update: schemas.RoleUpdate,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user's role (Admin only). Role must be 'user' or 'admin'."""
    if role_update.role not in ['user', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    if user.id == admin_user.id and role_update.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin"
        )

    user.role = role_update.role
    db.commit()
    db.refresh(user)

    logger.info(f"Admin {admin_user.email} changed user {user.email} role to {role_update.role}")
    return user


@router.post("/migrate-rooms")
async def migrate_rooms_to_building_level(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Migrate all buildings from floor-based to building-level rooms."""
    try:
        from ..migrations.migrate_rooms_to_building_level import migrate_property_buildings

        reports = db.query(models.Report).filter(models.Report.buildings.isnot(None)).all()
        properties = db.query(models.Property).filter(models.Property.buildings.isnot(None)).all()

        migrated_reports = 0
        migrated_buildings = 0

        for report in reports:
            if report.buildings:
                original_building_count = len(report.buildings)
                report_data = {'buildings': report.buildings}
                migrated_data = migrate_property_buildings(report_data)
                report.buildings = migrated_data['buildings']
                migrated_reports += 1
                migrated_buildings += original_building_count

        for prop in properties:
            if prop.buildings:
                original_building_count = len(prop.buildings)
                property_data = {'buildings': prop.buildings}
                migrated_data = migrate_property_buildings(property_data)
                prop.buildings = migrated_data['buildings']
                migrated_buildings += original_building_count

        db.commit()

        return {
            "status": "success",
            "message": "Migration completed successfully",
            "reports_processed": migrated_reports,
            "properties_processed": len(properties),
            "total_buildings_migrated": migrated_buildings,
            "migrated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] Migration failed: {str(e)}")
        import traceback
        logger.error(f"[ERROR] Migration traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.post("/migrate-occupier")
async def migrate_occupier_to_building_level(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Migrate occupier information from property-level to building-level."""
    try:
        from ..migrations.migrate_occupier_to_building_level import migrate_report, migrate_property

        reports = db.query(models.Report).filter(
            models.Report.occupier_name.isnot(None),
            models.Report.buildings.isnot(None)
        ).all()

        properties = db.query(models.Property).filter(
            models.Property.occupier_name.isnot(None),
            models.Property.buildings.isnot(None)
        ).all()

        migrated_reports = 0
        migrated_properties = 0
        migrated_buildings = 0

        for report in reports:
            if report.buildings and report.occupier_name:
                report_data = {
                    'occupier_name': report.occupier_name,
                    'occupier_relationship': report.occupier_relationship,
                    'buildings': report.buildings
                }
                migrated_data = migrate_report(report_data)
                report.buildings = migrated_data['buildings']
                migrated_reports += 1
                migrated_buildings += len(report.buildings)

        for prop in properties:
            if prop.buildings and prop.occupier_name:
                property_data = {
                    'occupier_name': prop.occupier_name,
                    'occupier_relationship': prop.occupier_relationship,
                    'buildings': prop.buildings
                }
                migrated_data = migrate_property(property_data)
                prop.buildings = migrated_data['buildings']
                migrated_properties += 1
                migrated_buildings += len(prop.buildings)

        db.commit()

        return {
            "status": "success",
            "message": "Occupier migration completed successfully",
            "reports_processed": migrated_reports,
            "properties_processed": migrated_properties,
            "total_buildings_migrated": migrated_buildings,
            "migrated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] Occupier migration failed: {str(e)}")
        import traceback
        logger.error(f"[ERROR] Migration traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Occupier migration failed: {str(e)}"
        )
