"""
Vehicle CRUD and report-vehicle junction router.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas, crud
from ..auth import get_current_user
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vehicles"])


# ===== STANDALONE VEHICLE ENDPOINTS =====

@router.post("/api/vehicles", response_model=schemas.VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: schemas.VehicleCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new vehicle for the authenticated user."""
    logger.info(f"[CREATE VEHICLE] User: {current_user.email}")
    try:
        db_vehicle = crud.create_vehicle(db, vehicle_data, current_user.id)
        logger.info(f"[CREATE VEHICLE] Vehicle created with ID: {db_vehicle.id}")
        return db_vehicle
    except ValueError as e:
        logger.error(f"[CREATE VEHICLE] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"[CREATE VEHICLE] Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating vehicle. Please try again."
        )


@router.get("/api/vehicles", response_model=list[schemas.VehicleResponse])
async def get_user_vehicles(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vehicles for the authenticated user (paginated)."""
    return crud.get_user_vehicles(db, current_user.id, skip=skip, limit=limit)


@router.get("/api/vehicles/templates", response_model=list[schemas.VehicleTemplateResponse])
async def get_vehicle_templates(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vehicle templates (Vehicle Library) for the authenticated user."""
    templates = crud.get_vehicle_templates(db, current_user.id)
    return [
        schemas.VehicleTemplateResponse(
            id=v.id,
            make=v.make,
            model=v.model,
            registration_number=v.registration_number,
            year_of_manufacture=v.year_of_manufacture,
            market_value=float(v.market_value) if v.market_value else None,
            created_at=v.created_at
        )
        for v in templates
    ]


@router.get("/api/vehicles/{vehicle_id}", response_model=schemas.VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific vehicle by ID (must belong to authenticated user)."""
    db_vehicle = crud.get_vehicle(db, vehicle_id, current_user.id)
    if db_vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )
    return db_vehicle


@router.put("/api/vehicles/{vehicle_id}", response_model=schemas.VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    vehicle_update: schemas.VehicleUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a vehicle (must belong to authenticated user)."""
    try:
        updated_vehicle = crud.update_vehicle(db, vehicle_id, vehicle_update, current_user.id)
        if not updated_vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} not found"
            )
        return updated_vehicle
    except ValueError as e:
        logger.error(f"[UPDATE VEHICLE] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/api/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: int,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a vehicle (soft delete by default, must belong to authenticated user)."""
    try:
        success = crud.delete_vehicle(db, vehicle_id, current_user.id, soft_delete=not hard_delete)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} not found"
            )
        return None
    except ValueError as e:
        logger.warning(f"[DELETE VEHICLE] Cannot delete: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/api/vehicles/{vehicle_id}/duplicate", response_model=schemas.VehicleResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_vehicle(
    vehicle_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate a vehicle (create a copy)."""
    logger.info(f"[DUPLICATE VEHICLE] Vehicle: {vehicle_id}")

    new_vehicle = crud.duplicate_vehicle(db, vehicle_id, current_user.id)
    if not new_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )

    logger.info(f"  Vehicle duplicated successfully (new ID: {new_vehicle.id})")
    return new_vehicle


@router.post("/api/vehicles/{vehicle_id}/suggest-valuation", response_model=schemas.VehicleValuationSuggestion)
async def suggest_vehicle_valuation(
    vehicle_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-suggested valuation for a vehicle."""
    logger.info(f"[SUGGEST VEHICLE VALUATION] Vehicle: {vehicle_id}")

    db_vehicle = crud.get_vehicle(db, vehicle_id, current_user.id)
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found"
        )

    try:
        from ..services.ai_valuation import suggest_vehicle_valuation as ai_suggest
        suggestion = await ai_suggest(db_vehicle)
        logger.info(f"  Valuation suggestion generated: Market Value={suggestion.get('suggested_market_value')}")
        return suggestion
    except ImportError:
        logger.warning("  AI valuation service not available, returning placeholder")
        return schemas.VehicleValuationSuggestion(
            suggested_market_value=None,
            suggested_forced_sale_value=None,
            suggested_brand_new_price=None,
            valuation_summary="By considering the above facts, the market value of the vehicle valued is estimated.",
            confidence=None,
            reasoning="AI valuation service not available. Please enter values manually."
        )
    except Exception as e:
        logger.error(f"[SUGGEST VEHICLE VALUATION] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating valuation suggestion: {str(e)}"
        )


# ===== REPORT-VEHICLE JUNCTION ENDPOINTS =====

@router.post("/api/reports/{report_id}/vehicles/{vehicle_id}", response_model=schemas.ReportVehicleResponse, status_code=status.HTTP_201_CREATED)
async def add_vehicle_to_report(
    report_id: int,
    vehicle_id: int,
    vehicle_order: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an existing vehicle to a report."""
    logger.info(f"[ADD VEHICLE TO REPORT] Report: {report_id}, Vehicle: {vehicle_id}")

    try:
        report_vehicle = crud.add_vehicle_to_report(
            db, report_id, vehicle_id, current_user.id, vehicle_order
        )
        logger.info(f"  Added with order: {report_vehicle.vehicle_order}")
        return report_vehicle
    except ValueError as e:
        logger.error(f"[ADD VEHICLE TO REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/api/reports/{report_id}/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vehicle_from_report(
    report_id: int,
    vehicle_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a vehicle from a report."""
    logger.info(f"[REMOVE VEHICLE FROM REPORT] Report: {report_id}, Vehicle: {vehicle_id}")

    try:
        crud.remove_vehicle_from_report(db, report_id, vehicle_id, current_user.id)
        return None
    except ValueError as e:
        logger.error(f"[REMOVE VEHICLE FROM REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/api/reports/{report_id}/vehicles/reorder", status_code=status.HTTP_200_OK)
async def reorder_report_vehicles(
    report_id: int,
    vehicle_order_map: dict[int, int],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder vehicles in a report (drag-drop support).

    Body: {"vehicle_id": new_order, ...}
    """
    logger.info(f"[REORDER VEHICLES] Report: {report_id}, New order: {vehicle_order_map}")

    try:
        crud.reorder_report_vehicles(db, report_id, vehicle_order_map, current_user.id)
        return {"status": "success", "message": "Vehicles reordered"}
    except ValueError as e:
        logger.error(f"[REORDER VEHICLES] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/api/reports/{report_id}/vehicles", response_model=list[schemas.ReportVehicleResponse])
async def get_report_vehicles(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vehicles for a report, ordered by vehicle_order."""
    db_report = crud.get_report(db, report_id, current_user.id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    return crud.get_report_vehicles(db, report_id)


@router.put("/api/reports/{report_id}/vehicles/{vehicle_id}", response_model=schemas.VehicleResponse)
async def update_report_vehicle(
    report_id: int,
    vehicle_id: int,
    vehicle_update: schemas.VehicleUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an individual vehicle within a report."""
    logger.info(f"[UPDATE REPORT VEHICLE] Report: {report_id}, Vehicle: {vehicle_id}")

    db_report = crud.get_report(db, report_id, current_user.id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied"
        )

    db_vehicle = crud.update_vehicle(db, vehicle_id, vehicle_update, current_user.id)
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found or access denied"
        )

    logger.info(f"  Vehicle updated successfully (status: {db_vehicle.status})")
    return db_vehicle
