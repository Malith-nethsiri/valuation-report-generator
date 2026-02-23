# Barrel re-exports — zero caller changes required.
# All names that were previously in schemas.py are available here.

# Pydantic primitives that main.py references via schemas.BaseModel (pre-router-split)
from pydantic import BaseModel

from .validators import (
    sanitize_dangerous_characters,
    validate_sri_lankan_nic,
    validate_passport,
    validate_date_format,
    normalize_date_format,
    validate_id_number,
)

from .auth_schemas import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    BankAccount,
    BankAccountCreate,
    BankAccountUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    PasswordResetResponse,
    SendVerificationRequest,
    VerifyEmailRequest,
    EmailVerificationResponse,
    RoleUpdate,
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
)

from .building_schemas import (
    DeedInfo,
    RoadCondition,
    RoofDetails,
    WallDetails,
    FloorDetails,
    DoorsWindowsDetails,
    AccommodationSummary,
    WallConstruction,
    ConstructionMaterials,
    Electricity,
    Parking,
    UtilitiesServices,
    Room,
    Floor,
    BuildingPhoto,
    Building,
)

from .invoice_schemas import (
    InvoiceItem,
    InvoiceData,
)

from .misc_schemas import (
    HealthResponse,
    TemplateMetadata,
    TemplateListResponse,
    JobCreate,
    JobResponse,
    JobStatusResponse,
)

from .report_schemas import (
    IdentificationFields,
    ApplicantFields,
    LocationFields,
    LandFields,
    BuildingFields,
    LocalityFields,
    LegalFields,
    ValuationFields,
    CertificationFields,
    ReportBase,
    ReportCreate,
    ReportUpdate,
    BareLandReportCreate,
    ResidentialReportCreate,
    ReportUpdateRequest,
    ReportResponse,
    ReportStats,
    PaginatedReportResponse,
    UserDataResponse,
    DocxGenerateRequest,
)

from .property_schemas import (
    PropertyBase,
    PropertyCreate,
    PropertyUpdate,
    PropertyStatusUpdate,
    PropertyResponse,
    PropertyTemplateResponse,
    ReportPropertyBase,
    ReportPropertyCreate,
    ReportPropertyUpdate,
    ReportPropertyResponse,
    MultiPropertyReportCreate,
    MultiPropertyReportResponse,
)

from .vehicle_schemas import (
    VehiclePhoto,
    VehicleTyreSet,
    VehicleTyres,
    VehicleSuspension,
    VehicleElectrical,
    VehicleLights,
    VehicleFeatures,
    VehicleOfficeData,
    VehiclePastValuation,
    VehicleBase,
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleTemplateResponse,
    ReportVehicleBase,
    ReportVehicleCreate,
    ReportVehicleUpdate,
    ReportVehicleResponse,
    VehicleValuationSuggestion,
)

__all__ = [
    # pydantic primitives (compatibility — used via schemas.BaseModel in main.py pre-router-split)
    "BaseModel",
    # validators
    "sanitize_dangerous_characters",
    "validate_sri_lankan_nic",
    "validate_passport",
    "validate_date_format",
    "normalize_date_format",
    "validate_id_number",
    # auth
    "UserBase", "UserCreate", "UserLogin", "UserResponse", "UserUpdate",
    "TokenResponse", "RefreshTokenRequest", "RefreshTokenResponse",
    "BankAccount", "BankAccountCreate", "BankAccountUpdate",
    "ForgotPasswordRequest", "ResetPasswordRequest", "PasswordResetResponse",
    "SendVerificationRequest", "VerifyEmailRequest", "EmailVerificationResponse",
    "RoleUpdate", "GoogleAuthUrlResponse", "GoogleCallbackRequest",
    # building
    "DeedInfo", "RoadCondition", "RoofDetails", "WallDetails", "FloorDetails",
    "DoorsWindowsDetails", "AccommodationSummary", "WallConstruction",
    "ConstructionMaterials", "Electricity", "Parking", "UtilitiesServices",
    "Room", "Floor", "BuildingPhoto", "Building",
    # invoice
    "InvoiceItem", "InvoiceData",
    # misc
    "HealthResponse", "TemplateMetadata", "TemplateListResponse",
    "JobCreate", "JobResponse", "JobStatusResponse",
    # report
    "IdentificationFields", "ApplicantFields", "LocationFields", "LandFields",
    "BuildingFields", "LocalityFields", "LegalFields", "ValuationFields",
    "CertificationFields", "ReportBase", "ReportCreate", "ReportUpdate",
    "BareLandReportCreate", "ResidentialReportCreate", "ReportUpdateRequest",
    "ReportResponse", "ReportStats", "PaginatedReportResponse",
    "UserDataResponse", "DocxGenerateRequest",
    # property
    "PropertyBase", "PropertyCreate", "PropertyUpdate", "PropertyStatusUpdate",
    "PropertyResponse", "PropertyTemplateResponse",
    "ReportPropertyBase", "ReportPropertyCreate", "ReportPropertyUpdate",
    "ReportPropertyResponse", "MultiPropertyReportCreate", "MultiPropertyReportResponse",
    # vehicle
    "VehiclePhoto", "VehicleTyreSet", "VehicleTyres", "VehicleSuspension",
    "VehicleElectrical", "VehicleLights", "VehicleFeatures", "VehicleOfficeData",
    "VehiclePastValuation", "VehicleBase", "VehicleCreate", "VehicleUpdate",
    "VehicleResponse", "VehicleTemplateResponse",
    "ReportVehicleBase", "ReportVehicleCreate", "ReportVehicleUpdate",
    "ReportVehicleResponse", "VehicleValuationSuggestion",
]
