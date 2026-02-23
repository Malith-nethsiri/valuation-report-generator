from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from .validators import normalize_date_format, validate_date_format


class DeedInfo(BaseModel):
    deed_type: str = Field(..., description="Type of deed (Deed of Gift, Transfer deed, etc.)")
    deed_number: str = Field(..., description="Deed number")
    deed_date: str = Field(..., description="Deed date (DD-MM-YYYY)")
    notary_name: Optional[str] = Field(None, description="Notary name")
    notary_location: Optional[str] = Field(None, description="Notary location")

    @field_validator('deed_date')
    @classmethod
    def validate_deed_date(cls, v):
        if not v:
            raise ValueError("Deed date is required")
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(f'Invalid deed date format: "{v}". Use DD-MM-YYYY format')
        return normalized


class RoadCondition(BaseModel):
    """Road condition information for access routes"""
    road_type: str = Field(..., pattern="^(paved_road|concrete_road|carpet_road|gravel_road|sand_road|earth_road)$", description="Type of road surface")
    condition: str = Field(..., pattern="^(excellent|good|fair|poor)$", description="Road surface condition")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance of this road type in kilometers (optional)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about this road segment")


class RoofDetails(BaseModel):
    structure_type: Optional[str] = Field(None, max_length=100)
    covering_material: Optional[List[str]] = Field(None)
    additional_details: Optional[str] = Field(None, max_length=500)


class WallDetails(BaseModel):
    material: Optional[str] = Field(None, max_length=100)
    finish: Optional[List[str]] = Field(None)


class FloorDetails(BaseModel):
    material: Optional[List[str]] = Field(None)
    finish_quality: Optional[str] = Field(None, max_length=50)


class DoorsWindowsDetails(BaseModel):
    window_frame_material: Optional[List[str]] = Field(None)
    window_glass_type: Optional[List[str]] = Field(None)
    window_security: Optional[List[str]] = Field(None)
    main_door_material: Optional[str] = Field(None, max_length=100)
    internal_door_material: Optional[str] = Field(None, max_length=100)
    door_security: Optional[List[str]] = Field(None)


class AccommodationSummary(BaseModel):
    bedrooms: int = Field(default=0, ge=0)
    bathrooms: int = Field(default=0, ge=0)
    living_rooms: int = Field(default=0, ge=0)
    dining_rooms: int = Field(default=0, ge=0)
    kitchens: int = Field(default=0, ge=0)
    pantries: int = Field(default=0, ge=0)
    verandahs: int = Field(default=0, ge=0)
    balconies: int = Field(default=0, ge=0)
    garages: int = Field(default=0, ge=0)
    store_rooms: int = Field(default=0, ge=0)
    other_rooms: int = Field(default=0, ge=0)


class WallConstruction(BaseModel):
    material: Optional[str] = Field(None, max_length=100, description="Wall material type (DEPRECATED - use WallDetails)")
    thickness: Optional[str] = Field(None, max_length=50, description="Wall thickness (DEPRECATED - use WallDetails)")
    finish: Optional[str] = Field(None, max_length=100, description="Wall finish type (DEPRECATED - use WallDetails)")


class ConstructionMaterials(BaseModel):
    roof_details: Optional[RoofDetails] = Field(None)
    wall_details: Optional[WallDetails] = Field(None)
    floor_details: Optional[FloorDetails] = Field(None)
    ceiling_type: Optional[str] = Field(None, max_length=100)
    doors_windows_details: Optional[DoorsWindowsDetails] = Field(None)

    foundation_type: Optional[str] = Field(None, max_length=100, description="Foundation type (DEPRECATED - no longer collected)")
    wall_construction: Optional[WallConstruction] = Field(None, description="Wall construction details (DEPRECATED - use wall_details)")
    roof_structure: Optional[str] = Field(None, max_length=100, description="Roof structure type (DEPRECATED - use roof_details)")


class Electricity(BaseModel):
    source: Optional[str] = Field(None, max_length=50)
    three_phase: Optional[bool] = Field(None)
    solar_panels: Optional[bool] = Field(None)


class Parking(BaseModel):
    covered_spaces: Optional[int] = Field(None, ge=0)
    uncovered_spaces: Optional[int] = Field(None, ge=0)


class UtilitiesServices(BaseModel):
    water_supply: Optional[List[str]] = Field(None)
    sewage: Optional[str] = Field(None, max_length=100)
    electricity: Optional[Electricity] = Field(None)
    parking: Optional[Parking] = Field(None)
    telephone: Optional[bool] = Field(None)
    internet: Optional[bool] = Field(None)
    gas_connection: Optional[bool] = Field(None)
    security_features: Optional[List[str]] = Field(default_factory=list)
    amenities: Optional[dict] = Field(None)
    hot_water_system: Optional[str] = Field(None, max_length=50)


class Room(BaseModel):
    room_type: str = Field(..., description="Room type (Bedroom, Bathroom, Attached Bathroom, Living Room, etc.)")
    count: int = Field(default=1, ge=1)
    has_attached_bathroom: Optional[bool] = Field(None)


class Floor(BaseModel):
    floor_name: str = Field(..., description="Floor name (e.g., 'Ground Floor')")
    floor_area: Optional[float] = Field(None, ge=0)


class BuildingPhoto(BaseModel):
    id: str = Field(..., description="Photo ID")
    image_data: str = Field(..., description="Base64 encoded image data")
    caption: Optional[str] = Field(None)
    order: int = Field(..., ge=0)


class Building(BaseModel):
    id: str = Field(..., description="Building ID")
    building_name: Optional[str] = Field(None, max_length=200)
    building_type: str = Field(..., max_length=100)
    stories: Optional[int] = Field(None, ge=1)
    building_age: Optional[int] = Field(None, ge=0, le=200)
    condition: Optional[str] = Field(None, max_length=50)
    occupier_name: Optional[str] = Field(None, max_length=300)
    occupier_relationship: Optional[str] = Field(None, max_length=50)
    is_rented: Optional[bool] = Field(None)
    rent_details: Optional[str] = Field(None, max_length=500)
    roof_types: List[str] = Field(default_factory=list)
    roof_description: Optional[str] = Field(None)
    wall_types: List[str] = Field(default_factory=list)
    wall_description: Optional[str] = Field(None)
    floor_types: List[str] = Field(default_factory=list)
    floor_description: Optional[str] = Field(None)
    total_floor_area: Optional[float] = Field(None, ge=0)
    floors: List[Floor] = Field(default_factory=list)
    rooms: List[Room] = Field(default_factory=list)
    accommodation_summary: Optional[AccommodationSummary] = Field(None)
    construction_materials: Optional[ConstructionMaterials] = Field(None)
    utilities_services: Optional[UtilitiesServices] = Field(None)
    conveniences: List[str] = Field(default_factory=list)
    building_description_text: Optional[str] = Field(None)
    building_photos: List[BuildingPhoto] = Field(default_factory=list, max_items=5)
    additional_structures_description: Optional[str] = Field(None, max_length=2000)
