"""
Background job service for async document generation.

Handles:
- Job creation and tracking
- Background DOCX/PDF generation
- Job status polling
- Cleanup of old jobs
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Job, JobStatus, Report, User
from ..database import SessionLocal
from .file_storage import FileStorage

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing background jobs."""

    @staticmethod
    def create_job(
        db: Session,
        user_id: int,
        report_id: int,
        job_type: str = "docx_generation"
    ) -> Job:
        """
        Create a new background job.

        Args:
            db: Database session
            user_id: ID of the user creating the job
            report_id: ID of the report to process
            job_type: Type of job (docx_generation, pdf_generation)

        Returns:
            Created Job object
        """
        job_id = str(uuid.uuid4())

        job = Job(
            id=job_id,
            user_id=user_id,
            report_id=report_id,
            job_type=job_type,
            status=JobStatus.PENDING.value,
            progress_percent=0,
            progress_message="Job queued"
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created job {job_id} for report {report_id}")
        return job

    @staticmethod
    def get_job(db: Session, job_id: str, user_id: Optional[int] = None) -> Optional[Job]:
        """
        Get a job by ID, optionally filtered by user.

        Args:
            db: Database session
            job_id: Job ID to find
            user_id: Optional user ID to filter by (for access control)

        Returns:
            Job object or None
        """
        query = db.query(Job).filter(Job.id == job_id)

        if user_id is not None:
            query = query.filter(Job.user_id == user_id)

        return query.first()

    @staticmethod
    def update_job_status(
        db: Session,
        job_id: str,
        status: str,
        progress_percent: Optional[int] = None,
        progress_message: Optional[str] = None,
        result_url: Optional[str] = None,
        result_filename: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update job status and progress.

        Args:
            db: Database session
            job_id: Job ID to update
            status: New status
            progress_percent: Optional progress percentage
            progress_message: Optional progress message
            result_url: Optional result file path
            result_filename: Optional original filename
            error_message: Optional error message

        Returns:
            Updated Job or None
        """
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            return None

        job.status = status

        if progress_percent is not None:
            job.progress_percent = progress_percent

        if progress_message is not None:
            job.progress_message = progress_message

        if result_url is not None:
            job.result_url = result_url

        if result_filename is not None:
            job.result_filename = result_filename

        if error_message is not None:
            job.error_message = error_message

        # Set timestamps based on status
        if status == JobStatus.PROCESSING.value and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)
        elif status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
            job.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)

        return job

    @staticmethod
    async def process_docx_job(job_id: str):
        """
        Background task to process DOCX generation job.

        Args:
            job_id: ID of the job to process
        """
        # Create a new database session for the background task
        db = SessionLocal()

        try:
            # Get the job
            job = db.query(Job).filter(Job.id == job_id).first()

            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Update to processing
            JobService.update_job_status(
                db, job_id,
                status=JobStatus.PROCESSING.value,
                progress_percent=10,
                progress_message="Starting document generation"
            )

            # Get the report
            report = db.query(Report).filter(Report.id == job.report_id).first()

            if not report:
                JobService.update_job_status(
                    db, job_id,
                    status=JobStatus.FAILED.value,
                    error_message="Report not found"
                )
                return

            # Get the user
            user = db.query(User).filter(User.id == job.user_id).first()

            if not user:
                JobService.update_job_status(
                    db, job_id,
                    status=JobStatus.FAILED.value,
                    error_message="User not found"
                )
                return

            # Update progress
            JobService.update_job_status(
                db, job_id,
                status=JobStatus.PROCESSING.value,
                progress_percent=30,
                progress_message="Loading report data"
            )

            # Import docx generator here to avoid circular imports
            from ..docx_generator import generate_user_data_docx, get_filename_for_user

            # Update progress
            JobService.update_job_status(
                db, job_id,
                status=JobStatus.PROCESSING.value,
                progress_percent=50,
                progress_message="Generating document"
            )

            # Generate the DOCX
            result = generate_user_data_docx(report, user)
            docx_bytes = result.getvalue() if hasattr(result, 'getvalue') else result
            filename = get_filename_for_user(report)

            # Update progress
            JobService.update_job_status(
                db, job_id,
                status=JobStatus.PROCESSING.value,
                progress_percent=80,
                progress_message="Saving document"
            )

            # Store the file
            file_path = FileStorage.store_file(
                content=docx_bytes,
                filename=filename,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            # Update job as completed
            JobService.update_job_status(
                db, job_id,
                status=JobStatus.COMPLETED.value,
                progress_percent=100,
                progress_message="Document ready",
                result_url=file_path,
                result_filename=filename
            )

            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")

            # Try to capture error in Sentry
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(e)
            except Exception as sentry_err:
                logger.debug(f"Sentry capture skipped (not configured or unavailable): {sentry_err}")

            # Update job as failed — if existing session is broken, retry with a fresh one
            try:
                JobService.update_job_status(
                    db, job_id,
                    status=JobStatus.FAILED.value,
                    error_message=str(e)
                )
            except Exception as status_err:
                logger.error(
                    f"[Job {job_id}] Failed to mark FAILED via existing session: {status_err}. "
                    f"Retrying with fresh session."
                )
                recovery_db = SessionLocal()
                try:
                    JobService.update_job_status(
                        recovery_db, job_id,
                        status=JobStatus.FAILED.value,
                        error_message=str(e)
                    )
                    logger.info(f"[Job {job_id}] Successfully marked as FAILED via recovery session.")
                except Exception as recovery_err:
                    logger.critical(
                        f"[Job {job_id}] CRITICAL: Failed to mark job as FAILED on both sessions. "
                        f"Job will remain stuck in PROCESSING. Recovery error: {recovery_err}"
                    )
                finally:
                    recovery_db.close()

        finally:
            db.close()

    @staticmethod
    def cleanup_old_jobs(db: Session, max_age_hours: int = 24) -> int:
        """
        Remove completed/failed jobs older than max_age_hours.

        Args:
            db: Database session
            max_age_hours: Maximum age of jobs to keep

        Returns:
            Number of jobs deleted
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        # Find old completed/failed jobs
        old_jobs = db.query(Job).filter(
            and_(
                Job.status.in_([JobStatus.COMPLETED.value, JobStatus.FAILED.value]),
                Job.completed_at < cutoff
            )
        ).all()

        count = 0
        for job in old_jobs:
            # Clean up associated files
            if job.result_url:
                try:
                    FileStorage.delete_file(job.result_url)
                except Exception as e:
                    logger.warning(f"Failed to delete file for job {job.id}: {e}")

            db.delete(job)
            count += 1

        if count > 0:
            db.commit()
            logger.info(f"Cleaned up {count} old jobs")

        return count

    @staticmethod
    def get_user_jobs(
        db: Session,
        user_id: int,
        limit: int = 10,
        status_filter: Optional[str] = None
    ):
        """
        Get recent jobs for a user.

        Args:
            db: Database session
            user_id: User ID to filter by
            limit: Maximum number of jobs to return
            status_filter: Optional status to filter by

        Returns:
            List of Job objects
        """
        query = db.query(Job).filter(Job.user_id == user_id)

        if status_filter:
            query = query.filter(Job.status == status_filter)

        return query.order_by(Job.created_at.desc()).limit(limit).all()


# Export
__all__ = ['JobService']
