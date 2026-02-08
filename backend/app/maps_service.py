"""
Google Maps API Service
Handles all interactions with Google Maps APIs for location and routing functionality
"""

import os
import requests
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode
import base64
from .utils.api_client import google_maps_client, CircuitBreakerOpen

logger = logging.getLogger(__name__)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

class GoogleMapsService:
    """Service class for Google Maps API interactions"""

    BASE_URL = "https://maps.googleapis.com/maps/api"

    @staticmethod
    def geocode_address(address: str) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates using Geocoding API
        Returns: {lat, lng, formatted_address, address_components}
        """
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key not configured")

        url = f"{GoogleMapsService.BASE_URL}/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_MAPS_API_KEY
        }

        try:
            response = google_maps_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except CircuitBreakerOpen as e:
            logger.error(f"Circuit breaker open for geocoding: {e}")
            return None
        except requests.Timeout as e:
            logger.error(f"Geocoding timeout for address '{address}': {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"Geocoding request failed for address '{address}': {e}")
            return None

        if data.get("status") == "OK" and len(data.get("results", [])) > 0:
            result = data["results"][0]
            location = result["geometry"]["location"]

            # Extract administrative components
            components = result.get("address_components", [])
            district = None
            province = None
            village = None

            for component in components:
                types = component.get("types", [])
                if "administrative_area_level_2" in types:
                    district = component.get("long_name")
                elif "administrative_area_level_1" in types:
                    province = component.get("long_name")
                elif "locality" in types or "sublocality" in types:
                    village = component.get("long_name")

            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": result.get("formatted_address"),
                "district": district,
                "province": province,
                "village": village,
                "address_components": components
            }

        return None

    @staticmethod
    def places_autocomplete(input_text: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get place suggestions using Places Autocomplete API
        Returns: list of {description, place_id, structured_formatting}
        """
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key not configured")

        url = f"{GoogleMapsService.BASE_URL}/place/autocomplete/json"
        params = {
            "input": input_text,
            "key": GOOGLE_MAPS_API_KEY,
            "components": "country:lk"  # Restrict to Sri Lanka
        }

        if location:
            params["location"] = location

        try:
            response = google_maps_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except (CircuitBreakerOpen, requests.Timeout, requests.RequestException) as e:
            logger.error(f"Places autocomplete failed for input '{input_text}': {e}")
            return []

        if data.get("status") == "OK":
            return data.get("predictions", [])

        return []

    @staticmethod
    def get_place_details(place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place using Place Details API
        Returns: {lat, lng, formatted_address, name, address_components}
        """
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key not configured")

        url = f"{GoogleMapsService.BASE_URL}/place/details/json"
        params = {
            "place_id": place_id,
            "key": GOOGLE_MAPS_API_KEY,
            "fields": "geometry,formatted_address,name,address_components"
        }

        try:
            response = google_maps_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except (CircuitBreakerOpen, requests.Timeout, requests.RequestException) as e:
            logger.error(f"Place details request failed for place_id '{place_id}': {e}")
            return None

        if data.get("status") == "OK":
            result = data.get("result", {})
            location = result.get("geometry", {}).get("location", {})

            # Extract administrative components
            components = result.get("address_components", [])
            district = None
            province = None
            village = None

            for component in components:
                types = component.get("types", [])
                if "administrative_area_level_2" in types:
                    district = component.get("long_name")
                elif "administrative_area_level_1" in types:
                    province = component.get("long_name")
                elif "locality" in types or "sublocality" in types:
                    village = component.get("long_name")

            return {
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "formatted_address": result.get("formatted_address"),
                "name": result.get("name"),
                "district": district,
                "province": province,
                "village": village,
                "address_components": components
            }

        return None

    @staticmethod
    def get_directions(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Optional[Dict[str, Any]]:
        """
        Get route directions between two points using Directions API
        Returns: {distance_km, duration_minutes, polyline, steps, raw_response}
        """
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key not configured")

        url = f"{GoogleMapsService.BASE_URL}/directions/json"
        params = {
            "origin": f"{origin_lat},{origin_lng}",
            "destination": f"{dest_lat},{dest_lng}",
            "key": GOOGLE_MAPS_API_KEY,
            "mode": "driving"
        }

        try:
            response = google_maps_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except (CircuitBreakerOpen, requests.Timeout, requests.RequestException) as e:
            logger.error(f"Directions request failed from ({origin_lat},{origin_lng}) to ({dest_lat},{dest_lng}): {e}")
            return None

        if data.get("status") == "OK" and len(data.get("routes", [])) > 0:
            route = data["routes"][0]
            leg = route["legs"][0]

            # Extract steps for narrative generation
            steps = []
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("html_instructions", ""),
                    "distance": step["distance"]["text"],
                    "duration": step["duration"]["text"],
                    "maneuver": step.get("maneuver", "")
                })

            return {
                "distance_km": leg["distance"]["value"] / 1000,  # Convert meters to km
                "duration_minutes": leg["duration"]["value"] // 60,  # Convert seconds to minutes
                "distance_text": leg["distance"]["text"],
                "duration_text": leg["duration"]["text"],
                "polyline": route["overview_polyline"]["points"],
                "steps": steps,
                "raw_response": data
            }

        return None

    @staticmethod
    def generate_professional_directions_text(steps: List[Dict[str, Any]],
                                             starting_point: str,
                                             distance_text: str,
                                             duration_text: str = None,
                                             road_position: str = None) -> str:
        """
        Generate professional ACCESS section text from route steps.
        Creates human-readable, professional paragraph suitable for valuation reports.
        """
        if not steps:
            return ""

        import re

        def clean_instruction(instruction: str) -> str:
            """Clean HTML and format instruction text"""
            text = re.sub(r'<[^>]+>', '', instruction)
            text = text.replace('&nbsp;', ' ')
            text = text.strip()
            return text

        def extract_landmark(instruction: str) -> str:
            """Extract landmark/location name from instruction if present"""
            # Look for "Pass by X" patterns
            pass_match = re.search(r'Pass by\s+(.+?)(?:\s+\(|$)', instruction)
            if pass_match:
                return pass_match.group(1).strip()
            # Look for "at X" patterns
            at_match = re.search(r'(?:at|onto)\s+(.+?)(?:\s+for|$)', instruction)
            if at_match:
                return at_match.group(1).strip()
            return None

        # Build the professional narrative
        narrative_parts = []

        # Opening sentence
        narrative_parts.append(f"The subject property can be accessed from {starting_point}.")

        # Process route steps - extract key turns and landmarks
        key_steps = []
        landmarks_mentioned = []

        for i, step in enumerate(steps):
            instruction = clean_instruction(step['instruction'])
            distance = step.get('distance', '')
            maneuver = step.get('maneuver', '')

            # Extract any landmarks
            landmark = extract_landmark(instruction)
            if landmark and landmark not in landmarks_mentioned:
                landmarks_mentioned.append(landmark)

            # Only include significant turns (skip minor "continue" steps)
            if maneuver in ['turn-left', 'turn-right', 'roundabout-left', 'roundabout-right']:
                key_steps.append({
                    'instruction': instruction,
                    'distance': distance,
                    'maneuver': maneuver
                })
            elif i == 0 or i == len(steps) - 1:
                # Always include first and last steps
                key_steps.append({
                    'instruction': instruction,
                    'distance': distance,
                    'maneuver': maneuver
                })

        # Build route description (summarized)
        if key_steps:
            route_desc = []
            for i, step in enumerate(key_steps[:5]):  # Limit to 5 key turns
                instruction = step['instruction']
                if i == 0:
                    route_desc.append(f"Proceed {instruction.lower()}")
                else:
                    # Simplify turn instructions
                    if 'turn left' in instruction.lower():
                        route_desc.append(f"turn left {instruction.split('left')[-1].strip()}")
                    elif 'turn right' in instruction.lower():
                        route_desc.append(f"turn right {instruction.split('right')[-1].strip()}")
                    else:
                        route_desc.append(instruction.lower())

            if route_desc:
                narrative_parts.append(" ".join([s.capitalize() if i == 0 else s for i, s in enumerate(route_desc[:3])]) + ".")

        # Add landmarks if found
        if landmarks_mentioned[:3]:  # Limit to 3 landmarks
            landmark_text = ", ".join(landmarks_mentioned[:3])
            narrative_parts.append(f"Notable landmarks along the route include {landmark_text}.")

        # Add distance and duration
        if duration_text:
            narrative_parts.append(f"The total distance is approximately {distance_text} ({duration_text} by vehicle).")
        else:
            narrative_parts.append(f"The total distance is approximately {distance_text}.")

        # Add road position if provided
        if road_position:
            narrative_parts.append(f"The property is located on the {road_position} of the road.")

        return " ".join(narrative_parts)

    @staticmethod
    def calculate_direction_from_point(origin_lat: float, origin_lng: float,
                                       dest_lat: float, dest_lng: float) -> str:
        """
        Calculate compass direction from origin to destination point
        Returns: "north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"
        """
        import math

        # Calculate bearing
        lat1 = math.radians(origin_lat)
        lat2 = math.radians(dest_lat)
        diff_lng = math.radians(dest_lng - origin_lng)

        x = math.sin(diff_lng) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(diff_lng)

        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360

        # Convert to direction
        if 337.5 <= bearing or bearing < 22.5:
            return "north"
        elif 22.5 <= bearing < 67.5:
            return "north-east"
        elif 67.5 <= bearing < 112.5:
            return "east"
        elif 112.5 <= bearing < 157.5:
            return "south-east"
        elif 157.5 <= bearing < 202.5:
            return "south"
        elif 202.5 <= bearing < 247.5:
            return "south-west"
        elif 247.5 <= bearing < 292.5:
            return "west"
        else:
            return "north-west"

    @staticmethod
    def calculate_road_position(route_polyline: str, property_lat: float, property_lng: float) -> str:
        """
        Determine if property is on left or right side of road based on route geometry
        This is a simplified calculation - in reality would need more sophisticated analysis
        """
        # For now, return a default that user can edit
        # A more sophisticated implementation would decode the polyline and
        # calculate the cross product to determine left/right
        return "on the left side"

    @staticmethod
    def generate_static_map_url(origin_lat: float, origin_lng: float,
                               dest_lat: float, dest_lng: float,
                               polyline: str,
                               width: int = 800, height: int = 600) -> str:
        """
        Generate Static Map API URL with route and markers.

        Note: The polyline is URL-encoded to handle special characters properly.
        Google's encoded polyline format can contain characters that need escaping.
        """
        from urllib.parse import quote

        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key not configured")

        # URL-encode the polyline to handle special characters
        # The encoded polyline format can contain characters like |, \, ~, etc.
        encoded_polyline = quote(polyline, safe='')

        # Build URL manually to handle multiple markers
        base_url = f"{GoogleMapsService.BASE_URL}/staticmap"
        url_parts = [
            f"size={width}x{height}",
            "maptype=roadmap",
            f"markers=color:red%7Clabel:A%7C{origin_lat},{origin_lng}",
            f"markers=color:green%7Clabel:B%7C{dest_lat},{dest_lng}",
            f"path=enc:{encoded_polyline}",
            f"key={GOOGLE_MAPS_API_KEY}"
        ]

        return f"{base_url}?{'&'.join(url_parts)}"

    @staticmethod
    def fetch_static_map_image(url: str) -> Optional[bytes]:
        """
        Fetch the actual image bytes from Static Maps API
        """
        try:
            response = google_maps_client.get(url)
            response.raise_for_status()
            return response.content
        except (CircuitBreakerOpen, requests.Timeout, requests.RequestException) as e:
            logger.error(f"Static map image fetch failed: {e}")
            return None

# Create singleton instance
maps_service = GoogleMapsService()
