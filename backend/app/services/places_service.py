"""
Google Places API integration service for fetching nearby facilities and location data.
"""
import os
import logging
import httpx
from typing import List, Dict, Optional, Tuple
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Facility type mappings for Google Places API
FACILITY_TYPE_MAPPINGS = {
    "hospital": {"types": ["hospital"], "label": "Hospitals"},
    "police": {"types": ["police"], "label": "Police Stations"},
    "post_office": {"types": ["post_office"], "label": "Post Offices"},
    "bank": {"types": ["bank"], "label": "Banks"},
    "school": {"types": ["school", "primary_school", "secondary_school"], "label": "Schools"},
    "place_of_worship": {"types": ["church", "hindu_temple", "mosque", "buddhist_temple"], "label": "Religious Places"},
    "bus_station": {"types": ["bus_station", "transit_station"], "label": "Bus Stands"},
    "train_station": {"types": ["train_station"], "label": "Railway Stations"},
    "gas_station": {"types": ["gas_station"], "label": "Filling Stations"},
    "lodging": {"types": ["lodging", "hotel"], "label": "Hotels/Resorts"},
    "shopping": {"types": ["shopping_mall", "supermarket"], "label": "Markets/Shopping"},
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on earth (in kilometers).

    Args:
        lat1: Latitude of point 1
        lon1: Longitude of point 1
        lat2: Latitude of point 2
        lon2: Longitude of point 2

    Returns:
        Distance in kilometers
    """
    from math import radians, cos, sin, asin, sqrt

    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def format_place_name(name: str) -> str:
    """
    Format place name from Google Places API.
    Handles mixed casing issues - MODERATE mode.

    Examples:
        "COLOMBO 7" -> "Colombo 7"
        "bus stand" -> "Bus Stand"
        "ColOMbo" -> "Colombo"

    Args:
        name: Raw place name from Google Places API

    Returns:
        Properly formatted place name
    """
    if not name:
        return name

    name = name.strip()

    # Check for all uppercase or all lowercase
    is_all_upper = name.isupper()
    is_all_lower = name.islower()

    # Check for random capitals (e.g., "ColOMbo")
    has_random_caps = any(
        name[i].islower() and name[i+1].isupper()
        for i in range(len(name)-1)
        if name[i].isalpha() and name[i+1].isalpha()
    )

    if is_all_upper or is_all_lower or has_random_caps:
        return name.title()

    return name


async def fetch_nearby_facilities(
    latitude: float,
    longitude: float,
    radius_meters: int = 5000,
    facility_types: Optional[List[str]] = None
) -> Dict[str, List[Dict]]:
    """
    Fetch nearby facilities using Google Places API Nearby Search.

    Args:
        latitude: Property latitude
        longitude: Property longitude
        radius_meters: Search radius in meters (default 5000m = 5km)
        facility_types: List of facility types to search for (defaults to all)

    Returns:
        Dictionary mapping facility categories to lists of facility objects
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Places API is not configured. Please contact support."
        )

    if facility_types is None:
        facility_types = list(FACILITY_TYPE_MAPPINGS.keys())

    results = {}

    async with httpx.AsyncClient(timeout=10) as http_client:
        for facility_category in facility_types:
            if facility_category not in FACILITY_TYPE_MAPPINGS:
                continue

            mapping = FACILITY_TYPE_MAPPINGS[facility_category]
            category_results = []

            # Search for each type within the category
            for place_type in mapping["types"]:
                try:
                    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                    params = {
                        "location": f"{latitude},{longitude}",
                        "radius": radius_meters,
                        "type": place_type,
                        "key": GOOGLE_PLACES_API_KEY
                    }

                    response = await http_client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()

                    if data.get("status") == "OK":
                        places = data.get("results", [])

                        # Process each place
                        for place in places[:5]:  # Limit to top 5 per type
                            place_lat = place["geometry"]["location"]["lat"]
                            place_lng = place["geometry"]["location"]["lng"]

                            # Calculate distance
                            distance_km = haversine_distance(latitude, longitude, place_lat, place_lng)

                            facility_obj = {
                                "type": facility_category,
                                "google_type": place_type,
                                "name": format_place_name(place.get("name", "Unknown")),
                                "address": format_place_name(place.get("vicinity", "")),
                                "distance_km": round(distance_km, 2),
                                "latitude": place_lat,
                                "longitude": place_lng,
                                "place_id": place.get("place_id", ""),
                                "selected": True  # Default to selected
                            }

                            category_results.append(facility_obj)

                except Exception as e:
                    logger.error("Error fetching %s: %s", place_type, e)
                    continue

        # Sort by distance and remove duplicates
        category_results = sorted(category_results, key=lambda x: x["distance_km"])

        # Remove duplicates based on name and distance (within 100m)
        unique_results = []
        for facility in category_results:
            is_duplicate = False
            for existing in unique_results:
                if (existing["name"] == facility["name"] and
                    abs(existing["distance_km"] - facility["distance_km"]) < 0.1):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_results.append(facility)

            # Keep top 3 closest facilities per category
            results[facility_category] = unique_results[:3]

    return results


