"""
Property CRUD and report-property junction router.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import models, schemas, crud
from ..auth import get_current_user
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["properties"])


# ===== STANDALONE PROPERTY ENDPOINTS =====

@router.post("/api/properties", response_model=schemas.PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: schemas.PropertyCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property for the authenticated user."""
    logger.info(f"[CREATE PROPERTY] User: {current_user.email}")
    try:
        db_property = crud.create_property(db, property_data, current_user.id)
        logger.info(f"[CREATE PROPERTY] Property created with ID: {db_property.id}")
        return db_property
    except ValueError as e:
        logger.error(f"[CREATE PROPERTY] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"[CREATE PROPERTY] Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating property. Please try again."
        )


@router.get("/api/properties", response_model=list[schemas.PropertyResponse])
async def get_user_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all properties for the authenticated user (paginated)."""
    return crud.get_user_properties(db, current_user.id, skip=skip, limit=limit)


@router.get("/api/properties/templates", response_model=list[schemas.PropertyTemplateResponse])
async def get_property_templates(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all property templates (Property Library) for the authenticated user."""
    templates = crud.get_property_templates(db, current_user.id)
    return [
        schemas.PropertyTemplateResponse(
            id=p.id,
            template_name=p.template_name,
            property_village=p.property_village,
            property_district=p.property_district,
            land_extent_formatted=p.land_extent_formatted,
            last_valued_date=p.last_valued_date,
            valuation_market_value=p.valuation_market_value
        )
        for p in templates
    ]


@router.get("/api/properties/{property_id}", response_model=schemas.PropertyResponse)
async def get_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific property by ID (must belong to authenticated user)."""
    db_property = crud.get_property(db, property_id, current_user.id)
    if db_property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found"
        )
    return db_property


@router.put("/api/properties/{property_id}", response_model=schemas.PropertyResponse)
async def update_property(
    property_id: int,
    property_update: schemas.PropertyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a property (must belong to authenticated user)."""
    try:
        updated_property = crud.update_property(db, property_id, property_update, current_user.id)
        if not updated_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )
        return updated_property
    except ValueError as e:
        logger.error(f"[UPDATE PROPERTY] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/api/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a property (must belong to authenticated user, and not used in any reports)."""
    from ..services.audit_service import AuditService

    try:
        success = crud.delete_property(db, property_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with ID {property_id} not found"
            )

        await AuditService.log_resource_delete(
            db=db,
            user_id=current_user.id,
            resource_type="property",
            resource_id=property_id,
            request=request
        )

        return None
    except ValueError as e:
        logger.warning(f"[DELETE PROPERTY] Cannot delete: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch("/api/properties/{property_id}/status")
async def update_property_status(
    property_id: int,
    status_update: schemas.PropertyStatusUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the status of a property ('draft' or 'completed')."""
    logger.info(f"[UPDATE PROPERTY STATUS] Property: {property_id}")

    status_value = status_update.status

    try:
        db_property = crud.update_property_status(db, property_id, status_value, current_user.id)
        if not db_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found or access denied"
            )

        logger.info(f"  Status updated to: {status_value}")
        return {"status": "success", "property_id": property_id, "new_status": status_value}
    except ValueError as e:
        logger.error(f"[UPDATE PROPERTY STATUS] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ===== REPORT-PROPERTY JUNCTION ENDPOINTS =====

@router.post("/api/reports/{report_id}/properties/{property_id}", response_model=schemas.ReportPropertyResponse, status_code=status.HTTP_201_CREATED)
async def add_property_to_report(
    report_id: int,
    property_id: int,
    property_order: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an existing property to a report."""
    logger.info(f"[ADD PROPERTY TO REPORT] Report: {report_id}, Property: {property_id}")

    try:
        report_property = crud.add_property_to_report(
            db, report_id, property_id, current_user.id, property_order
        )
        logger.info(f"  Added with order: {report_property.property_order}")
        return report_property
    except ValueError as e:
        logger.error(f"[ADD PROPERTY TO REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/api/reports/{report_id}/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property_from_report(
    report_id: int,
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a property from a report."""
    logger.info(f"[REMOVE PROPERTY FROM REPORT] Report: {report_id}, Property: {property_id}")

    try:
        crud.remove_property_from_report(db, report_id, property_id, current_user.id)
        return None
    except ValueError as e:
        logger.error(f"[REMOVE PROPERTY FROM REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/api/reports/{report_id}/properties/reorder", status_code=status.HTTP_200_OK)
async def reorder_report_properties(
    report_id: int,
    property_order_map: dict[int, int],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder properties in a report (drag-drop support).

    Body: {"property_id": new_order, ...}
    """
    logger.info(f"[REORDER PROPERTIES] Report: {report_id}, New order: {property_order_map}")

    try:
        crud.reorder_report_properties(db, report_id, property_order_map, current_user.id)
        return {"status": "success", "message": "Properties reordered"}
    except ValueError as e:
        logger.error(f"[REORDER PROPERTIES] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/api/reports/{report_id}/properties/{property_id}", response_model=schemas.PropertyResponse)
async def update_report_property(
    report_id: int,
    property_id: int,
    property_update: schemas.PropertyUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an individual property within a report."""
    logger.info(f"[UPDATE REPORT PROPERTY] Report: {report_id}, Property: {property_id}")

    db_report = crud.get_report(db, report_id, current_user.id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied"
        )

    db_property = crud.update_property(db, property_id, property_update, current_user.id)
    if not db_property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or access denied"
        )

    logger.info(f"  Property updated successfully (status: {db_property.status})")
    return db_property


@router.post("/api/reports/{report_id}/properties/{property_id}/duplicate", response_model=schemas.PropertyResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_report_property(
    report_id: int,
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate a property within a report (deep copy including images)."""
    logger.info(f"[DUPLICATE PROPERTY] Report: {report_id}, Property: {property_id}")

    try:
        new_property = crud.duplicate_property(db, report_id, property_id, current_user.id)
        logger.info(f"  Property duplicated successfully (new ID: {new_property.id})")
        return new_property
    except ValueError as e:
        logger.error(f"[DUPLICATE PROPERTY] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/api/reports/{report_id}/properties", response_model=list[schemas.ReportPropertyResponse])
async def get_report_properties(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all properties for a report, ordered by property_order."""
    db_report = crud.get_report(db, report_id, current_user.id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    return crud.get_report_properties(db, report_id)
