"""
OCR Service for extracting property data from survey plans, deeds, and other legal documents
Uses Google Cloud Vision API REST endpoint for text extraction and Claude AI for intelligent parsing
"""

import base64
import os
from typing import Dict, List, Optional, Tuple
from fastapi import UploadFile
import json
import re
from datetime import datetime
import requests

# Import AI parser for Claude AI integration
from .ai_parser import parse_with_claude, merge_multi_document_results, parse_vehicle_book_with_claude


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


def extract_text_from_image(image_data: bytes) -> str:
    """
    Extract all text from an image using Google Cloud Vision API REST endpoint.

    Args:
        image_data: Raw image bytes

    Returns:
        Extracted text as a single string
    """
    try:
        # GOOGLE_VISION_API_KEY is required - no fallback to GOOGLE_MAPS_API_KEY
        # Vision API should use its own dedicated key with appropriate quotas
        api_key = os.getenv("GOOGLE_VISION_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_VISION_API_KEY environment variable is required")

        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Google Vision API endpoint
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

        # Request payload with enhanced image context for better accuracy
        payload = {
            "requests": [
                {
                    "image": {
                        "content": base64_image
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",
                            "maxResults": 50
                        }
                    ],
                    "imageContext": {
                        "languageHints": ["en", "si"],
                        "textDetectionParams": {
                            "enableTextDetectionConfidenceScore": True
                        }
                    }
                }
            ]
        }

        # Make API request
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Extract text from response
        if 'responses' in result and len(result['responses']) > 0:
            first_response = result['responses'][0]

            if 'error' in first_response:
                error_msg = first_response['error'].get('message', 'Unknown error')
                raise Exception(f"Google Vision API error: {error_msg}")

            extracted_text = ""
            if 'fullTextAnnotation' in first_response:
                extracted_text = first_response['fullTextAnnotation']['text']
            elif 'textAnnotations' in first_response and len(first_response['textAnnotations']) > 0:
                extracted_text = first_response['textAnnotations'][0]['description']

            return extracted_text

        return ""

    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")


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


