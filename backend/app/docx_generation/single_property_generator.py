"""
Single-property valuation report DOCX generation entry point.
"""
from io import BytesIO
from typing import Optional
import logging

from docx import Document

from .. import models
from ..letterhead_templates import get_template
from .cover_page import render_cover_page
from .document_builder import render_body_sections

logger = logging.getLogger(__name__)


def generate_single_property_docx(report: models.Report, user: Optional[models.User] = None) -> BytesIO:
    """
    Generate a formatted DOCX file for a single-property valuation report.
    Called by generate_user_data_docx dispatcher after routing.
    """
    try:
        doc = Document()

        # ===== LETTERHEAD =====
        template_id = (user.preferred_letterhead_template or 'classic') if user else 'classic'
        template = get_template(template_id)
        template.render_letterhead(doc, user, report)

        # ===== COVER PAGE (opening section) =====
        render_cover_page(doc, report)

        # ===== BODY SECTIONS (1.0–9.0 + invoice) =====
        render_body_sections(doc, report, user)

        # ===== SAVE DOCUMENT =====
        logger.info("[DOCX] About to save document to BytesIO")
        file_stream = BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        if file_stream.getvalue() == b'':
            raise ValueError("Generated document is empty or None")

        logger.info(f"Document generated successfully, size: {len(file_stream.getvalue())} bytes")
        return file_stream

    except AttributeError as e:
        logger.error(f"Missing required field in report generation: {e}", exc_info=True)
        raise ValueError(f"Report data incomplete: Missing field - {str(e)}")
    except IndexError as e:
        logger.error(f"Array access error in report generation: {e}", exc_info=True)
        raise ValueError(f"Report data malformed: Array indexing error - {str(e)}")
    except TypeError as e:
        logger.error(f"Type error in report data: {e}", exc_info=True)
        raise ValueError(f"Report data has incorrect types: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in DOCX generation: {e}", exc_info=True)
        raise
