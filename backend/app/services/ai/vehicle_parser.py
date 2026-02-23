"""
AI-powered parser for Sri Lankan vehicle registration books using Claude AI.
"""

import json
import logging
import traceback
from typing import Dict, Any
from ..anthropic_client import get_anthropic_client, AI_DEFAULT_MODEL, AI_VEHICLE_MODEL


def parse_vehicle_book_with_claude(ocr_text: str) -> Dict[str, Any]:
    """
    Parse OCR-extracted text from a Sri Lankan vehicle registration book using Claude AI.

    Args:
        ocr_text: Raw text extracted from vehicle book images via OCR

    Returns:
        Dictionary containing:
        - extracted_data: Dict of field_name -> value
        - confidence_scores: Dict of field_name -> confidence (0.0-1.0)
        - overall_confidence: Average confidence across all fields
        - metadata: Additional parsing metadata
    """

    # Get singleton client
    client = get_anthropic_client()

    # Construct the vehicle book parsing prompt
    prompt = f"""You are an expert at extracting structured data from Sri Lankan vehicle registration books (Certificate of Registration / CR Book).

DOCUMENT TEXT:
{ocr_text}

TASK: Extract ALL available vehicle information and return it as a JSON object with the following structure:

{{
  "extracted_data": {{
    // VEHICLE IDENTIFICATION
    "registration_number": "string or null - format: WP CAB-1234 or similar",
    "provincial_council": "string or null - Western, Central, Southern, etc.",
    "class_of_vehicle": "string or null - Motor Car, Motor Cycle, Three-wheeler, etc.",
    "body_colour": "string or null",
    "chassis_number": "string or null - alphanumeric",
    "engine_number": "string or null - alphanumeric",
    "vehicle_status": "string or null - Registered, De-registered, etc.",
    "country_of_origin": "string or null - Japan, India, etc.",
    "make": "string or null - Toyota, Honda, Nissan, Suzuki, etc.",
    "model": "string or null - Corolla, Civic, etc.",
    "date_of_first_registration": "DD/MM/YYYY or null",
    "year_of_manufacture": number or null,
    "cylinder_capacity": number or null - in cc,
    "fuel_type": "string or null - Petrol, Diesel, Hybrid, Electric, etc.",

    // ENGINE & TRANSMISSION
    "engine_type": "string or null - descriptive, e.g., 4-cylinder inline",
    "transmission": "string or null - Manual, Automatic, CVT",
    "wheel_drive": "string or null - 2WD, 4WD, AWD",

    // OWNER INFORMATION
    "owner_name": "string or null - registered owner name",
    "owner_address": "string or null",
    "owner_nic": "string or null - National ID number",

    // VEHICLE SPECIFICATIONS
    "seating_capacity": number or null,
    "unladen_weight": "string or null - in kg",
    "gross_weight": "string or null - in kg",
    "number_of_axles": number or null,
    "wheelbase": "string or null",
    "overall_length": "string or null",
    "overall_width": "string or null",
    "overall_height": "string or null",

    // TAX & INSURANCE
    "revenue_license_valid_until": "DD/MM/YYYY or null",
    "insurance_valid_until": "DD/MM/YYYY or null",
    "last_transferred_date": "DD/MM/YYYY or null"
  }},

  "confidence_scores": {{
    // For each field extracted, provide confidence 0.0-1.0
    "registration_number": 0.95,
    "make": 0.90,
    // ... etc for each extracted field
  }},

  "metadata": {{
    "document_type": "Vehicle Registration Book / CR Book / Transfer Certificate",
    "language_detected": "English / Sinhala / Mixed",
    "parsing_notes": "Any important observations about the document"
  }}
}}

IMPORTANT INSTRUCTIONS:
1. **Sri Lankan Vehicle Registration**: Format is typically Provincial Code + Category + Number (e.g., WP CAB-1234, CP ABC-5678)
2. **Provincial Codes**: WP (Western), CP (Central), SP (Southern), NP (Northern), EP (Eastern), NW (North Western), NC (North Central), UP (Uva), SG (Sabaragamuwa)
3. **Date Format**: Convert all dates to DD/MM/YYYY format
4. **Cylinder Capacity**: Extract in cc (cubic centimeters)
5. **Make vs Model**: Make is the brand (Toyota, Honda), Model is the specific model (Corolla, Civic)
6. **Confidence Scoring**:
   - 0.95-1.0: Clearly readable, exact match
   - 0.80-0.95: Readable but may have minor OCR issues
   - 0.60-0.80: Partially readable, some inference needed
   - Below 0.60: Low confidence, significant guesswork
7. **Vehicle Class**: Common classes in Sri Lanka - Motor Car, Motor Cycle, Three-wheeler, Lorry, Bus, Van, Dual Purpose Vehicle (SUV)
8. **Owner Information**: May be in Sinhala - extract as-is if readable

Return ONLY the JSON object, no additional text.

IMPORTANT: Return ONLY valid JSON. No markdown formatting, no code blocks, just the raw JSON object."""

    try:
        # Call Claude API using singleton client
        message = client.messages.create(
            model=AI_VEHICLE_MODEL,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract response text
        response_text = message.content[0].text.strip()

        # Clean up response - remove markdown if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Find first line with actual JSON
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("{"):
                    start_idx = i
                    break
            # Find closing
            end_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().startswith("}"):
                    end_idx = i + 1
                    break
            response_text = "\n".join(lines[start_idx:end_idx])

        # Parse JSON response
        parsed_result = json.loads(response_text)

        # Calculate overall confidence
        confidence_scores = parsed_result.get("confidence_scores", {})
        if confidence_scores:
            numeric_confidences = [v for v in confidence_scores.values() if isinstance(v, (int, float))]
            overall_confidence = sum(numeric_confidences) / len(numeric_confidences) if numeric_confidences else 0.5
        else:
            overall_confidence = 0.5

        # Prepare final result
        result = {
            "extracted_data": parsed_result.get("extracted_data", {}),
            "confidence_scores": confidence_scores,
            "overall_confidence": round(overall_confidence, 2),
            "metadata": parsed_result.get("metadata", {})
        }

        return result

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Vehicle book AI parsing failed: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise Exception(f"Vehicle book AI parsing failed: {str(e)}")
