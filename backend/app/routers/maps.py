"""
Google Maps proxy router.
"""
import logging

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maps", tags=["maps"])


@router.post("/geocode")
async def geocode_address_endpoint(request: dict):
    """Geocode an address to get coordinates and location details.

    Request body: {address: string}
    """
    try:
        from ..maps_service import maps_service
        address = request.get("address")
        if not address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address is required"
            )

        result = maps_service.geocode_address(address)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error geocoding address: {str(e)}"
        )


@router.post("/places/autocomplete")
async def places_autocomplete_endpoint(request: dict):
    """Get place suggestions using Google Places Autocomplete.

    Request body: {input: string, location?: string}
    """
    try:
        from ..maps_service import maps_service
        input_text = request.get("input")
        if not input_text or len(input_text) < 2:
            return []

        location = request.get("location")
        results = maps_service.places_autocomplete(input_text, location)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching autocomplete suggestions: {str(e)}"
        )


@router.post("/places/details")
async def place_details_endpoint(request: dict):
    """Get detailed information about a place from place_id.

    Request body: {place_id: string}
    """
    try:
        from ..maps_service import maps_service
        place_id = request.get("place_id")
        if not place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Place ID is required"
            )

        result = maps_service.get_place_details(place_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place not found"
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching place details: {str(e)}"
        )


@router.post("/directions")
async def directions_endpoint(request: dict):
    """Get route directions between two points.

    Request body: {origin_lat, origin_lng, dest_lat, dest_lng}
    """
    try:
        from ..maps_service import maps_service
        origin_lat = request.get("origin_lat")
        origin_lng = request.get("origin_lng")
        dest_lat = request.get("dest_lat")
        dest_lng = request.get("dest_lng")

        if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Origin and destination coordinates are required"
            )

        result = maps_service.get_directions(origin_lat, origin_lng, dest_lat, dest_lng)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        if result.get("steps"):
            starting_point = request.get("starting_point_name", "the starting point")
            result["professional_text"] = maps_service.generate_professional_directions_text(
                result["steps"],
                starting_point,
                result["distance_text"]
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching directions: {str(e)}"
        )


@router.post("/static-map")
async def static_map_endpoint(request: dict):
    """Generate static map URL with route.

    Request body: {origin_lat, origin_lng, dest_lat, dest_lng, polyline, width?, height?}
    """
    try:
        from ..maps_service import maps_service

        logger.debug(f"Received static map request: {request}")

        origin_lat = request.get("origin_lat")
        origin_lng = request.get("origin_lng")
        dest_lat = request.get("dest_lat")
        dest_lng = request.get("dest_lng")
        polyline = request.get("polyline")

        if not all([origin_lat, origin_lng, dest_lat, dest_lng, polyline]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All coordinates and polyline are required"
            )

        width = request.get("width", 800)
        height = request.get("height", 600)

        url = maps_service.generate_static_map_url(
            origin_lat, origin_lng, dest_lat, dest_lng, polyline, width, height
        )

        return {"map_url": url}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Static map generation failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating static map: {str(e)}"
        )


@router.post("/transform-access")
async def transform_access_endpoint(request: dict):
    """Transform Google Maps directions into professional valuation report format."""
    try:
        from ..services.access import (
            transform_directions_to_professional,
            generate_fallback_access_text,
            extract_navigation_entities
        )

        starting_point_name = request.get("starting_point_name")
        steps = request.get("steps", [])
        road_conditions = request.get("road_conditions", [])
        road_segments = request.get("road_segments", [])
        total_distance_km = request.get("total_distance_km", 0)
        total_duration_mins = request.get("total_duration_mins", 0)
        property_position = request.get("property_position", "right")

        logger.info(f"[TRANSFORM_ACCESS] Request received:")
        logger.debug(f"  Starting point: {starting_point_name}")
        logger.debug(f"  Steps count: {len(steps)}")

        if not starting_point_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="starting_point_name is required"
            )

        try:
            professional_text = transform_directions_to_professional(
                starting_point_name=starting_point_name,
                total_distance_km=total_distance_km,
                total_duration_mins=total_duration_mins,
                property_position=property_position,
                road_conditions=road_conditions,
                road_segments=road_segments,
                steps=steps
            )
        except Exception as ai_error:
            logger.warning(f"[WARN] AI transformation failed, using fallback: {ai_error}")
            navigation_entities = extract_navigation_entities(steps) if steps else None
            professional_text = generate_fallback_access_text(
                starting_point_name=starting_point_name,
                total_distance_km=total_distance_km,
                total_duration_mins=total_duration_mins,
                property_position=property_position,
                navigation_entities=navigation_entities
            )

        return {"professional_text": professional_text}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Access transformation failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transforming access directions: {str(e)}"
        )