async def get_distance_to_major_town(
    latitude: float,
    longitude: float,
    town_name: Optional[str] = None
) -> Tuple[Optional[str], Optional[float]]:
    """
    Get the distance to the nearest major town or a specific town.

    Args:
        latitude: Property latitude
        longitude: Property longitude
        town_name: Optional specific town name to get distance to

    Returns:
        Tuple of (town_name, distance_km)
    """
    if not GOOGLE_PLACES_API_KEY:
        return (None, None)

    try:
        async with httpx.AsyncClient(timeout=10) as http_client:
            # If specific town provided, geocode it
            if town_name:
                geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "address": f"{town_name}, Sri Lanka",
                    "key": GOOGLE_PLACES_API_KEY
                }
                response = await http_client.get(geocode_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and len(data.get("results", [])) > 0:
                    location = data["results"][0]["geometry"]["location"]
                    town_lat = location["lat"]
                    town_lng = location["lng"]

                    distance_km = haversine_distance(latitude, longitude, town_lat, town_lng)
                    return (town_name, round(distance_km, 2))

            # Otherwise, search for nearby localities
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": 20000,  # 20km radius
                "type": "locality",
                "key": GOOGLE_PLACES_API_KEY
            }

            response = await http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK":
                places = data.get("results", [])

                # Find the nearest town (skip the immediate village)
                for place in places:
                    place_lat = place["geometry"]["location"]["lat"]
                    place_lng = place["geometry"]["location"]["lng"]
                    distance_km = haversine_distance(latitude, longitude, place_lat, place_lng)

                    # Skip very close places (likely the village itself)
                    if distance_km > 0.5:
                        return (format_place_name(place.get("name", "Unknown")), round(distance_km, 2))

    except Exception as e:
        logger.error("Error getting distance to major town: %s", e)

    return (None, None)


async def find_nearest_transport(
    latitude: float,
    longitude: float
) -> Dict[str, Optional[Dict]]:
    """
    Find the nearest bus stop and railway station.

    Args:
        latitude: Property latitude
        longitude: Property longitude

    Returns:
        Dictionary with 'bus_stop' and 'railway_station' keys containing facility info
    """
    if not GOOGLE_PLACES_API_KEY:
        return {"bus_stop": None, "railway_station": None}

    result = {"bus_stop": None, "railway_station": None}

    try:
        async with httpx.AsyncClient(timeout=10) as http_client:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": 2000,  # 2km radius
                "type": "bus_station",
                "key": GOOGLE_PLACES_API_KEY
            }

            response = await http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK" and len(data.get("results", [])) > 0:
                place = data["results"][0]
                place_lat = place["geometry"]["location"]["lat"]
                place_lng = place["geometry"]["location"]["lng"]
                distance_km = haversine_distance(latitude, longitude, place_lat, place_lng)

                result["bus_stop"] = {
                    "name": format_place_name(place.get("name", "Bus Stop")),
                    "distance_km": round(distance_km, 2)
                }

            # Find nearest railway station
            params["type"] = "train_station"
            params["radius"] = 10000  # 10km radius for railway

            response = await http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK" and len(data.get("results", [])) > 0:
                place = data["results"][0]
                place_lat = place["geometry"]["location"]["lat"]
                place_lng = place["geometry"]["location"]["lng"]
                distance_km = haversine_distance(latitude, longitude, place_lat, place_lng)

                result["railway_station"] = {
                    "name": format_place_name(place.get("name", "Railway Station")),
                    "distance_km": round(distance_km, 2)
                }

    except Exception as e:
        logger.error("Error finding nearest transport: %s", e)

    return result
