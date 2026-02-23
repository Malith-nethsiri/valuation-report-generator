"""
Report CRUD and document generation router.
"""
import logging
import asyncio
import math
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas, crud
from ..auth import get_current_user
from ..database import get_db
from ..docx_generator import generate_user_data_docx, get_filename_for_user
from ..services.job_service import JobService

logger = logging.getLogger(__name__)
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: schemas.ReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new report for the authenticated user."""
    logger.info(f"[CREATE REPORT] Received data from frontend:")
    logger.debug(f"  property_village: {report_data.property_village}")
    logger.debug(f"  property_district: {report_data.property_district}")
    logger.debug(f"  buildings: {report_data.buildings}")
    logger.debug(f"  property_photos count: {len(report_data.property_photos) if report_data.property_photos else 0}")

    try:
        db_report = crud.create_report(db, report_data, current_user.id)
        logger.info(f"[CREATE REPORT] Report created with ID: {db_report.id}")
        return db_report
    except Exception as e:
        import traceback
        logger.error(f"[CREATE REPORT] Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating report. Please try again."
        )


@router.get("", response_model=schemas.PaginatedReportResponse)
async def get_user_reports(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(8, ge=1, le=100, description="Number of reports per page"),
    reference: Optional[str] = Query(None, description="Filter by report reference (exact match, case insensitive)"),
    applicant_name: Optional[str] = Query(None, description="Filter by applicant name (partial match)"),
    village: Optional[str] = Query(None, description="Filter by village name (partial match)"),
    report_date: Optional[str] = Query(None, description="Filter by report date (YYYY-MM-DD)"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get filtered and paginated reports for the authenticated user."""
    skip = (page - 1) * page_size

    reports, total, stats = crud.get_user_reports_filtered(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        reference=reference,
        applicant_name=applicant_name,
        village=village,
        report_date=report_date
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return schemas.PaginatedReportResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        stats=schemas.ReportStats(**stats)
    )


