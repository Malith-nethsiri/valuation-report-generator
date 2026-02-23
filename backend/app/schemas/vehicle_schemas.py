from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List

from .validators import normalize_date_format, validate_date_format


class VehiclePhoto(BaseModel):
    """Vehicle photo structure"""
    id: str = Field(..., description="Photo ID")
    image_data: str = Field(..., description="Base64 encoded image data")
    caption: Optional[str] = Field(None, description="Photo caption")
    order: int = Field(..., ge=0, description="Display order")


class VehicleTyreSet(BaseModel):
    """Tyre information for front or rear set"""
    brand: Optional[str] = Field(None, max_length=100, description="Tyre brand")
    size: Optional[str] = Field(None, max_length=50, description="Tyre size (e.g., 195/65R15)")
    tread_percent: Optional[int] = Field(None, ge=0, le=100, description="Tread percentage (0-100)")
    condition: Optional[str] = Field(None, description="Condition: Excellent/Good/Fair/Poor/Very Poor")


class VehicleTyres(BaseModel):
    """Complete tyre information"""
    front: Optional[VehicleTyreSet] = None
    rear: Optional[VehicleTyreSet] = None
    spare_available: Optional[bool] = Field(None, description="Spare tyre available")
    need_replacement: Optional[bool] = Field(None, description="Tyres need replacement")
    rear_type: Optional[str] = Field(None, description="Single or Dual (for trucks)")


class VehicleSuspension(BaseModel):
    """Suspension information"""
    front: Optional[str] = Field(None, description="Front suspension condition")
    rear: Optional[str] = Field(None, description="Rear suspension condition")


class VehicleElectrical(BaseModel):
    """Electrical system information"""
    starter: Optional[bool] = Field(None, description="Starter working")
    horn: Optional[bool] = Field(None, description="Horn working")
    wiper: Optional[bool] = Field(None, description="Wiper working")
    battery_condition: Optional[str] = Field(None, description="Battery condition: Good/Fair/Poor/Needs Replacement")


class VehicleLights(BaseModel):
    """Lights status"""
    head: Optional[bool] = Field(None, description="Head lights working")
    dim: Optional[bool] = Field(None, description="Dim lights working")
    signal: Optional[bool] = Field(None, description="Signal lights working")
    parking: Optional[bool] = Field(None, description="Parking lights working")
    reverse: Optional[bool] = Field(None, description="Reverse lights working")
    meter: Optional[bool] = Field(None, description="Dashboard/Meter lights working")


class VehicleFeatures(BaseModel):
    """Vehicle features and amenities"""
    air_condition: Optional[bool] = Field(None, description="Air condition working")
    dual_air_condition: Optional[bool] = Field(None, description="Dual air condition")
    power_mirror: Optional[bool] = Field(None, description="Power mirror available")
    power_window: Optional[bool] = Field(None, description="Power window available")
    power_steering: Optional[bool] = Field(None, description="Power steering available")
    airbag: Optional[bool] = Field(None, description="Airbag available")
    num_airbags: Optional[int] = Field(None, ge=0, description="Number of airbags")
    seats: Optional[int] = Field(None, ge=1, description="Number of seats")
    doors: Optional[int] = Field(None, ge=1, description="Number of doors")


class VehicleOfficeData(BaseModel):
    """Office use only fields (for government reports)"""
    civil_no: Optional[str] = Field(None, max_length=100, description="Civil number (government vehicles)")
    military_no: Optional[str] = Field(None, max_length=100, description="Military number (military vehicles)")
    approval_position: Optional[str] = Field(None, max_length=200, description="Approval position")


class VehiclePastValuation(BaseModel):
    """Past valuation entry for comparison table"""
    serial: Optional[int] = Field(None, description="Serial number (auto-generated)")
    civil_no: Optional[str] = Field(None, max_length=100, description="Vehicle No - Civil")
    military_no: Optional[str] = Field(None, max_length=100, description="Vehicle No - Military")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Year of past valuation")
    value: Optional[float] = Field(None, ge=0, description="Past valuation value (Rs)")
    market_value: Optional[float] = Field(None, ge=0, description="Market value (Rs)")