def parse_property_data_from_text(text: str, document_hint: Optional[str] = None) -> Tuple[Dict, float]:
    """
    Parse structured property data from extracted text.

    Args:
        text: Extracted text from document
        document_hint: Optional hint about document type

    Returns:
        Tuple of (extracted_data_dict, overall_confidence_score)
    """
    # Preprocess text for better accuracy
    text = preprocess_ocr_text(text)

    extracted_data = {}
    confidence_scores = {
        "plan_info": 0.0,
        "extent": 0.0,
        "boundaries": 0.0,
        "physical_boundaries": 0.0,
        "location": 0.0
    }

    # Helper function to search for patterns
    def find_pattern(pattern, flags=re.IGNORECASE):
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else None

    # Extract Plan Number (enhanced patterns)
    plan_patterns = [
        r'Plan\s+No\.?\s*:?\s*([0-9]+(?:[/-][0-9]+)*)',
        r'Survey\s+Plan\s+No\.?\s*:?\s*([0-9]+(?:[/-][0-9]+)*)',
        r'P\.?S\.?\s+No\.?\s*:?\s*([0-9]+(?:[/-][0-9]+)*)',
        r'Plan\s+Number\s*:?\s*([0-9]+(?:[/-][0-9]+)*)',
        r'Plan\s*[:#]\s*([0-9]+(?:[/-][0-9]+)*)',
        r'(?:^|\n)Plan\s+([0-9]+(?:[/-][0-9]+)*)',
    ]
    for pattern in plan_patterns:
        plan_number = find_pattern(pattern)
        if plan_number and len(plan_number) >= 3:
            extracted_data['plan_number'] = plan_number.strip()
            confidence_scores['plan_info'] = 0.90
            break

    # Extract Plan Date (enhanced with more formats)
    date_patterns = [
        r'Date\s+of\s+Survey\s*:?\s*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})',
        r'Plan\s+dated\s*:?\s*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})',
        r'Survey\s+Date\s*:?\s*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})',
        r'Dated\s*:?\s*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})',
        r'Date\s*:?\s*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})',
        r'([0-9]{1,2}[-/.][0-9]{1,2}[-/.][19|20][0-9]{2})',
    ]
    for pattern in date_patterns:
        plan_date = find_pattern(pattern)
        if plan_date:
            # Normalize date format
            normalized_date = plan_date.replace('.', '-').replace('/', '-')
            extracted_data['plan_date'] = normalized_date
            confidence_scores['plan_info'] = max(confidence_scores['plan_info'], 0.85)
            break

    # Extract Licensed Surveyor Name (enhanced)
    surveyor_patterns = [
        r'Licensed\s+Surveyor\s*:?\s*([A-Z][a-zA-Z\s.]+?)(?:\n|$|Reg|License)',
        r'Surveyor\s*:?\s*([A-Z][a-zA-Z\s.]+?)(?:\n|$)',
        r'L\.?S\.?\s*:?\s*([A-Z][a-zA-Z\s.]+?)(?:\n|$)',
        r'Prepared\s+by\s*:?\s*([A-Z][a-zA-Z\s.]+?)(?:\n|$)',
        r'(?:By|by)\s+([A-Z][a-zA-Z\s.]+?)\s*(?:Licensed|L\.S\.)',
    ]
    for pattern in surveyor_patterns:
        surveyor = find_pattern(pattern)
        if surveyor:
            # Clean up surveyor name
            surveyor = surveyor.split('\n')[0].strip()
            # Remove common suffixes and clean
            surveyor = re.sub(r'\s+(Reg\.|License|No\.|#).*$', '', surveyor, flags=re.IGNORECASE)
            if 3 < len(surveyor) < 50 and surveyor.count(' ') <= 5:
                extracted_data['licensed_surveyor_name'] = surveyor.strip()
                confidence_scores['plan_info'] = max(confidence_scores['plan_info'], 0.85)
                break

    # Extract Plan Scale
    scale_patterns = [
        r'Scale\s*:?\s*(1\s*:\s*[0-9,]+)',
        r'Scale\s+of\s+Plan\s*:?\s*(1\s*:\s*[0-9,]+)',
    ]
    for pattern in scale_patterns:
        scale = find_pattern(pattern)
        if scale:
            extracted_data['survey_plan_scale'] = scale.replace(' ', '')
            break

    # Extract Lot Description
    lot_patterns = [
        r'Lot\s+([A-Z0-9\s,&]+?)(?:\n|in this plan)',
        r'Lots?\s+No\.?\s*([A-Z0-9\s,&]+)',
    ]
    for pattern in lot_patterns:
        lot = find_pattern(pattern)
        if lot:
            lot = lot.split('\n')[0].strip()
            if len(lot) < 30:
                extracted_data['lot_number'] = lot
                break

    # Extract Land Extent (A-R-P format) - Enhanced with more patterns
    extent_patterns = [
        # Standard format with labels
        r'(?:Extent|Area|Total\s+Extent)\s*:?\s*([0-9]+)\s*A[creACRE]*\s*[-\s,]*([0-9]+)\s*R[oods]*\s*[-\s,]*([0-9.]+)\s*P[erches]*',
        # Compact format: 00A-0R-00.00P
        r'([0-9]{1,3})A\s*[-\s,]\s*([0-9]{1})\s*R\s*[-\s,]\s*([0-9.]+)\s*P',
        # With spaces: 0 A 0 R 00.00 P
        r'([0-9]+)\s+A\s+([0-9]+)\s+R\s+([0-9.]+)\s+P',
        # Alternative with colons
        r'(?:Extent|Area)\s*[:\-]\s*([0-9]+)\s*[AaRr]\s*[-\s,]*([0-9]+)\s*[Rr]\s*[-\s,]*([0-9.]+)\s*[Pp]',
        # Numeric only with context
        r'([0-9]{1,2})\s*[-\s]\s*([0-9]{1})\s*[-\s]\s*([0-9]{1,2}\.?[0-9]*)\s*(?:A\.?R\.?P\.?|Acres)',
        # Sri Lankan format
        r'([0-9]+)\s*අක්කර\s*([0-9]+)\s*රූඩ්\s*([0-9.]+)\s*පර්චස්',
    ]
    for pattern in extent_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                acres = int(match.group(1))
                roods = int(match.group(2))
                perches = float(match.group(3))

                # Validate ranges (stricter validation)
                if 0 <= acres <= 999 and 0 <= roods <= 3 and 0 <= perches < 40:
                    extracted_data['land_extent_acres'] = acres
                    extracted_data['land_extent_roods'] = roods
                    extracted_data['land_extent_perches'] = perches

                    # Calculate hectares (1 perch = 25.29 sqm)
                    total_perches = acres * 160 + roods * 40 + perches
                    total_sqm = total_perches * 25.29
                    hectares = total_sqm / 10000
                    extracted_data['land_extent_hectares'] = round(hectares, 4)
                    extracted_data['land_extent_raw_text'] = f"{acres:02d}A-{roods}R-{perches}P"

                    # Higher confidence for well-formatted data
                    if roods <= 3 and perches < 40 and acres > 0:
                        confidence_scores['extent'] = 0.90
                    else:
                        confidence_scores['extent'] = 0.75
                    break
            except (ValueError, IndexError):
                continue

    # Extract Traditional Land Name
    name_patterns = [
        r'(?:Name of Land|Land Name|Traditional Name)\s*:?\s*["\']?([A-Za-z\s]+)["\']?',
        r'called\s+["\']([A-Za-z\s]+)["\']',
        r'known as\s+["\']([A-Za-z\s]+)["\']',
    ]
    for pattern in name_patterns:
        name = find_pattern(pattern)
        if name:
            name = name.split('\n')[0].strip()
            if 3 < len(name) < 50:
                extracted_data['land_traditional_name'] = name
                break

    # Extract Boundaries (enhanced patterns)
    boundaries = {'north': {}, 'south': {}, 'east': {}, 'west': {}}
    directions = {
        'north': [
            r'(?:North|Northern|N)\s*[:\-]\s*(.{10,300}?)(?:\n\s*(?:South|East|West)|$)',
            r'(?:On the )?North\s+by\s+(.{10,300}?)(?:\n\s*(?:South|East|West)|$)',
        ],
        'south': [
            r'(?:South|Southern|S)\s*[:\-]\s*(.{10,300}?)(?:\n\s*(?:East|West|North)|$)',
            r'(?:On the )?South\s+by\s+(.{10,300}?)(?:\n\s*(?:East|West|North)|$)',
        ],
        'east': [
            r'(?:East|Eastern|E)\s*[:\-]\s*(.{10,300}?)(?:\n\s*(?:South|West|North)|$)',
            r'(?:On the )?East\s+by\s+(.{10,300}?)(?:\n\s*(?:South|West|North)|$)',
        ],
        'west': [
            r'(?:West|Western|W)\s*[:\-]\s*(.{10,300}?)(?:\n\s*(?:South|East|North)|$)',
            r'(?:On the )?West\s+by\s+(.{10,300}?)(?:\n\s*(?:South|East|North)|$)',
        ],
    }

    found_any_boundary = False
    boundary_count = 0
    for direction, patterns in directions.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                # Clean up the description
                description = re.sub(r'\s+', ' ', description)
                if len(description) > 10:
                    boundaries[direction]['description'] = description
                    found_any_boundary = True
                    boundary_count += 1
                break

    if found_any_boundary:
        extracted_data['boundaries'] = boundaries
        # Higher confidence if we found all 4 boundaries
        if boundary_count >= 4:
            confidence_scores['boundaries'] = 0.85
        elif boundary_count >= 2:
            confidence_scores['boundaries'] = 0.75
        else:
            confidence_scores['boundaries'] = 0.60

    # Extract Physical Boundary Types
    physical_types = []
    if re.search(r'brick\s+wall', text, re.IGNORECASE):
        physical_types.append('brick_walls')
    if re.search(r'barbed\s+wire', text, re.IGNORECASE):
        physical_types.append('barbed_wire')
    if re.search(r'live\s+fence', text, re.IGNORECASE):
        physical_types.append('live_fence')
    if re.search(r'concrete\s+post', text, re.IGNORECASE):
        physical_types.append('concrete_posts')
    if re.search(r'iron\s+gate', text, re.IGNORECASE):
        physical_types.append('iron_gate')
    if re.search(r'rubble\s+foundation', text, re.IGNORECASE):
        physical_types.append('rubble_foundation')

    if physical_types:
        extracted_data['physical_boundaries_types'] = physical_types
        confidence_scores['physical_boundaries'] = 0.75

    # Extract Deed Information
    deed_number_patterns = [
        r'Deed\s+No\.?\s*:?\s*([0-9]+)',
        r'D\.?D\.?\s*No\.?\s*:?\s*([0-9]+)',
    ]
    for pattern in deed_number_patterns:
        deed_no = find_pattern(pattern)
        if deed_no:
            extracted_data['deed_number'] = deed_no
            break

    # Extract Property Number
    property_patterns = [
        r'Property\s+No\.?\s*:?\s*([0-9]+[A-Z0-9/]*)',
        r'No\.?\s*:?\s*([0-9]+[A-Z0-9/]*)',
    ]
    for pattern in property_patterns:
        prop_no = find_pattern(pattern)
        if prop_no:
            extracted_data['property_number'] = prop_no
            confidence_scores['location'] = 0.75
            break

    # Extract Village/GN Division
    village_patterns = [
        r'Village\s*:?\s*([A-Za-z\s]+)',
        r'Grama\s+Niladari\s+Division\s*:?\s*([A-Za-z\s]+)',
    ]
    for pattern in village_patterns:
        village = find_pattern(pattern)
        if village:
            village = village.split('\n')[0].strip()
            if len(village) < 50:
                extracted_data['property_village'] = village
                confidence_scores['location'] = max(confidence_scores['location'], 0.75)
                break

    # Validate extracted data
    extracted_data = validate_extracted_data(extracted_data)

    # Calculate overall confidence
    extracted_data['confidence_scores'] = confidence_scores
    overall_confidence = sum(confidence_scores.values()) / len(confidence_scores)

    # Adjust confidence based on number of fields extracted
    fields_extracted = len([k for k in extracted_data.keys() if not k.startswith('_') and k != 'confidence_scores'])
    if fields_extracted >= 8:
        overall_confidence = min(1.0, overall_confidence * 1.1)
    elif fields_extracted <= 3:
        overall_confidence = overall_confidence * 0.8

    return extracted_data, overall_confidence


