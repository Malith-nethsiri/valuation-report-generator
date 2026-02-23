"""
Services package for business logic and external integrations
"""

from .ocr import (
    process_uploaded_document,
    extract_property_data_from_image,
    merge_ocr_with_existing_data
)

__all__ = [
    "process_uploaded_document",
    "extract_property_data_from_image",
    "merge_ocr_with_existing_data"
]
