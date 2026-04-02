"""
AI-powered vehicle valuation service using Claude AI.
Analyzes vehicle data and suggests market values based on condition, age, mileage, and market trends.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
from .anthropic_client import get_anthropic_client, is_anthropic_configured, AI_DEFAULT_MODEL

logger = logging.getLogger(__name__)


def _calculate_vehicle_age(year_of_manufacture: Optional[int], date_of_first_registration: Optional[str]) -> Optional[int]:
    """Calculate vehicle age in years from manufacture year or registration date."""
    current_year = datetime.now().year

    if year_of_manufacture:
        return current_year - year_of_manufacture

    if date_of_first_registration:
        try:
            # Try DD/MM/YYYY format
            parts = date_of_first_registration.replace("-", "/").split("/")
            if len(parts) == 3:
                year = int(parts[2]) if len(parts[2]) == 4 else int(parts[0])
                return current_year - year
        except (ValueError, IndexError):
            pass

    return None


def _format_condition_summary(vehicle_data: Dict[str, Any]) -> str:
    """Create a summary of the vehicle's condition from various condition fields."""
    conditions = []

    condition_fields = [
        ("running_condition", "Running"),
        ("engine_condition", "Engine"),
        ("gear_box_condition", "Gearbox"),
        ("body_condition", "Body"),
        ("chassis_condition", "Chassis"),
        ("upholstery_condition", "Upholstery"),
        ("underside_condition", "Underside"),
    ]

    for field, label in condition_fields:
        value = vehicle_data.get(field)
        if value:
            conditions.append(f"{label}: {value}")

    # Add brake conditions
    foot_brake = vehicle_data.get("foot_brake_condition")
    parking_brake = vehicle_data.get("parking_brake_condition")
    if foot_brake:
        conditions.append(f"Foot Brake: {foot_brake}")
    if parking_brake:
        conditions.append(f"Parking Brake: {parking_brake}")

    # Add parts availability
    parts_fields = [
        ("body_parts_status", "Body Parts"),
        ("engine_parts_status", "Engine Parts"),
        ("accessories_status", "Accessories"),
    ]
    for field, label in parts_fields:
        value = vehicle_data.get(field)
        if value:
            conditions.append(f"{label} Availability: {value}")

    # Add history flags
    if vehicle_data.get("has_accidents"):
        conditions.append("Has accident history")
    if vehicle_data.get("has_repairs"):
        conditions.append("Has had major repairs")
    if vehicle_data.get("needs_repairs_within_year"):
        conditions.append("Needs repairs within next year")
    if vehicle_data.get("body_parts_replaced"):
        conditions.append("Body parts have been replaced")

    return "\n".join(conditions) if conditions else "No detailed condition data available"


def _format_features_summary(vehicle_data: Dict[str, Any]) -> str:
    """Create a summary of the vehicle's features."""
    features_list = []
    features = vehicle_data.get("features", {}) or {}

    if features.get("air_condition"):
        if features.get("dual_air_condition"):
            features_list.append("Dual A/C")
        else:
            features_list.append("A/C")

    power_features = []
    if features.get("power_steering"):
        power_features.append("Steering")
    if features.get("power_window"):
        power_features.append("Windows")
    if features.get("power_mirror"):
        power_features.append("Mirrors")
    if power_features:
        features_list.append(f"Power: {', '.join(power_features)}")

    if features.get("airbag"):
        num_airbags = features.get("num_airbags", 0)
        features_list.append(f"Airbags ({num_airbags})" if num_airbags else "Airbags")

    # Safety features
    if vehicle_data.get("abs_available"):
        features_list.append("ABS")
    if vehicle_data.get("disc_brake_available"):
        features_list.append("Disc Brakes")

    # Capacity
    seats = features.get("seats")
    doors = features.get("doors")
    if seats:
        features_list.append(f"{seats} seats")
    if doors:
        features_list.append(f"{doors} doors")

    return ", ".join(features_list) if features_list else "Standard features"