async def extract_property_data_from_image(
    image_data: bytes,
    media_type: str = "image/jpeg",
    document_hint: Optional[str] = None
) -> Tuple[Dict, float]:
    """
    Extract property data from an image using Google Cloud Vision API.

    Args:
        image_data: Raw image bytes
        media_type: MIME type of the image (image/jpeg, image/png, image/webp)
        document_hint: Optional hint about document type ('survey_plan', 'deed', 'title_certificate')

    Returns:
        Tuple of (extracted_data_dict, overall_confidence_score)

    Example:
        data, confidence = await extract_property_data_from_image(image_bytes, "image/jpeg")
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        # Extract text using Google Vision
        logger.info("[OCR] Extracting text from image using Google Vision API...")
        extracted_text = extract_text_from_image(image_data)
        logger.info(f"[OCR] Extracted {len(extracted_text)} characters of text")

        if not extracted_text:
            logger.warning("[OCR] No text extracted from image")
            return {}, 0.0

        # Parse structured data using Claude AI
        # Use different parser for vehicle books vs property documents
        logger.info(f"[OCR] Parsing text with Claude AI (document_hint: {document_hint})...")
        if document_hint == 'vehicle_book':
            ai_result = parse_vehicle_book_with_claude(extracted_text)
        else:
            ai_result = parse_with_claude(extracted_text, document_hint)
        logger.info(f"[OCR] AI parsing result type: {type(ai_result)}")

        # Defensive check: ensure ai_result is not None
        if ai_result is None:
            logger.error("[OCR] AI parser returned None - API configuration issue")
            raise Exception("AI parser returned None - possible API configuration issue")

        # Defensive check: ensure ai_result is a dictionary
        if not isinstance(ai_result, dict):
            logger.error(f"[OCR] AI parser returned unexpected type: {type(ai_result)}")
            raise Exception(f"AI parser returned unexpected type: {type(ai_result)}")

        extracted_data = ai_result.get('extracted_data', {})
        confidence_scores = ai_result.get('confidence_scores', {})
        overall_confidence = ai_result.get('overall_confidence', 0.5)
        detected_plans = ai_result.get('detected_plans', [])
        metadata = ai_result.get('metadata', {})

        logger.info(f"[OCR] Successfully extracted {len(extracted_data)} fields with confidence {overall_confidence}")

        # Store additional metadata
        extracted_data['_confidence_scores'] = confidence_scores
        extracted_data['_detected_plans'] = detected_plans
        extracted_data['_ai_metadata'] = metadata
        extracted_data['_raw_ocr_text'] = extracted_text

        return extracted_data, overall_confidence

    except Exception as e:
        logger.error(f"[OCR] Extraction failed: {str(e)}")
        logger.error(f"[OCR] Full traceback:\n{traceback.format_exc()}")
        raise Exception(f"OCR extraction failed: {str(e)}")


async def process_uploaded_document(
    file: UploadFile,
    document_type_hint: Optional[str] = None
) -> Dict:
    """
    Process an uploaded document file and extract property data.

    Args:
        file: FastAPI UploadFile object
        document_type_hint: Optional hint about document type

    Returns:
        Dictionary with extracted data, confidence scores, and metadata

    Example:
        result = await process_uploaded_document(uploaded_file, "survey_plan")
    """
    try:
        # Read file content
        content = await file.read()

        # Determine media type
        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/jpg", "image/png", "image/webp"]:
            # If PDF, we need to convert it to images first
            # For now, raise error (PDF conversion can be added later)
            if content_type == "application/pdf":
                raise ValueError("PDF support coming soon. Please convert PDF pages to images first.")
            else:
                raise ValueError(f"Unsupported file type: {content_type}. Supported: JPEG, PNG, WEBP")

        # Extract data using Google Vision
        extracted_data, confidence = await extract_property_data_from_image(
            content,
            media_type=content_type,
            document_hint=document_type_hint
        )

        # Extract AI-specific metadata
        confidence_scores = extracted_data.pop('_confidence_scores', {})
        detected_plans = extracted_data.pop('_detected_plans', [])
        ai_metadata = extracted_data.pop('_ai_metadata', {})

        # Add metadata
        result = {
            "success": True,
            "extracted_data": extracted_data,
            "overall_confidence": confidence,
            "confidence_scores": confidence_scores,
            "detected_plans": detected_plans,
            "metadata": {
                "filename": file.filename,
                "content_type": content_type,
                "file_size_bytes": len(content),
                "processed_at": datetime.utcnow().isoformat(),
                "document_type_hint": document_type_hint,
                "ai_metadata": ai_metadata
            }
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "metadata": {
                "filename": file.filename if file else "unknown",
                "processed_at": datetime.utcnow().isoformat()
            }
        }


async def process_multiple_documents(
    files: List[UploadFile],
    document_type_hint: Optional[str] = None
) -> Dict:
    """
    Process multiple uploaded document files (e.g., deed pages + plan pages) and combine results.

    Args:
        files: List of FastAPI UploadFile objects (typically 4-7 images for a complete property)
        document_type_hint: Optional hint about document type

    Returns:
        Dictionary with combined extracted data, confidence scores, and metadata

    Strategy:
        - Process each image separately with Google Vision OCR
        - Intelligently combine results (e.g., plan info from plan page, boundaries from deed)
        - Prefer data with higher confidence scores
        - Track which page each field came from for audit trail

    Example:
        result = await process_multiple_documents([deed1, deed2, deed3, plan1], "deed")
    """
    try:
        if not files or len(files) == 0:
            raise ValueError("No files provided")

        # Process each file and collect AI parsing results
        individual_results = []
        for idx, file in enumerate(files):
            result = await process_uploaded_document(file, document_type_hint)
            if result.get('success'):
                # Collect results in format expected by AI merger
                individual_results.append({
                    'extracted_data': result.get('extracted_data', {}),
                    'confidence_scores': result.get('confidence_scores', {}),
                    'overall_confidence': result.get('overall_confidence', 0.5),
                    'detected_plans': result.get('detected_plans', []),
                    'metadata': {
                        'filename': file.filename,
                        'page_number': idx + 1,
                        **result.get('metadata', {})
                    }
                })

        if not individual_results:
            raise ValueError("Failed to extract data from any of the uploaded files")

        # Use AI-powered intelligent merging
        merged_result = merge_multi_document_results(individual_results)

        # Prepare final result with enhanced metadata
        result = {
            "success": True,
            "extracted_data": merged_result.get('extracted_data', {}),
            "overall_confidence": merged_result.get('overall_confidence', 0.5),
            "confidence_scores": merged_result.get('confidence_scores', {}),
            "detected_plans": merged_result.get('detected_plans', []),
            "metadata": {
                "total_pages_processed": len(individual_results),
                "total_files_submitted": len(files),
                "processed_at": datetime.utcnow().isoformat(),
                "document_type_hint": document_type_hint,
                "merged_from_documents": merged_result.get('metadata', {}).get('merged_from_documents', len(individual_results)),
                "total_fields_extracted": merged_result.get('metadata', {}).get('total_fields_extracted', 0),
                "individual_files": [
                    {
                        'page': r['metadata']['page_number'],
                        'filename': r['metadata']['filename'],
                        'confidence': r['overall_confidence']
                    }
                    for r in individual_results
                ]
            }
        }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "metadata": {
                "total_files_submitted": len(files) if files else 0,
                "processed_at": datetime.utcnow().isoformat()
            }
        }


def merge_ocr_with_existing_data(
    existing_data: Dict,
    ocr_data: Dict,
    confidence_threshold: float = 0.7
) -> Tuple[Dict, Dict]:
    """
    Merge OCR extracted data with existing manually entered data.

    Args:
        existing_data: Existing report data from database
        ocr_data: Newly extracted OCR data
        confidence_threshold: Minimum confidence to auto-fill (0.0 to 1.0)

    Returns:
        Tuple of (merged_data, conflicts_dict)
        - merged_data: Updated data with OCR values
        - conflicts_dict: Fields where existing data differs from OCR

    Strategy:
        - If field is empty in existing_data: Fill from OCR
        - If field exists in existing_data and differs from OCR:
          - If OCR confidence >= threshold: Mark as conflict for user review
          - If OCR confidence < threshold: Keep existing value
    """
    merged_data = existing_data.copy()
    conflicts = {}

    # Fields to potentially update from OCR
    ocr_fields = [
        'plan_number', 'plan_date', 'licensed_surveyor_name', 'survey_plan_scale',
        'lot_number', 'land_traditional_name', 'property_number',
        'property_village', 'grama_niladari_division'
    ]

    for field in ocr_fields:
        ocr_value = ocr_data.get(field)
        existing_value = existing_data.get(field)

        if ocr_value:
            if not existing_value:
                # Field is empty, fill from OCR
                merged_data[field] = ocr_value
            elif existing_value != ocr_value:
                # Conflict: existing data differs from OCR
                field_confidence = ocr_data.get('confidence_scores', {}).get(field, 0.5)
                if field_confidence >= confidence_threshold:
                    conflicts[field] = {
                        'existing': existing_value,
                        'ocr': ocr_value,
                        'confidence': field_confidence
                    }

    # Handle extent data specially
    if ocr_data.get('land_extent_acres') is not None:
        if not existing_data.get('land_extent_acres'):
            merged_data['land_extent_acres'] = ocr_data.get('land_extent_acres')
            merged_data['land_extent_roods'] = ocr_data.get('land_extent_roods')
            merged_data['land_extent_perches'] = ocr_data.get('land_extent_perches')
            merged_data['land_extent_hectares'] = ocr_data.get('land_extent_hectares')

    # Handle boundaries
    if ocr_data.get('boundaries'):
        if not existing_data.get('boundaries'):
            merged_data['boundaries'] = ocr_data.get('boundaries')
        else:
            # Merge boundaries, preferring OCR for empty directions
            existing_boundaries = existing_data.get('boundaries', {})
            ocr_boundaries = ocr_data.get('boundaries', {})
            for direction in ['north', 'south', 'east', 'west']:
                if not existing_boundaries.get(direction) and ocr_boundaries.get(direction):
                    existing_boundaries[direction] = ocr_boundaries[direction]
            merged_data['boundaries'] = existing_boundaries

    # Handle physical boundaries
    if ocr_data.get('physical_boundaries_types'):
        if not existing_data.get('physical_boundaries_types'):
            merged_data['physical_boundaries_types'] = ocr_data.get('physical_boundaries_types')
            merged_data['physical_boundaries_description'] = ocr_data.get('physical_boundaries_description')

    return merged_data, conflicts
