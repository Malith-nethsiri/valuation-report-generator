"""
AI-powered parser for Sri Lankan property documents using Claude AI.
Extracts structured data from OCR text with confidence scoring.
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic


def parse_with_claude(ocr_text: str, document_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse OCR-extracted text using Claude AI to extract structured property data.

    Args:
        ocr_text: Raw text extracted from document images via OCR
        document_type: Optional hint about document type ('survey_plan', 'deed', 'title_certificate')

    Returns:
        Dictionary containing:
        - extracted_data: Dict of field_name -> value
        - confidence_scores: Dict of field_name -> confidence (0.0-1.0)
        - overall_confidence: Average confidence across all fields
        - detected_plans: List of plans found in the document
        - metadata: Additional parsing metadata
    """

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    # Construct the parsing prompt
    prompt = f"""You are an expert at extracting structured data from Sri Lankan property documents (deeds, survey plans, certificates).

DOCUMENT TEXT:
{ocr_text}

TASK: Extract ALL available property information and return it as a JSON object with the following structure:

{{
  "extracted_data": {{
    // PLAN INFORMATION
    "plan_number": "string or null",
    "plan_date": "DD-MM-YYYY or null",
    "licensed_surveyor_name": "string or null",
    "survey_plan_scale": "string or null",
    "plan_reference_notes": "string or null",

    // DEED INFORMATION (array - can have multiple deeds)
    "deeds": [
      {{
        "deed_type": "Mortgage Bond/Transfer Deed/Certificate of Sale/etc",
        "deed_number": "string",
        "deed_date": "DD-MM-YYYY",
        "notary_name": "string",
        "notary_location": "string",
        "notary_serial_number": "string or null"
      }}
    ],

    // LAND EXTENT
    "land_extent_acres": number or null,
    "land_extent_roods": number or null,
    "land_extent_perches": number or null,
    "land_extent_hectares": number or null,
    "land_traditional_name": "string or null",

    // BOUNDARIES (extract all 4 directions)
    "boundaries": {{
      "north": {{
        "description": "string",
        "length": "string or null",
        "adjoins": "string or null"
      }},
      "south": {{
        "description": "string",
        "length": "string or null",
        "adjoins": "string or null"
      }},
      "east": {{
        "description": "string",
        "length": "string or null",
        "adjoins": "string or null"
      }},
      "west": {{
        "description": "string",
        "length": "string or null",
        "adjoins": "string or null"
      }}
    }},

    // LOCATION INFORMATION (ALL administrative divisions)
    "village": "string or null",
    "gn_division_name": "string or null",
    "gn_division_number": "string or null",
    "ds_division": "string or null",
    "district": "string or null",
    "province": "string or null",
    "korale": "string or null",
    "pradeshiya_sabha": "string or null",

    // LAND REGISTRY
    "land_registry_volume": "string or null",
    "land_registry_folio": "string or null",
    "land_registry_location": "string or null",

    // OWNERSHIP (current owners mentioned in deed)
    "current_owners": ["name1", "name2"] or null
  }},

  "confidence_scores": {{
    // For each field extracted, provide confidence 0.0-1.0
    // Only include fields that were actually found
    "plan_number": 0.95,
    "plan_date": 0.90,
    // ... etc for each extracted field
  }},

  "detected_plans": [
    {{
      "plan_number": "7789",
      "plan_date": "28-06-2016",
      "surveyor": "G.B. Dissanayaka",
      "confidence": 0.95
    }}
    // Include ALL plans mentioned in the document
  ],

  "metadata": {{
    "document_appears_to_be": "Certificate of Sale / Deed / Survey Plan",
    "multiple_plans_detected": true or false,
    "language_detected": "English / Sinhala / Mixed",
    "parsing_notes": "Any important observations about the document"
  }}
}}

IMPORTANT INSTRUCTIONS:
1. **Sri Lankan Measurement Units**: Land extent in Acres-Roods-Perches (A-R-P) where 1 Acre = 4 Roods = 160 Perches
2. **Date Format**: Convert all dates to DD-MM-YYYY format (e.g., 28.06.2016 → 28-06-2016)
3. **Administrative Hierarchy**: Province → District → DS Division → GN Division → Village
4. **Multiple Plans**: If the document references multiple plans (e.g., "Plan No. 7789" and "Plan No. 7769"), list ALL in detected_plans array
5. **Boundaries**: Look for phrases like "bounded on the North by", "East by", etc. Extract the description (e.g., "Lot 1", "Main road", "Nangalle Ela")
6. **Korale/Pattu**: Historical administrative divisions (e.g., "Beligal Korale", "Otara Pattu")
7. **Land Registry**: Format is "Volume/Folio Location" (e.g., "K 54/138 at Land Registry, Kegalle")
8. **Confidence Scoring**:
   - 0.95-1.0: Explicitly stated, unambiguous
   - 0.80-0.94: Clearly stated but minor OCR artifacts
   - 0.60-0.79: Inferred from context or partial match
   - 0.40-0.59: Low confidence, needs verification
   - Below 0.40: Don't include the field
9. **Null Values**: If a field is not found or confidence is below 0.40, set it to null
10. **Return ONLY valid JSON** - no markdown, no code blocks, just the JSON object

Extract as much data as possible from the provided text. Be thorough and accurate."""

    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast and cost-effective
            max_tokens=4096,
            temperature=0,  # Deterministic output for data extraction
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract the response text
        response_text = response.content[0].text.strip()

        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Find the JSON content between code blocks
                lines = response_text.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not line.startswith("```")):
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            parsed_result = json.loads(response_text)

        except json.JSONDecodeError as e:
            raise ValueError(f"Claude AI returned invalid JSON: {e}")

        # Calculate overall confidence (only from numeric values)
        confidence_scores = parsed_result.get("confidence_scores", {})
        if confidence_scores:
            numeric_confidences = []
            for conf_value in confidence_scores.values():
                if isinstance(conf_value, (int, float)):
                    numeric_confidences.append(conf_value)
                elif isinstance(conf_value, dict):
                    # Handle nested confidence (e.g., boundaries with N/S/E/W)
                    sub_values = [v for v in conf_value.values() if isinstance(v, (int, float))]
                    if sub_values:
                        numeric_confidences.append(sum(sub_values) / len(sub_values))
            overall_confidence = sum(numeric_confidences) / len(numeric_confidences) if numeric_confidences else 0.5
        else:
            overall_confidence = 0.5

        # Prepare final result
        result = {
            "extracted_data": parsed_result.get("extracted_data", {}),
            "confidence_scores": confidence_scores,
            "overall_confidence": round(overall_confidence, 2),
            "detected_plans": parsed_result.get("detected_plans", []),
            "metadata": parsed_result.get("metadata", {})
        }

        # Safety check: ensure result is valid before returning
        if not isinstance(result, dict):
            raise Exception("Internal error: Result is not a dictionary")

        return result

    except Exception as e:
        # Log the full error for debugging with traceback
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"AI parsing failed: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

        # Always raise exception - never return None
        raise Exception(f"AI parsing failed: {str(e)}")