async def suggest_vehicle_valuation(vehicle) -> Dict[str, Any]:
    """
    Generate AI-powered valuation suggestions for a vehicle.

    Args:
        vehicle: SQLAlchemy Vehicle model instance or dictionary with vehicle data

    Returns:
        Dictionary with:
        - suggested_market_value: float or None
        - suggested_forced_sale_value: float or None
        - suggested_brand_new_price: float or None
        - valuation_summary: str
        - confidence: float (0.0-1.0)
        - reasoning: str
    """

    if not is_anthropic_configured():
        logger.warning("ANTHROPIC_API_KEY not found, returning placeholder response")
        return {
            "suggested_market_value": None,
            "suggested_forced_sale_value": None,
            "suggested_brand_new_price": None,
            "valuation_summary": "By considering the above facts, the market value of the vehicle valued is estimated.",
            "confidence": None,
            "reasoning": "AI valuation service not available. Please enter values manually."
        }

    # Convert SQLAlchemy model to dict if needed
    if hasattr(vehicle, "__dict__"):
        # It's a SQLAlchemy model
        vehicle_data = {
            key: value for key, value in vehicle.__dict__.items()
            if not key.startswith("_")
        }
    else:
        vehicle_data = dict(vehicle)

    # Extract key information
    make = vehicle_data.get("make", "Unknown")
    model = vehicle_data.get("model", "Unknown")
    year = vehicle_data.get("year_of_manufacture")
    registration_date = vehicle_data.get("date_of_first_registration")
    vehicle_age = _calculate_vehicle_age(year, registration_date)
    mileage = vehicle_data.get("mileage")
    mileage_unit = vehicle_data.get("mileage_unit", "km")
    fuel_type = vehicle_data.get("fuel_type", "Unknown")
    transmission = vehicle_data.get("transmission", "Unknown")
    engine_capacity = vehicle_data.get("cylinder_capacity")
    vehicle_class = vehicle_data.get("class_of_vehicle", "Vehicle")
    country_of_origin = vehicle_data.get("country_of_origin", "Unknown")

    # Format condition and features
    condition_summary = _format_condition_summary(vehicle_data)
    features_summary = _format_features_summary(vehicle_data)

    # Include AI-enriched manufacturer spec data if available
    spec_data = vehicle_data.get("spec_data") or {}
    spec_lines = []
    if spec_data:
        if spec_data.get("fuel_economy_kmpl"):
            spec_lines.append(f"- Manufacturer Rated Fuel Economy: {spec_data['fuel_economy_kmpl']} km/L")
        if spec_data.get("safety_rating"):
            spec_lines.append(f"- Safety Rating: {spec_data['safety_rating']}")
        std_features = spec_data.get("standard_features") or {}
        if std_features.get("airbag_count") is not None:
            spec_lines.append(f"- Factory Airbags: {std_features['airbag_count']}")
        if std_features.get("abs_standard"):
            spec_lines.append("- ABS: Standard equipment")
    spec_section = "\n".join(spec_lines) if spec_lines else "Not available"

    # Existing values (for reference)
    existing_purchase_price = vehicle_data.get("purchase_price")
    existing_market_value = vehicle_data.get("market_value")

    # Build the prompt
    prompt = f"""You are an expert vehicle valuation specialist in Sri Lanka. Analyze the following vehicle data and provide valuation suggestions in Sri Lankan Rupees (LKR).

VEHICLE INFORMATION:
- Make: {make}
- Model: {model}
- Year of Manufacture: {year if year else 'Unknown'}
- Vehicle Age: {f'{vehicle_age} years' if vehicle_age else 'Unknown'}
- Mileage: {f'{mileage:,} {mileage_unit}' if mileage else 'Unknown'}
- Fuel Type: {fuel_type}
- Transmission: {transmission}
- Engine Capacity: {f'{engine_capacity} cc' if engine_capacity else 'Unknown'}
- Vehicle Class: {vehicle_class}
- Country of Origin: {country_of_origin}

MANUFACTURER SPECIFICATIONS (verified data):
{spec_section}

CONDITION ASSESSMENT:
{condition_summary}

FEATURES:
{features_summary}

EXISTING DATA (if available):
- Purchase Price: {f'LKR {existing_purchase_price:,.2f}' if existing_purchase_price else 'Not provided'}
- Current Market Value Input: {f'LKR {existing_market_value:,.2f}' if existing_market_value else 'Not provided'}

TASK: Based on the Sri Lankan vehicle market (as of {datetime.now().strftime('%B %Y')}), provide valuation estimates.

Consider these factors:
1. Age depreciation (Sri Lankan vehicles typically depreciate 10-15% per year for first 5 years)
2. Mileage impact (higher mileage reduces value significantly)
3. Condition ratings (each "Poor" or "Very Poor" rating reduces value)
4. Parts availability (rare parts reduce resale value)
5. Accident history significantly reduces value (20-30%)
6. Fuel type (Hybrid/Electric generally command premium)
7. Japanese reconditioned vehicles dominate the Sri Lankan market

Return ONLY a JSON object with this exact structure:
{{
    "suggested_market_value": number or null,
    "suggested_forced_sale_value": number or null,
    "suggested_brand_new_price": number or null,
    "valuation_summary": "string - professional summary for the report",
    "confidence": number between 0 and 1,
    "reasoning": "string - brief explanation of valuation factors considered"
}}

Notes:
- Market value is the fair market price for private sale
- Forced sale value is typically 60-75% of market value (quick/forced sale scenario)
- Brand new price is the current showroom price for an equivalent new vehicle
- If insufficient data for accurate valuation, return null for values and explain in reasoning
- Confidence should reflect how much data was available (0.3 for minimal, 0.9+ for comprehensive)
- Format the valuation_summary as: "By considering the above facts including [key factors], the market value of this [year] [make] [model] is assessed at Rs. [value]"

Return ONLY the JSON object, no additional text."""

    try:
        client = get_anthropic_client()

        # Call Claude API
        message = client.messages.create(
            model=AI_DEFAULT_MODEL,
            max_tokens=1024,
            temperature=0.2,  # Slight variation allowed for market estimates
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
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith("{"):
                    start_idx = i
                    break
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().endswith("}"):
                    end_idx = i + 1
                    break
            response_text = "\n".join(lines[start_idx:end_idx])

        # Parse JSON response
        result = json.loads(response_text)

        # Validate and clean up the response
        suggestion = {
            "suggested_market_value": result.get("suggested_market_value"),
            "suggested_forced_sale_value": result.get("suggested_forced_sale_value"),
            "suggested_brand_new_price": result.get("suggested_brand_new_price"),
            "valuation_summary": result.get("valuation_summary", ""),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning", "")
        }

        # Ensure numeric values are valid
        for key in ["suggested_market_value", "suggested_forced_sale_value", "suggested_brand_new_price"]:
            if suggestion[key] is not None:
                try:
                    suggestion[key] = float(suggestion[key])
                    if suggestion[key] < 0:
                        suggestion[key] = None
                except (ValueError, TypeError):
                    suggestion[key] = None

        # Ensure confidence is valid
        if suggestion["confidence"] is not None:
            try:
                suggestion["confidence"] = float(suggestion["confidence"])
                suggestion["confidence"] = max(0.0, min(1.0, suggestion["confidence"]))
            except (ValueError, TypeError):
                suggestion["confidence"] = 0.5

        logger.info(f"[AI Valuation] Generated suggestion for {make} {model}: Market Value = {suggestion['suggested_market_value']}")

        return suggestion

    except json.JSONDecodeError as e:
        logger.error(f"[AI Valuation] Failed to parse JSON response: {e}")
        return {
            "suggested_market_value": None,
            "suggested_forced_sale_value": None,
            "suggested_brand_new_price": None,
            "valuation_summary": "By considering the above facts, the market value of the vehicle valued is estimated.",
            "confidence": 0.3,
            "reasoning": f"AI response parsing failed. Please enter values manually."
        }

    except Exception as e:
        logger.error(f"[AI Valuation] Error generating valuation: {str(e)}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

        return {
            "suggested_market_value": None,
            "suggested_forced_sale_value": None,
            "suggested_brand_new_price": None,
            "valuation_summary": "By considering the above facts, the market value of the vehicle valued is estimated.",
            "confidence": None,
            "reasoning": f"Error generating AI valuation: {str(e)}. Please enter values manually."
        }
