"""
AI narrative generation router (building and land descriptions).
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from .. import models
from ..auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["narratives"])


@router.post("/api/building/generate-description")
async def generate_building_description_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Generate professional building description using AI."""
    try:
        from ..services.building_narrative import generate_building_narrative

        description = await generate_building_narrative(
            building_name=request.get("building_name", "Building"),
            building_type=request.get("building_type", "residential"),
            stories=request.get("stories", 1),
            floors=request.get("floors"),
            construction_materials=request.get("construction_materials"),
            utilities_services=request.get("utilities_services"),
            total_floor_area=request.get("total_floor_area"),
            building_age=request.get("building_age"),
            condition=request.get("condition"),
            roof_types=request.get("roof_types"),
            wall_types=request.get("wall_types"),
            floor_types=request.get("floor_types")
        )

        if not description:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate description - check API key"
            )

        return {
            "status": "success",
            "description": description,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Building description generation failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating building description: {str(e)}"
        )


@router.post("/api/land/generate-description")
async def generate_land_description_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """Generate professional land description using AI."""
    try:
        from ..services.land_narrative import generate_land_narrative

        description = await generate_land_narrative(
            land_shape=request.get("land_shape"),
            land_type=request.get("land_type"),
            land_level=request.get("land_level"),
            land_level_difference=request.get("land_level_difference"),
            land_frontage_type=request.get("land_frontage_type"),
            land_frontage_width=request.get("land_frontage_width"),
            land_frontage_description=request.get("land_frontage_description"),
            soil_type=request.get("soil_type"),
            water_table_depth=request.get("water_table_depth"),
            flood_risk=request.get("flood_risk"),
            land_condition=request.get("land_condition"),
            elevation_changes=request.get("elevation_changes"),
            drainage_pattern=request.get("drainage_pattern"),
            vegetation_type=request.get("vegetation_type"),
            natural_features=request.get("natural_features")
        )

        if not description:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate land description. Please check ANTHROPIC_API_KEY configuration."
            )

        return {
            "status": "success",
            "description": description,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Land description generation failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating land description: {str(e)}"
        )
