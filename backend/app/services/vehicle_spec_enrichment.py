"""
AI-powered vehicle specification enrichment service.
Given make + model + year (+ optional variant), retrieves manufacturer specifications
from Claude AI and returns structured spec_data.
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .anthropic_client import get_anthropic_client, is_anthropic_configured, AI_DEFAULT_MODEL

logger = logging.getLogger(__name__)


def enrich_vehicle_specs(
    make: str,
    model: str,
    year: int,
    variant: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve manufacturer specifications for a vehicle using Claude AI.

    Returns a spec_data dict with engine, transmission, dimensions, and standard
    features. All fields are marked as AI-suggested and require user confirmation
    before being treated as authoritative.

    Args:
        make: Vehicle brand (e.g., "Toyota")
        model: Vehicle model (e.g., "Aqua")
        year: Year of manufacture (e.g., 2015)
        variant: Optional trim/grade (e.g., "G grade", "X grade")

    Returns:
        dict matching VehicleSpecData structure, with source="ai_claude" and
        retrieved_at set to now. Returns empty dict with confidence=0.0 if
        Claude cannot identify the vehicle.
    """
    if not is_anthropic_configured():
        logger.warning("[SPEC ENRICHMENT] ANTHROPIC_API_KEY not configured — returning empty specs")
        return {"confidence": 0.0, "source": "unconfigured"}

    vehicle_description = f"{year} {make} {model}"
    if variant:
        vehicle_description += f" ({variant})"

    prompt = f"""You are a vehicle specification database for the Sri Lankan automotive market.
Most vehicles in Sri Lanka are Japanese domestic market (JDM) reconditioned imports.

Vehicle to look up: {vehicle_description}

Return ONLY a JSON object with the following structure. If you are not confident about a field, return null for that field. Do not guess or fabricate data.

{{
  "engine_type": "e.g. Inline-4 DOHC or null",
  "displacement_cc": 1498,
  "transmission": "e.g. CVT, Automatic, Manual or null",
  "wheel_drive": "e.g. FWD, RWD, AWD, 4WD or null",
  "fuel_type": "e.g. Petrol, Diesel, Hybrid (Petrol) or null",
  "fuel_economy_kmpl": 21.4,
  "length_mm": 3995,
  "width_mm": 1695,
  "height_mm": 1445,
  "wheelbase_mm": 2550,
  "seating_capacity": 5,
  "doors": 4,
  "standard_features": {{
    "air_condition": true,
    "dual_air_condition": false,
    "power_window": true,
    "power_steering": true,
    "airbag_count": 2,
    "abs_standard": true
  }},
  "safety_rating": "e.g. 5-star JNCAP or null",
  "confidence": 0.90,
  "notes": "any important notes about trim variants or market differences"
}}

IMPORTANT RULES:
1. Use Japanese domestic market (JDM) specifications as primary source for Japanese brands (Toyota, Honda, Nissan, Suzuki, Mitsubishi, Mazda, Subaru, Daihatsu)
2. For fuel_economy_kmpl: use JC08 cycle rating for Japanese vehicles, WLTP for European vehicles
3. For standard_features: reflect the base/common trim unless a specific variant was provided
4. If a specific variant was provided (e.g. "G grade"), reflect that trim's standard equipment
5. confidence should reflect how certain you are about this specific model-year-variant combination:
   - 0.9-1.0: Very well known model, high certainty
   - 0.7-0.9: Known model, minor uncertainty about specific year details
   - 0.5-0.7: Less certain, may be a niche or regional variant
   - Below 0.5: Not confident — return null for uncertain fields instead
6. Return ONLY the JSON object — no markdown, no explanations, just raw JSON"""

    try:
        client = get_anthropic_client()

        message = client.messages.create(
            model=AI_DEFAULT_MODEL,
            max_tokens=1024,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            start_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("{")), 0)
            end_idx = next(
                (i for i in range(len(lines) - 1, -1, -1) if lines[i].strip().startswith("}")),
                len(lines) - 1
            ) + 1
            response_text = "\n".join(lines[start_idx:end_idx])

        parsed = json.loads(response_text)

        # Validate confidence is in range
        confidence = parsed.get("confidence")
        if confidence is not None:
            confidence = max(0.0, min(1.0, float(confidence)))
        else:
            confidence = 0.5

        spec_data: Dict[str, Any] = {
            "source": "ai_claude",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
        }

        # Copy valid fields from parsed response
        simple_fields = [
            "engine_type", "displacement_cc", "transmission", "wheel_drive",
            "fuel_type", "fuel_economy_kmpl", "length_mm", "width_mm",
            "height_mm", "wheelbase_mm", "seating_capacity", "doors", "safety_rating",
        ]
        for field in simple_fields:
            if parsed.get(field) is not None:
                spec_data[field] = parsed[field]

        # Handle standard_features nested object
        features = parsed.get("standard_features")
        if features and isinstance(features, dict):
            spec_data["standard_features"] = {
                k: v for k, v in features.items() if v is not None
            }

        logger.info(
            f"[SPEC ENRICHMENT] {vehicle_description}: confidence={confidence:.2f}, "
            f"fields={len([k for k in spec_data if k not in ('source', 'retrieved_at', 'confidence')])}"
        )
        return spec_data

    except json.JSONDecodeError as e:
        logger.error(f"[SPEC ENRICHMENT] JSON parse failed for {vehicle_description}: {e}")
        return {"confidence": 0.0, "source": "ai_claude", "error": "parse_failed"}
    except Exception as e:
        logger.error(f"[SPEC ENRICHMENT] Error for {vehicle_description}: {e}\n{traceback.format_exc()}")
        return {"confidence": 0.0, "source": "ai_claude", "error": str(e)}