def merge_multi_document_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge results from multiple document pages into a single comprehensive result.

    Intelligent merging strategy:
    - Plan info: Use the result with highest confidence
    - Deeds: Combine all unique deeds found across documents
    - Extent: Use the result with highest confidence
    - Boundaries: Prefer more complete/detailed boundary descriptions
    - Location: Use most complete location information
    - Detected plans: Combine all unique plans found

    Args:
        results: List of parsing results from individual document pages

    Returns:
        Merged result dictionary
    """

    if not results:
        return {
            "extracted_data": {},
            "confidence_scores": {},
            "overall_confidence": 0.0,
            "detected_plans": [],
            "metadata": {}
        }

    if len(results) == 1:
        return results[0]

    merged_data = {}
    merged_confidence = {}
    all_detected_plans = []

    # Merge each field by selecting the value with highest confidence
    for result in results:
        data = result.get("extracted_data", {})
        confidence = result.get("confidence_scores", {})

        for field, value in data.items():
            if value is None:
                continue

            raw_confidence = confidence.get(field, 0.5)
            # Ensure field_confidence is numeric (Claude sometimes returns dicts for nested fields)
            if isinstance(raw_confidence, dict):
                # Average the nested confidence values
                nested_values = [v for v in raw_confidence.values() if isinstance(v, (int, float))]
                field_confidence = sum(nested_values) / len(nested_values) if nested_values else 0.5
            elif isinstance(raw_confidence, (int, float)):
                field_confidence = raw_confidence
            else:
                field_confidence = 0.5

            # Special handling for deeds (array - merge all unique)
            if field == "deeds" and isinstance(value, list):
                if "deeds" not in merged_data:
                    merged_data["deeds"] = []

                # Track confidence scores in a temporary list
                if "_deeds_confidences" not in merged_data:
                    merged_data["_deeds_confidences"] = []

                for deed in value:
                    # Check if this deed is already in merged results
                    is_duplicate = False
                    for existing_deed in merged_data["deeds"]:
                        if (existing_deed.get("deed_number") == deed.get("deed_number") and
                            existing_deed.get("deed_date") == deed.get("deed_date")):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        merged_data["deeds"].append(deed)
                        merged_data["_deeds_confidences"].append(field_confidence)

                continue

            # Special handling for boundaries (dict - merge by direction)
            if field == "boundaries" and isinstance(value, dict):
                if "boundaries" not in merged_data:
                    merged_data["boundaries"] = {}
                    merged_confidence["boundaries"] = 0.0

                for direction, boundary_info in value.items():
                    if direction not in merged_data["boundaries"]:
                        merged_data["boundaries"][direction] = boundary_info
                    else:
                        # Use more detailed description
                        existing_desc = merged_data["boundaries"][direction].get("description", "")
                        new_desc = boundary_info.get("description", "")
                        if len(new_desc) > len(existing_desc):
                            merged_data["boundaries"][direction] = boundary_info

                merged_confidence["boundaries"] = max(merged_confidence["boundaries"], field_confidence)
                continue

            # For all other fields: Use value with highest confidence
            existing_confidence = merged_confidence.get(field)
            # Safely get numeric value for comparison
            if isinstance(existing_confidence, dict):
                nested = [v for v in existing_confidence.values() if isinstance(v, (int, float))]
                existing_confidence = sum(nested) / len(nested) if nested else 0.0
            elif not isinstance(existing_confidence, (int, float)):
                existing_confidence = 0.0

            if field not in merged_confidence or field_confidence > existing_confidence:
                merged_data[field] = value
                merged_confidence[field] = field_confidence

        # Collect all detected plans
        for plan in result.get("detected_plans", []):
            # Check for duplicates
            is_duplicate = False
            for existing_plan in all_detected_plans:
                if existing_plan.get("plan_number") == plan.get("plan_number"):
                    # Keep the one with higher confidence
                    if plan.get("confidence", 0) > existing_plan.get("confidence", 0):
                        all_detected_plans.remove(existing_plan)
                        all_detected_plans.append(plan)
                    is_duplicate = True
                    break

            if not is_duplicate:
                all_detected_plans.append(plan)

    # Calculate deeds confidence from temporary list
    if "_deeds_confidences" in merged_data and merged_data["_deeds_confidences"]:
        merged_confidence["deeds"] = sum(merged_data["_deeds_confidences"]) / len(merged_data["_deeds_confidences"])
        del merged_data["_deeds_confidences"]  # Remove temporary tracking list

    # Calculate overall confidence (only from numeric values)
    if merged_confidence:
        numeric_confidences = []
        for conf_value in merged_confidence.values():
            if isinstance(conf_value, (int, float)):
                numeric_confidences.append(conf_value)
            elif isinstance(conf_value, dict):
                # Handle nested confidence (e.g., boundaries with N/S/E/W)
                sub_values = [v for v in conf_value.values() if isinstance(v, (int, float))]
                if sub_values:
                    numeric_confidences.append(sum(sub_values) / len(sub_values))
        overall_confidence = sum(numeric_confidences) / len(numeric_confidences) if numeric_confidences else 0.5
    else:
        overall_confidence = 0.0

    merged_result = {
        "extracted_data": merged_data,
        "confidence_scores": merged_confidence,
        "overall_confidence": round(overall_confidence, 2),
        "detected_plans": all_detected_plans,
        "metadata": {
            "merged_from_documents": len(results),
            "total_fields_extracted": len(merged_data)
        }
    }

    return merged_result


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

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

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

Return ONLY the JSON object, no additional text.</prompt>

IMPORTANT: Return ONLY valid JSON. No markdown formatting, no code blocks, just the raw JSON object."""

    try:
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
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
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Vehicle book AI parsing failed: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise Exception(f"Vehicle book AI parsing failed: {str(e)}")
