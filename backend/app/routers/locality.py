"""
Locality information and narrative generation router.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from .. import models
from ..auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/locality", tags=["locality"])


@router.post("/nearby-facilities")
async def get_nearby_facilities_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Fetch nearby facilities using Google Places API.

    Request body: {latitude, longitude, radius_meters?, facility_types?}
    """
    try:
        from ..services.places_service import fetch_nearby_facilities, get_distance_to_major_town, find_nearest_transport

        latitude = request.get("latitude")
        longitude = request.get("longitude")
        radius_meters = request.get("radius_meters", 5000)
        facility_types = request.get("facility_types")

        if not latitude or not longitude:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and longitude are required"
            )

        facilities = await fetch_nearby_facilities(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            facility_types=facility_types
        )

        major_town, distance = await get_distance_to_major_town(latitude, longitude)
        transport = await find_nearest_transport(latitude, longitude)

        return {
            "status": "success",
            "facilities": facilities,
            "major_town": {
                "name": major_town,
                "distance_km": distance
            },
            "transport": transport
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Nearby facilities fetch failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching nearby facilities: {str(e)}"
        )


@router.post("/generate-narrative")
async def generate_locality_narrative_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Generate professional locality description using AI.

    Request body: All locality data fields (village, district, facilities, etc.)
    """
    try:
        from ..services.locality_narrative import generate_locality_narrative

        narrative = await generate_locality_narrative(
            property_village=request.get("property_village"),
            property_district=request.get("property_district"),
            divisional_secretariat=request.get("divisional_secretariat"),
            pradeshiya_sabha=request.get("pradeshiya_sabha"),
            distance_to_major_town_km=request.get("distance_to_major_town_km"),
            major_town_name=request.get("major_town_name"),
            nearby_facilities=request.get("nearby_facilities"),
            has_electricity=request.get("has_electricity"),
            water_supply_type=request.get("water_supply_type"),
            telecommunication_types=request.get("telecommunication_types"),
            internet_types=request.get("internet_types"),
            has_public_transport=request.get("has_public_transport"),
            public_transport_routes=request.get("public_transport_routes"),
            public_transport_frequency=request.get("public_transport_frequency"),
            area_type=request.get("area_type"),
            development_level=request.get("development_level"),
            predominant_building_type=request.get("predominant_building_type"),
            is_tourist_area=request.get("is_tourist_area"),
            tourist_attractions_nearby=request.get("tourist_attractions_nearby")
        )

        if not narrative:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate locality narrative"
            )

        return {"status": "success", "narrative": narrative}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Locality narrative generation failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating locality narrative: {str(e)}"
        )
