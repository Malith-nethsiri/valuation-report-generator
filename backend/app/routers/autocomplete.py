"""
Autocomplete and administrative divisions router (public, no authentication).
"""
import json
import logging
import os

from fastapi import APIRouter, HTTPException, status

from ..autocomplete import get_all_autocomplete_data, search_autocomplete

logger = logging.getLogger(__name__)

router = APIRouter(tags=["autocomplete"])


@router.get("/api/autocomplete")
async def get_autocomplete_data():
    """Get all autocomplete data for professional credentials form."""
    try:
        return get_all_autocomplete_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching autocomplete data: {str(e)}"
        )


@router.get("/api/autocomplete/{category}")
async def search_autocomplete_category(
    category: str,
    q: str = "",
    limit: int = 10
):
    """Search within a specific autocomplete category.

    Categories: membership_levels, academic_qualifications, professional_designations,
    post_nominal_letters, sri_lankan_banks, office_departments, provinces
    """
    try:
        if limit > 50:
            limit = 50

        results = search_autocomplete(category, q, limit)
        return {
            "category": category,
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching autocomplete data: {str(e)}"
        )


@router.get("/api/administrative-divisions")
async def get_administrative_divisions():
    """Get Sri Lankan administrative divisions (Districts and DS Divisions)."""
    try:
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "administrative_divisions.json")

        if not os.path.exists(json_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrative divisions data not found"
            )

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "status": "success",
            "data": data,
            "total_districts": len(data),
            "total_ds_divisions": sum(len(v) for v in data.values())
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrative divisions data file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading administrative divisions: {str(e)}"
        )


@router.get("/api/administrative-divisions/{district}")
async def get_ds_divisions_by_district(district: str):
    """Get DS Divisions for a specific district."""
    try:
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "administrative_divisions.json")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        district_data = None
        for key in data.keys():
            if key.lower() == district.lower():
                district_data = data[key]
                break

        if not district_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"District '{district}' not found"
            )

        return {
            "status": "success",
            "district": district,
            "ds_divisions": district_data
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrative divisions data file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading DS divisions: {str(e)}"
        )