class VehicleBase(BaseModel):
    """Base schema for Vehicle - contains all vehicle-specific fields"""

    # Status & Type
    status: Optional[str] = Field("draft", max_length=50, description="Vehicle status: 'draft' or 'completed'")
    vehicle_type: Optional[str] = Field(None, max_length=50, description="Vehicle type: 'car', 'motorcycle', 'truck', 'special'")
    is_template: Optional[bool] = Field(False, description="Save to Vehicle Library")

    # ===== VEHICLE IDENTIFICATION =====
    registration_number: Optional[str] = Field(None, max_length=50, description="Vehicle registration number")
    provincial_council: Optional[str] = Field(None, max_length=100, description="Provincial council")
    class_of_vehicle: Optional[str] = Field(None, max_length=100, description="Class of vehicle")
    body_colour: Optional[str] = Field(None, max_length=100, description="Body colour")
    chassis_number: Optional[str] = Field(None, max_length=100, description="Chassis number")
    engine_number: Optional[str] = Field(None, max_length=100, description="Engine number")
    vehicle_status: Optional[str] = Field(None, max_length=100, description="Vehicle status")
    country_of_origin: Optional[str] = Field(None, max_length=100, description="Country of origin")
    make: Optional[str] = Field(None, max_length=100, description="Vehicle make/brand")
    model: Optional[str] = Field(None, max_length=200, description="Vehicle model")
    date_of_first_registration: Optional[str] = Field(None, max_length=50, description="Date of first registration")
    year_of_manufacture: Optional[int] = Field(None, ge=1900, le=2100, description="Year of manufacture")
    cylinder_capacity: Optional[int] = Field(None, ge=0, description="Cylinder capacity in cc")
    fuel_type: Optional[str] = Field(None, max_length=50, description="Fuel type")
    mileage: Optional[int] = Field(None, ge=0, description="Mileage")
    mileage_unit: Optional[str] = Field("km", max_length=20, description="Mileage unit: 'km' or 'miles'")

    # ===== ENGINE & TRANSMISSION =====
    engine_type: Optional[str] = Field(None, max_length=100, description="Engine type description")
    transmission: Optional[str] = Field(None, max_length=50, description="Transmission type")
    wheel_drive: Optional[str] = Field(None, max_length=20, description="Wheel drive: 2WD, 4WD, AWD")

    # ===== CONDITION FIELDS =====
    running_condition: Optional[str] = Field(None, max_length=50, description="Running condition")
    clutch_status: Optional[str] = Field(None, max_length=100, description="Clutch status")
    engine_condition: Optional[str] = Field(None, max_length=50, description="Engine condition")
    gear_box_condition: Optional[str] = Field(None, max_length=50, description="Gear box condition")
    differential_status: Optional[str] = Field(None, max_length=100, description="Differential status")
    gear_selection: Optional[str] = Field(None, max_length=50, description="Gear selection quality")
    body_condition: Optional[str] = Field(None, max_length=50, description="Body condition")
    chassis_condition: Optional[str] = Field(None, max_length=50, description="Chassis condition")
    upholstery_condition: Optional[str] = Field(None, max_length=50, description="Upholstery condition")
    underside_condition: Optional[str] = Field(None, max_length=50, description="Underside condition")

    # ===== PARTS AVAILABILITY =====
    body_parts_status: Optional[str] = Field(None, max_length=100, description="Body parts availability")
    engine_parts_status: Optional[str] = Field(None, max_length=100, description="Engine parts availability")
    accessories_status: Optional[str] = Field(None, max_length=100, description="Accessories availability")

    # ===== FUEL & PERFORMANCE =====
    fuel_consumption: Optional[float] = Field(None, ge=0, description="Average fuel consumption")
    fuel_consumption_unit: Optional[str] = Field(None, max_length=20, description="Unit: 'km/L' or 'L/100km'")

    # ===== BRAKES =====
    foot_brake_condition: Optional[str] = Field(None, max_length=50, description="Foot brake condition")
    disc_brake_available: Optional[bool] = Field(None, description="Disc brake available")
    parking_brake_condition: Optional[str] = Field(None, max_length=50, description="Parking brake condition")
    abs_available: Optional[bool] = Field(None, description="ABS available")

    # ===== FEATURES (JSONB) =====
    features: Optional[VehicleFeatures] = Field(None, description="Vehicle features")

    # ===== SUSPENSION (JSONB) =====
    suspension: Optional[VehicleSuspension] = Field(None, description="Suspension information")

    # ===== TYRES (JSONB) =====
    tyres: Optional[VehicleTyres] = Field(None, description="Tyre information")

    # ===== ELECTRICAL (JSONB) =====
    electrical: Optional[VehicleElectrical] = Field(None, description="Electrical system")

    # ===== LIGHTS (JSONB) =====
    lights: Optional[VehicleLights] = Field(None, description="Lights status")

    # ===== HISTORY =====
    has_accidents: Optional[bool] = Field(None, description="Has accident history")
    has_repairs: Optional[bool] = Field(None, description="Has repair history")
    needs_repairs_within_year: Optional[bool] = Field(None, description="Needs repairs within a year")
    body_parts_replaced: Optional[bool] = Field(None, description="Body parts have been replaced")

    # ===== VALUATION =====
    purchase_price: Optional[float] = Field(None, ge=0, description="Purchase price (LKR)")
    brand_new_price: Optional[float] = Field(None, ge=0, description="Brand new price (LKR)")
    market_value: Optional[float] = Field(None, ge=0, description="Market value (LKR)")
    forced_sale_value: Optional[float] = Field(None, ge=0, description="Forced sale value (LKR)")
    valuation_summary: Optional[str] = Field(None, description="Valuation summary text")

    # ===== OFFICE USE =====
    office_data: Optional[VehicleOfficeData] = Field(None, description="Office use only fields")

    # ===== PAST VALUATIONS =====
    past_valuations: Optional[List[VehiclePastValuation]] = Field(None, description="Past valuations for comparison")

    # ===== PHOTOS =====
    vehicle_photos: Optional[List[VehiclePhoto]] = Field(None, max_items=5, description="Vehicle photos (max 5)")
    book_images: Optional[List[VehiclePhoto]] = Field(None, max_items=5, description="Vehicle book images for OCR (max 5)")

    # ===== VALIDATORS =====
    @field_validator('date_of_first_registration')
    @classmethod
    def validate_vehicle_date(cls, v):
        """Validate and normalize date of first registration to DD-MM-YYYY or DD/MM/YYYY format."""
        if v is None:
            return v
        normalized = normalize_date_format(v)
        if not validate_date_format(normalized):
            raise ValueError(f'Invalid date format: "{v}". Use DD-MM-YYYY format')
        return normalized

    @field_validator('registration_number')
    @classmethod
    def normalize_registration_number(cls, v):
        """Normalize vehicle registration number - uppercase and strip whitespace."""
        if v is None:
            return v
        return v.strip().upper()


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle"""
    pass


class VehicleUpdate(VehicleBase):
    """Schema for updating an existing vehicle"""
    pass


class VehicleResponse(VehicleBase):
    """Schema for vehicle response (includes ID and timestamps)"""
    id: int
    user_id: int
    is_deleted: Optional[bool] = False
    original_vehicle_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VehicleTemplateResponse(BaseModel):
    """Simplified vehicle response for Vehicle Library listing"""
    id: int
    make: Optional[str] = None
    model: Optional[str] = None
    registration_number: Optional[str] = None
    year_of_manufacture: Optional[int] = None
    market_value: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportVehicleBase(BaseModel):
    """Base schema for ReportVehicle junction"""
    vehicle_id: int = Field(..., description="ID of the vehicle")
    vehicle_order: int = Field(default=1, ge=1, description="Display order in report (for drag-drop)")
    report_specific_notes: Optional[str] = Field(None, description="Notes specific to this vehicle in this report")
    override_market_value: Optional[float] = Field(None, ge=0, description="Override market value for this report")


class ReportVehicleCreate(ReportVehicleBase):
    """Schema for creating a report-vehicle association"""
    pass


class ReportVehicleUpdate(BaseModel):
    """Schema for updating report-vehicle association"""
    vehicle_order: Optional[int] = Field(None, ge=1)
    report_specific_notes: Optional[str] = None
    override_market_value: Optional[float] = Field(None, ge=0)


class ReportVehicleResponse(ReportVehicleBase):
    """Schema for report-vehicle response (includes full vehicle data)"""
    id: int
    report_id: int
    vehicle: VehicleResponse  # Nested full vehicle data
    created_at: datetime

    class Config:
        from_attributes = True


class VehicleValuationSuggestion(BaseModel):
    """AI-generated valuation suggestion for a vehicle"""
    suggested_market_value: Optional[float] = Field(None, description="AI-suggested market value")
    suggested_forced_sale_value: Optional[float] = Field(None, description="AI-suggested forced sale value")
    suggested_brand_new_price: Optional[float] = Field(None, description="AI-suggested brand new price")
    valuation_summary: Optional[str] = Field(None, description="AI-generated valuation summary")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")
    reasoning: Optional[str] = Field(None, description="Explanation for the valuation")
