"""
OCR text preprocessing and validation utilities.
"""

import re
from typing import Dict


def detect_document_type(extracted_data: Dict) -> str:
    """
    Auto-detect document type based on extracted fields.

    Args:
        extracted_data: Extracted data dictionary

    Returns:
        Document type: 'survey_plan', 'deed', 'title_certificate', or 'unknown'
    """
    # Check for survey plan indicators
    if extracted_data.get('plan_number') and extracted_data.get('licensed_surveyor_name'):
        return 'survey_plan'

    # Check for deed indicators
    if extracted_data.get('deed_number') or extracted_data.get('deed_type'):
        return 'deed'

    # Check for title certificate indicators
    if extracted_data.get('title_number') or extracted_data.get('folio_number'):
        return 'title_certificate'

    return 'unknown'


def preprocess_ocr_text(text: str) -> str:
    """
    Preprocess OCR text to improve parsing accuracy.
    Enhanced with better text normalization.

    Args:
        text: Raw OCR text

    Returns:
        Cleaned and normalized text
    """
    # Remove zero-width spaces and invisible characters (do this first)
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)

    # Remove excessive whitespace (but preserve structure)
    text = re.sub(r'\s+', ' ', text)

    # Preserve newlines but normalize them
    text = re.sub(r'\n\s*\n', '\n', text)

    # Normalize unicode characters
    text = text.encode('utf-8', errors='ignore').decode('utf-8')

    # Normalize dashes and hyphens
    text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)

    # NOTE: Removed aggressive character replacement (O->0, l->1, I->1)
    # as it corrupts legitimate text. OCR should be accurate enough or
    # manual correction is safer.

    return text.strip()


def validate_extracted_data(data: Dict) -> Dict:
    """
    Validate and clean extracted data.

    Args:
        data: Extracted data dictionary

    Returns:
        Validated and cleaned data
    """
    validated = data.copy()

    # Validate plan number (should be numeric with optional slashes/dashes)
    if 'plan_number' in validated:
        plan_num = validated['plan_number']
        if not re.match(r'^[0-9/-]+$', plan_num):
            del validated['plan_number']

    # Validate extent values
    if 'land_extent_roods' in validated and validated['land_extent_roods'] > 3:
        # Invalid roods value
        for key in ['land_extent_acres', 'land_extent_roods', 'land_extent_perches', 'land_extent_hectares', 'land_extent_raw_text']:
            validated.pop(key, None)

    if 'land_extent_perches' in validated and validated['land_extent_perches'] >= 40:
        # Invalid perches value
        for key in ['land_extent_acres', 'land_extent_roods', 'land_extent_perches', 'land_extent_hectares', 'land_extent_raw_text']:
            validated.pop(key, None)

    return validated