@router.get("/adjacent-date")
async def get_adjacent_report_date(
    current_date: str = Query(..., description="Current date in YYYY-MM-DD format"),
    direction: str = Query(..., pattern="^(next|previous)$", description="Direction: 'next' or 'previous'"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the next or previous date that has reports for date filter navigation."""
    adjacent_date = crud.get_adjacent_report_date(
        db=db,
        user_id=current_user.id,
        current_date=current_date,
        direction=direction
    )
    return {"adjacent_date": adjacent_date}


@router.post("/multi-property", response_model=schemas.MultiPropertyReportResponse, status_code=status.HTTP_201_CREATED)
async def create_multi_property_report(
    report_data: schemas.MultiPropertyReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a multi-property report with existing or new properties."""
    logger.info(f"[CREATE MULTI-PROPERTY REPORT] User: {current_user.email}")
    logger.info(f"  Property IDs: {report_data.property_ids}")
    logger.info(f"  New properties: {len(report_data.properties or [])}")

    try:
        db_report = crud.create_multi_property_report(db, report_data, current_user.id)
        logger.info(f"[CREATE MULTI-PROPERTY REPORT] Report created with ID: {db_report.id}")

        response = schemas.MultiPropertyReportResponse(
            id=db_report.id,
            is_multi_property=db_report.is_multi_property,
            property_count=db_report.property_count,
            total_valuation_amount=db_report.total_valuation_amount,
            properties=[rp.property for rp in db_report.property_associations],
            invoice_data=db_report.invoice_data
        )
        return response
    except ValueError as e:
        logger.error(f"[CREATE MULTI-PROPERTY REPORT] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"[CREATE MULTI-PROPERTY REPORT] Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating multi-property report. Please try again."
        )


@router.get("/{report_id}")
async def get_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific report by ID (must belong to authenticated user)."""
    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    if db_report.is_multi_property:
        properties = db_report.properties
        response_data = {
            **{key: getattr(db_report, key) for key in db_report.__dict__ if not key.startswith('_')},
            'properties': properties
        }
        return response_data

    return db_report


@router.put("/{report_id}")
async def update_report(
    report_id: int,
    request_body: schemas.ReportUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a report (must belong to authenticated user).

    Security: Uses ReportUpdateRequest schema with extra='forbid' to prevent
    injection of internal fields like user_id, id, or other protected fields.

    Concurrency: Uses pessimistic locking (SELECT FOR UPDATE) to prevent race
    conditions when multiple requests try to modify the same report.
    """
    logger.info(f"[UPDATE_REPORT] Received PUT request for report {report_id}")

    try:
        request_dict = request_body.model_dump(exclude={'properties', 'property_metadata'}, exclude_unset=True)
        logger.info(f"[UPDATE_REPORT] Request body keys: {list(request_dict.keys())}")

        properties_data = request_body.properties
        property_metadata = request_body.property_metadata

        logger.info(f"[UPDATE_REPORT] Properties data present: {properties_data is not None}")

        if properties_data:
            request_dict['is_multi_property'] = True
            request_dict['property_count'] = len(properties_data)

        report_update = schemas.ReportUpdate(**request_dict)
        updated_report = crud.update_report(db, report_id, report_update, current_user.id, use_locking=True)
        if not updated_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID {report_id} not found"
            )

        if properties_data:
            logger.info(f"[UPDATE_REPORT] Updating properties for multi-property report {report_id}")

            current_property_ids = {rp.property_id for rp in updated_report.property_associations}
            incoming_property_ids = {
                prop_data.get('id') for prop_data in properties_data
                if prop_data.get('id') and isinstance(prop_data.get('id'), int)
            }

            properties_to_delete = current_property_ids - incoming_property_ids

            for property_id in properties_to_delete:
                db.query(models.ReportProperty).filter(
                    models.ReportProperty.report_id == report_id,
                    models.ReportProperty.property_id == property_id
                ).delete()

                property_to_check = db.query(models.Property).filter(
                    models.Property.id == property_id
                ).with_for_update().first()

                if property_to_check:
                    property_usage_count = db.query(models.ReportProperty).filter(
                        models.ReportProperty.property_id == property_id
                    ).count()

                    if property_usage_count == 0:
                        db.delete(property_to_check)

            for idx, prop_data in enumerate(properties_data):
                property_id = prop_data.get('id')

                if property_id and isinstance(property_id, int):
                    property_update = schemas.PropertyUpdate(**prop_data)
                    crud.update_property(db, property_id, property_update, current_user.id)
                else:
                    property_create = schemas.PropertyCreate(**prop_data)
                    new_property = crud.create_property(db, property_create, current_user.id)

                    property_order = prop_data.get('property_order', idx + 1)
                    report_property = models.ReportProperty(
                        report_id=report_id,
                        property_id=new_property.id,
                        property_order=property_order
                    )
                    db.add(report_property)

        db.commit()
        db.refresh(updated_report)

        if updated_report.is_multi_property:
            properties = updated_report.properties
            response_data = {
                **{key: getattr(updated_report, key) for key in updated_report.__dict__ if not key.startswith('_')},
                'properties': properties
            }
            return response_data

        return updated_report

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[UPDATE_REPORT] Transaction failed for report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update report due to a server error"
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a report (must belong to authenticated user)."""
    from ..services.audit_service import AuditService

    success = crud.delete_report(db, report_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    await AuditService.log_resource_delete(
        db=db,
        user_id=current_user.id,
        resource_type="report",
        resource_id=report_id,
        request=request
    )

    return None


@router.post("/{report_id}/duplicate", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate an existing report as a new draft."""
    logger.info(f"[DUPLICATE_REPORT] User {current_user.email} duplicating report {report_id}")

    new_report = crud.duplicate_report(db, report_id, current_user.id)
    if not new_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    logger.info(f"[DUPLICATE_REPORT] Successfully created duplicate report {new_report.id}")
    return new_report


@router.post("/{report_id}/generate")
async def generate_report_docx(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a DOCX file from report data (synchronous).

    For production use prefer /generate-async which uses background jobs.
    """
    if IS_PRODUCTION:
        logger.warning(
            f"[DOCX_GENERATION] Sync endpoint used in production by user={current_user.email}. "
            "Consider using /api/reports/{report_id}/generate-async for better scalability."
        )

    logger.info(f"[DOCX_GENERATION] Starting generation for report_id={report_id}, user={current_user.email}")

    db_report = crud.get_report(db, report_id, current_user.id, eager_load_for_docx=True)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    logger.info(f"[DOCX_GENERATION] Report found - status: {db_report.status}, type: {db_report.report_type}")

    try:
        docx_stream = await asyncio.to_thread(generate_user_data_docx, db_report, current_user)
        logger.info(f"[DOCX_GENERATION] DOCX generated successfully, size: {len(docx_stream.getvalue())} bytes")

        filename = get_filename_for_user(db_report)

        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        import traceback
        logger.error(f"[DOCX_GENERATION_ERROR] Error type: {type(e).__name__}")
        logger.error(f"[DOCX_GENERATION_ERROR] Error message: {str(e)}")
        logger.error(f"[DOCX_GENERATION_ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating DOCX file. Please try again."
        )


@router.post("/{report_id}/generate-async", response_model=schemas.JobResponse)
async def generate_report_docx_async(
    report_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start async DOCX generation job for a report. Returns immediately with a job_id."""
    logger.info(f"[ASYNC_DOCX] Starting async generation for report_id={report_id}, user={current_user.email}")

    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    job = JobService.create_job(
        db=db,
        user_id=current_user.id,
        report_id=report_id,
        job_type="docx_generation"
    )

    background_tasks.add_task(JobService.process_docx_job, job.id)

    logger.info(f"[ASYNC_DOCX] Job {job.id} created and queued")
    return job
