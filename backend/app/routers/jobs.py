"""
Background job status and download router.
"""
import logging
from typing import Optional, List
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..services.job_service import JobService
from ..services.file_storage import FileStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=schemas.JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the status of a background job. Used for polling document generation progress."""
    job = JobService.get_job(db, job_id, current_user.id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    download_ready = job.status == "completed" and job.result_url is not None

    return schemas.JobStatusResponse(
        id=job.id,
        status=job.status,
        progress_percent=job.progress_percent or 0,
        progress_message=job.progress_message,
        error_message=job.error_message,
        download_ready=download_ready,
        download_url=f"/api/jobs/{job.id}/download" if download_ready else None,
        filename=job.result_filename
    )


@router.get("/{job_id}/download")
async def download_job_result(
    job_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the result of a completed job."""
    job = JobService.get_job(db, job_id, current_user.id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job.status})"
        )

    if not job.result_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job result not available"
        )

    result = FileStorage.get_file(job.result_url)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File has expired or been deleted"
        )

    content, filename, content_type = result

    return StreamingResponse(
        BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("", response_model=List[schemas.JobResponse])
async def list_user_jobs(
    limit: int = 10,
    status_filter: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List recent jobs for the current user."""
    jobs = JobService.get_user_jobs(
        db=db,
        user_id=current_user.id,
        limit=min(limit, 50),
        status_filter=status_filter
    )
    return jobs
