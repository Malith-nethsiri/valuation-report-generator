"""
OCR services package.
Re-exports all public functions for zero-impact caller migration.
"""

from .vision_client import extract_text_from_image
from .preprocessor import detect_document_type, preprocess_ocr_text, validate_extracted_data
from .pipeline import (
    parse_property_data_from_text,
    extract_property_data_from_image,
    process_uploaded_document,
    process_multiple_documents,
    merge_ocr_with_existing_data,
)

__all__ = [
    "extract_text_from_image",
    "detect_document_type",
    "preprocess_ocr_text",
    "validate_extracted_data",
    "parse_property_data_from_text",
    "extract_property_data_from_image",
    "process_uploaded_document",
    "process_multiple_documents",
    "merge_ocr_with_existing_data",
]
