"""
Audit logging service for tracking sensitive operations.

Provides a simple interface to log security-relevant events:
- User authentication (login, logout, password changes)
- Resource modifications (create, update, delete)
- Role changes
- Data exports

Usage:
    from app.services.audit_service import AuditService

    # Log a report deletion
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        action="delete",
        resource_type="report",
        resource_id=report_id,
        description="User deleted report",
        request=request  # Optional FastAPI request for IP/user-agent
    )
"""

import logging
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from fastapi import Request

from .. import models
from ..database import SessionLocal

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating audit log entries."""

    @staticmethod
    async def log(
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> models.AuditLog:
        """
        Create an audit log entry.

        Args:
            db: Database session
            user_id: ID of the user performing the action (None for anonymous)
            action: Type of action (create, update, delete, login, etc.)
            resource_type: Type of resource affected (report, property, user, etc.)
            resource_id: ID of the affected resource (optional)
            description: Human-readable description of the action
            details: Additional structured data (e.g., changed fields)
            request: FastAPI request object for IP/user-agent extraction
            success: Whether the action was successful
            error_message: Error message if success=False

        Returns:
            Created AuditLog entry
        """
        # Use an independent session so audit entries are never rolled back
        # if the caller's business transaction fails.
        audit_db = SessionLocal()
        try:
            # Extract request context
            ip_address = None
            user_agent = None
            request_id = None

            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent", "")[:500]
                request_id = getattr(request.state, "request_id", None)

            # Create audit log entry
            audit_log = models.AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                success=success,
                error_message=error_message
            )

            audit_db.add(audit_log)
            audit_db.commit()
            audit_db.refresh(audit_log)

            # Log for debugging
            logger.info(
                f"[AUDIT] user={user_id} action={action} "
                f"resource={resource_type}:{resource_id} "
                f"success={success}"
            )

            return audit_log

        except Exception as e:
            # Don't let audit logging failures break the application
            logger.error(f"[AUDIT ERROR] Failed to create audit log: {str(e)}")
            audit_db.rollback()
            return None
        finally:
            audit_db.close()

    @staticmethod
    async def log_login(
        db: Session,
        user_id: int,
        request: Request,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> models.AuditLog:
        """Log a login attempt."""
        return await AuditService.log(
            db=db,
            user_id=user_id if success else None,
            action="login",
            resource_type="user",
            resource_id=user_id,
            description=f"{'Successful' if success else 'Failed'} login attempt",
            request=request,
            success=success,
            error_message=error_message
        )

    @staticmethod
    async def log_password_change(
        db: Session,
        user_id: int,
        request: Request,
        is_reset: bool = False
    ) -> models.AuditLog:
        """Log a password change or reset."""
        action = "password_reset" if is_reset else "password_change"
        return await AuditService.log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            description=f"User {'reset' if is_reset else 'changed'} password",
            request=request
        )

    @staticmethod
    async def log_role_change(
        db: Session,
        admin_user_id: int,
        target_user_id: int,
        old_role: str,
        new_role: str,
        request: Request
    ) -> models.AuditLog:
        """Log a role change."""
        return await AuditService.log(
            db=db,
            user_id=admin_user_id,
            action="role_change",
            resource_type="user",
            resource_id=target_user_id,
            description=f"Changed user role from {old_role} to {new_role}",
            details={"old_role": old_role, "new_role": new_role},
            request=request
        )

    @staticmethod
    async def log_resource_delete(
        db: Session,
        user_id: int,
        resource_type: str,
        resource_id: int,
        request: Request,
        details: Optional[Dict[str, Any]] = None
    ) -> models.AuditLog:
        """Log a resource deletion."""
        return await AuditService.log(
            db=db,
            user_id=user_id,
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            description=f"Deleted {resource_type} {resource_id}",
            details=details,
            request=request
        )

    @staticmethod
    async def log_bank_account_change(
        db: Session,
        user_id: int,
        action: str,
        bank_account_id: Optional[str],
        request: Request,
        details: Optional[Dict[str, Any]] = None
    ) -> models.AuditLog:
        """Log a bank account modification."""
        return await AuditService.log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="bank_account",
            resource_id=None,  # Bank accounts use string IDs
            description=f"{action.capitalize()} bank account {bank_account_id}",
            details={"bank_account_id": bank_account_id, **(details or {})},
            request=request
        )
