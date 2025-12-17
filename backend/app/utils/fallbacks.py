"""
Fallback mechanisms for external service failures.

Provides graceful degradation when external APIs (Google Maps, Claude AI, OCR) fail.
Instead of crashing, the system returns helpful default values or manual entry prompts.

Benefits:
- Application remains functional even when external services are down
- Better user experience with helpful error messages
- Reduced dependency on third-party services
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class ServiceFallback:
    """Fallback handlers for external service failures"""

    @staticmethod
    def google_maps_geocoding_fallback(address: str) -> Dict[str, Any]:
        """
        Fallback when Google Maps Geocoding API fails.

        Returns a helpful message and prompts for manual entry.
        """
        logger.warning(f"Google Maps geocoding failed for address: {address}")

        return {
            "success": False,
            "error": "geocoding_unavailable",
            "message": "Address lookup service is temporarily unavailable. Please enter location details manually.",
            "fallback_data": {
                "lat": None,
                "lng": None,
                "formatted_address": address,
                "district": None,
                "province": None,
                "village": None,
                "manual_entry_required": True
            },
            "user_instructions": [
                "Enter GPS coordinates manually if available",
                "Fill in district and province fields",
                "Add detailed address information"
            ]
        }

    @staticmethod
    def google_maps_directions_fallback(origin: str, destination: str) -> Dict[str, Any]:
        """
        Fallback when Google Maps Directions API fails.

        Returns template text for manual directions entry.
        """
        logger.warning(f"Google Maps directions failed from {origin} to {destination}")

        return {
            "success": False,
            "error": "directions_unavailable",
            "message": "Route calculation service is temporarily unavailable.",
            "fallback_data": {
                "distance_km": None,
                "duration_minutes": None,
                "polyline": None,
                "steps": [],
                "access_directions_text": f"The property can be accessed from {origin}. [Please add detailed directions manually]",
                "manual_entry_required": True
            },
            "user_instructions": [
                "Describe the route from the starting point to the property",
                "Include landmarks and turn-by-turn directions",
                "Estimate distance and travel time"
            ]
        }

    @staticmethod
    def google_maps_places_fallback(query: str) -> List[Dict[str, Any]]:
        """
        Fallback when Google Maps Places Autocomplete fails.

        Returns empty list and prompts manual entry.
        """
        logger.warning(f"Google Maps places autocomplete failed for query: {query}")

        return []

    @staticmethod
    def claude_ai_fallback(task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Fallback when Claude AI API fails.

        Returns template text based on the task type.
        """
        logger.warning(f"Claude AI failed for task: {task}")

        templates = {
            "building_description": {
                "text": "[Building description placeholder - Please provide detailed information about the building's construction, condition, and features]",
                "fields_to_complete": [
                    "Building type and purpose",
                    "Construction materials and quality",
                    "Number of rooms and layout",
                    "Current condition and age",
                    "Notable features or amenities"
                ]
            },
            "land_description": {
                "text": "[Land description placeholder - Please describe the land's characteristics, topography, and condition]",
                "fields_to_complete": [
                    "Land shape and topography",
                    "Soil type and quality",
                    "Vegetation and natural features",
                    "Drainage and flood risk",
                    "Overall suitability for intended use"
                ]
            },
            "locality_narrative": {
                "text": "[Locality description placeholder - Please describe the surrounding area, amenities, and accessibility]",
                "fields_to_complete": [
                    "Type of area (urban/suburban/rural)",
                    "Nearby facilities and amenities",
                    "Public transport availability",
                    "Infrastructure and utilities",
                    "General development level"
                ]
            },
            "document_parsing": {
                "text": "[Document parsing unavailable - Please enter information manually]",
                "fields_to_complete": [
                    "Extract relevant data from uploaded documents",
                    "Enter values in corresponding form fields",
                    "Double-check accuracy of extracted information"
                ]
            }
        }

        fallback = templates.get(task, {
            "text": "[AI service unavailable - Please complete this section manually]",
            "fields_to_complete": ["Provide detailed information as required"]
        })

        return {
            "success": False,
            "error": "ai_service_unavailable",
            "message": "AI assistance is temporarily unavailable. Please complete this section manually.",
            "fallback_data": fallback,
            "user_instructions": fallback.get("fields_to_complete", [])
        }

    @staticmethod
    def ocr_fallback(filename: str) -> Dict[str, Any]:
        """
        Fallback when OCR (Google Vision API) fails.

        Returns instructions for manual data entry.
        """
        logger.warning(f"OCR failed for file: {filename}")

        return {
            "success": False,
            "error": "ocr_unavailable",
            "message": "Document scanning service is temporarily unavailable.",
            "fallback_data": {
                "extracted_text": None,
                "confidence": 0.0,
                "manual_entry_required": True
            },
            "user_instructions": [
                "Review the uploaded document manually",
                "Enter plan number, date, and surveyor information",
                "Fill in boundary and extent details from the document",
                "Double-check all entered values for accuracy"
            ]
        }

    @staticmethod
    def static_map_fallback(lat: float, lng: float) -> Dict[str, Any]:
        """
        Fallback when Google Static Maps API fails.

        Returns coordinates-based fallback.
        """
        logger.warning(f"Static map generation failed for coordinates: {lat}, {lng}")

        return {
            "success": False,
            "error": "map_generation_unavailable",
            "message": "Map generation service is temporarily unavailable.",
            "fallback_data": {
                "map_url": None,
                "coordinates": {"lat": lat, "lng": lng},
                "alternative_url": f"https://www.google.com/maps?q={lat},{lng}",
                "manual_instructions": "You can view the location on Google Maps using the alternative URL"
            }
        }


# ===== HELPER FUNCTIONS FOR COMMON FALLBACK SCENARIOS =====

def safe_api_call(api_func, *args, fallback_func=None, fallback_args=None, **kwargs):
    """
    Safely call an external API with automatic fallback on failure.

    Args:
        api_func: The API function to call
        *args: Arguments for the API function
        fallback_func: Fallback function to call on failure
        fallback_args: Arguments for the fallback function
        **kwargs: Keyword arguments for the API function

    Returns:
        API result or fallback result
    """
    try:
        result = api_func(*args, **kwargs)

        # Check if API returned an error indicator
        if isinstance(result, dict) and result.get('error'):
            raise Exception(f"API error: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"API call failed: {api_func.__name__}. Error: {e}")

        if fallback_func:
            fallback_args = fallback_args or []
            return fallback_func(*fallback_args)

        # Generic fallback
        return {
            "success": False,
            "error": "api_failure",
            "message": "Service temporarily unavailable. Please try again or enter data manually.",
            "original_error": str(e)
        }


def is_fallback_response(response: Any) -> bool:
    """
    Check if a response is a fallback response.

    Args:
        response: Response to check

    Returns:
        True if response is a fallback, False otherwise
    """
    if isinstance(response, dict):
        return (
            response.get("success") is False and
            "fallback_data" in response
        )
    return False


def get_fallback_instructions(response: Dict[str, Any]) -> List[str]:
    """
    Extract user instructions from a fallback response.

    Args:
        response: Fallback response

    Returns:
        List of instruction strings
    """
    if is_fallback_response(response):
        return response.get("user_instructions", [])
    return []


# Create singleton instance
service_fallback = ServiceFallback()

# Export commonly used functions
__all__ = [
    'ServiceFallback',
    'service_fallback',
    'safe_api_call',
    'is_fallback_response',
    'get_fallback_instructions'
]
