"""
OCR document processing router.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..services.ocr import process_multiple_documents
from ..utils.extent_calculator import calculate_extent_data
from ..utils.upload_validator import MAX_FILES_PER_UPLOAD, validate_upload_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/extract")
async def extract_data_from_document(
    files: List[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract property data from uploaded documents using OCR.

    - **files**: Multiple image files (JPEG, PNG, WEBP, PDF) - max 10 files, 10MB each
    - **document_type**: Optional hint ('survey_plan', 'deed', 'title_certificate')
    """
    try:
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many files uploaded. Maximum {MAX_FILES_PER_UPLOAD} files allowed, got {len(files)} files"
            )

        for file in files:
            await validate_upload_file(file)

        result = await process_multiple_documents(files, document_type)

        if result is None:
            logger.error("[OCR_ENDPOINT] process_multiple_documents returned None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OCR processing returned None - server may be reloading. Please try again in a few seconds."
            )

        if not isinstance(result, dict):
            logger.error(f"[OCR_ENDPOINT] Invalid result type: {type(result)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing returned unexpected type: {type(result)}. Server may be reloading."
            )

        success = result.get('success') if isinstance(result, dict) else False
        if not success:
            error_msg = result.get('error', 'OCR processing failed') if isinstance(result, dict) else 'Unknown error'
            logger.error(f"[OCR_ENDPOINT] Processing failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        extracted_data = result.get('extracted_data', {})
        if extracted_data.get('land_extent_acres') is not None:
            extent_data = calculate_extent_data(
                acres=extracted_data.get('land_extent_acres', 0),
                roods=extracted_data.get('land_extent_roods', 0),
                perches=extracted_data.get('land_extent_perches', 0)
            )
            extracted_data.update(extent_data)
            result['extracted_data'] = extracted_data

        return {
            "status": "success",
            "message": "Document processed successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_str = str(e).lower()

        logger.error(f"[OCR_ERROR] Full traceback:\n{error_trace}")

        error_code = "OCR_UNKNOWN_ERROR"
        user_message = "Document processing failed. Please try again."
        retry_after = None

        if "api_key" in error_str or "authentication" in error_str:
            error_code = "GOOGLE_VISION_AUTH_ERROR"
            user_message = "OCR service configuration error. Please contact support."
        elif "quota" in error_str or "limit" in error_str or "429" in error_str:
            error_code = "GOOGLE_VISION_RATE_LIMIT"
            user_message = "OCR service is temporarily overloaded. Please try again in a few minutes."
            retry_after = 60
        elif "timeout" in error_str or "timed out" in error_str:
            error_code = "GOOGLE_VISION_TIMEOUT"
            user_message = "OCR request timed out. The document may be too complex. Try uploading smaller files."
            retry_after = 30
        elif "anthropic" in error_str or "claude" in error_str:
            error_code = "AI_PARSING_ERROR"
            user_message = "AI document parsing failed. Please try again."
            retry_after = 10
        elif "file" in error_str or "decode" in error_str or "corrupt" in error_str:
            error_code = "FILE_PROCESSING_ERROR"
            user_message = "Could not process the document. Please ensure it's a valid image or PDF file."
        elif "connection" in error_str or "network" in error_str:
            error_code = "NETWORK_ERROR"
            user_message = "Network error during OCR processing. Please check your connection and try again."
            retry_after = 5

        error_detail = {"error_code": error_code, "message": user_message}
        if retry_after:
            error_detail["retry_after_seconds"] = retry_after

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )
