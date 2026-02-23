"""
DOCX generation dispatcher.

Routes report generation to the appropriate generator module in docx_generation/.
This file remains the public API: callers import generate_user_data_docx and
get_filename_for_user from here — zero changes required in routers or jobs.
"""

from io import BytesIO
from datetime import datetime
from typing import Optional

from . import models
import logging

logger = logging.getLogger(__name__)


def generate_user_data_docx(report: models.Report, user: Optional[models.User] = None) -> BytesIO:
    """
    Generate a formatted DOCX file from report and user data.
    Routes to the appropriate generator based on report type.

    Args:
        report: Report model instance
        user: Optional user model (uses report.user if not provided)

    Returns:
        BytesIO object containing the DOCX document
    """
    # Use the user from the report relationship if not provided
    if user is None:
        user = report.user

    # Route to appropriate generator based on report type
    if hasattr(report, 'report_type') and report.report_type == 'vehicle':
        logger.info("[DOCX] Generating vehicle report")
        from .docx_generation.vehicle_generator import generate_vehicle_report_docx
        return generate_vehicle_report_docx(report, user)

    # Route to multi-property generator if applicable
    if hasattr(report, 'is_multi_property') and report.is_multi_property:
        logger.info(f"[DOCX] Generating multi-property report with {report.property_count} properties")
        from .docx_generation.multi_property_generator import generate_multi_property_report_docx
        return generate_multi_property_report_docx(report, user)

    # Single-property path — normalize report_type before delegating
    logger.info("[DOCX] Generating single-property report")

    if not report.report_type:
        report.report_type = 'residential_property'
        logger.warning(f"[DOCX] Report {report.id} missing report_type, defaulting to residential_property")

    if report.report_type not in ['residential_property', 'bare_land', 'multi_property', 'vehicle']:
        logger.warning(f"[DOCX] Unknown report_type: {report.report_type}, treating as residential_property")
        report.report_type = 'residential_property'

    from .docx_generation.single_property_generator import generate_single_property_docx
    return generate_single_property_docx(report, user)


def get_filename_for_user(report: models.Report) -> str:
    """Generate a safe filename for the report document"""
    # Use applicant name if available, otherwise use valuer name
    name = report.applicant_full_name if report.applicant_full_name else report.user.full_name
    # Clean the name for use in filename
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_type = report.report_type.replace('_', '-')
    return f"{report_type}_{safe_name}_{timestamp}.docx"
