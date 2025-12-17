from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os
import asyncio
from datetime import timedelta, datetime
from typing import Optional, List

from . import models, schemas, crud
from .database import engine, get_db
from .docx_generator import generate_user_data_docx, get_filename_for_user
from .autocomplete import get_all_autocomplete_data, search_autocomplete
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .services.ocr_service import process_uploaded_document, process_multiple_documents
from .utils.extent_calculator import calculate_extent_data
from .utils.error_responses import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
    add_request_id_middleware
)
from .middleware.rate_limiting import (
    RateLimitMiddleware,
    configure_rate_limits,
    cleanup_task
)

# Load environment variables
load_dotenv()

# ===== FILE UPLOAD SECURITY CONSTANTS =====
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_FILES_PER_UPLOAD = 10

ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/jpg',
    'application/pdf'
}

ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.pdf'
}

# Mapping of magic number signatures to MIME types
MAGIC_NUMBER_SIGNATURES = {
    b'\xFF\xD8\xFF': 'image/jpeg',  # JPEG
    b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
    b'RIFF': 'image/webp',  # WEBP (needs additional check)
    b'%PDF': 'application/pdf',  # PDF
}


def verify_file_type_by_magic_number(file_content: bytes) -> Optional[str]:
    """
    Verify file type using magic number (file signature).

    Returns MIME type if valid, None otherwise.
    """
    # Check magic number signatures
    for signature, mime_type in MAGIC_NUMBER_SIGNATURES.items():
        if file_content.startswith(signature):
            # Special handling for WEBP (check for WEBP after RIFF)
            if signature == b'RIFF' and len(file_content) >= 12:
                if file_content[8:12] == b'WEBP':
                    return mime_type
                else:
                    continue  # Not a WEBP file
            return mime_type

    return None


async def validate_upload_file(file: UploadFile) -> None:
    """
    Validate uploaded file for security.

    Checks:
    - File size (≤ 10MB)
    - File extension is allowed
    - Magic number matches extension (prevents file type spoofing)

    Raises HTTPException if validation fails.
    """
    import os

    # Read file content for validation
    file_content = await file.read()
    file_size = len(file_content)

    # Reset file pointer for later use
    await file.seek(0)

    # 1. Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{file.filename}' is too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB, got {file_size / (1024*1024):.2f}MB"
        )

    # 2. Check file extension
    filename_lower = file.filename.lower() if file.filename else ""
    file_ext = os.path.splitext(filename_lower)[1]

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' has unsupported extension '{file_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 3. Verify magic number (actual file type)
    detected_mime = verify_file_type_by_magic_number(file_content)

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' appears to be a different type than its extension suggests. File validation failed for security reasons."
        )

    # 4. Cross-check: ensure declared content type matches detected type
    if file.content_type and detected_mime:
        # Normalize content types (some browsers send image/jpg instead of image/jpeg)
        declared_type = file.content_type.lower()
        if declared_type == 'image/jpg':
            declared_type = 'image/jpeg'

        if declared_type != detected_mime and not (declared_type.startswith('image/') and detected_mime.startswith('image/')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' type mismatch. Declared: {file.content_type}, Detected: {detected_mime}"
            )


# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Data Collection & DOCX Generator API",
    description="API for collecting user data and generating DOCX documents",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add request logging middleware
app.middleware("http")(add_request_id_middleware)

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ===== STARTUP EVENT =====
@app.on_event("startup")
async def startup_event():
    """Configure rate limits and start background cleanup task on application startup"""
    # Configure rate limits for all endpoints
    configure_rate_limits()

    # Start background task for periodic bucket cleanup
    asyncio.create_task(cleanup_task())


@app.get("/", response_model=schemas.HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "success",
        "message": "Data Collection & DOCX Generator API is running"
    }

@app.get("/api/health", response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "success",
        "message": "API is healthy and running"
    }

# Authentication Endpoints
@app.post("/api/auth/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    - **email**: User's email address (must be unique)
    - **password**: Password (minimum 6 characters)
    - **full_name**: User's full name
    - **phone**: Phone number (optional)
    """
    # Check if user already exists
    existing_user = crud.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Create new user
        db_user = crud.create_user(db, user_data)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": db_user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
async def login_user(
    user_credentials: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user and return access token

    - **email**: User's email address
    - **password**: User's password
    """
    # Authenticate user
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user

# User Profile Endpoints
@app.put("/api/profile", response_model=schemas.UserResponse)
async def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    updated_user = crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

# Letterhead Template Endpoints
@app.get("/api/letterhead-templates", response_model=schemas.TemplateListResponse)
async def get_letterhead_templates():
    """Get all available letterhead templates"""
    from .letterhead_templates import get_all_templates
    templates = get_all_templates()
    return {"templates": [t.to_dict() for t in templates]}

# Report Endpoints (Protected)
@app.post("/api/reports", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: schemas.ReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new report for the authenticated user"""
    print(f"[CREATE REPORT] Received data from frontend:")
    print(f"  property_village: {report_data.property_village}")
    print(f"  property_district: {report_data.property_district}")
    print(f"  grama_niladari_division: {report_data.grama_niladari_division}")
    print(f"  property_divisional_secretariat: {report_data.property_divisional_secretariat}")
    print(f"  korale: {report_data.korale}")
    print(f"  pradeshiya_sabha: {report_data.pradeshiya_sabha}")
    print(f"  access_directions_text: {report_data.access_directions_text}")
    print(f"  location_map_image_data: {report_data.location_map_image_data}")
    print(f"  property_latitude: {report_data.property_latitude}")
    print(f"  property_longitude: {report_data.property_longitude}")
    # Property Description fields
    print(f"  === PROPERTY DESCRIPTION FIELDS ===")
    print(f"  land_shape: {report_data.land_shape}")
    print(f"  land_type: {report_data.land_type}")
    print(f"  soil_type: {report_data.soil_type}")
    print(f"  flood_risk: {report_data.flood_risk}")
    print(f"  land_description_text: {report_data.land_description_text}")
    print(f"  buildings: {report_data.buildings}")
    print(f"  occupier_name: {report_data.occupier_name}")
    print(f"  property_photos count: {len(report_data.property_photos) if report_data.property_photos else 0}")

    try:
        db_report = crud.create_report(db, report_data, current_user.id)
        print(f"[CREATE REPORT] Report created with ID: {db_report.id}")
        return db_report
    except Exception as e:
        print(f"[CREATE REPORT] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating report: {str(e)}"
        )

@app.get("/api/reports", response_model=list[schemas.ReportResponse])
async def get_user_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for the authenticated user (paginated)"""
    return crud.get_user_reports(db, current_user.id, skip=skip, limit=limit)

@app.get("/api/reports/{report_id}", response_model=schemas.ReportResponse)
async def get_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific report by ID (must belong to authenticated user)"""
    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    return db_report

@app.put("/api/reports/{report_id}", response_model=schemas.ReportResponse)
async def update_report(
    report_id: int,
    report_update: schemas.ReportUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a report (must belong to authenticated user)"""
    updated_report = crud.update_report(db, report_id, report_update, current_user.id)
    if not updated_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    return updated_report

@app.delete("/api/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a report (must belong to authenticated user)"""
    success = crud.delete_report(db, report_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    return None

@app.post("/api/reports/{report_id}/generate")
async def generate_report_docx(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a DOCX file from report data combined with user profile data
    """
    print(f"[DOCX_GENERATION] Starting generation for report_id={report_id}, user={current_user.email}")

    # Get report data from database
    db_report = crud.get_report(db, report_id, current_user.id)
    if db_report is None:
        print(f"[DOCX_GENERATION] Report {report_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    print(f"[DOCX_GENERATION] Report found - status: {db_report.status}, type: {db_report.report_type}")
    print(f"[DOCX_GENERATION] Has buildings: {bool(db_report.buildings)}, num_buildings: {len(db_report.buildings) if db_report.buildings else 0}")

    try:
        # Generate DOCX file with both report and user data
        print(f"[DOCX_GENERATION] Calling generate_user_data_docx...")
        docx_stream = generate_user_data_docx(db_report, current_user)
        print(f"[DOCX_GENERATION] DOCX generated successfully, size: {len(docx_stream.getvalue())} bytes")

        filename = get_filename_for_user(db_report)
        print(f"[DOCX_GENERATION] Filename: {filename}")

        # Return as downloadable file
        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[DOCX_GENERATION_ERROR] Error type: {type(e).__name__}")
        print(f"[DOCX_GENERATION_ERROR] Error message: {str(e)}")
        print(f"[DOCX_GENERATION_ERROR] Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating DOCX file: {type(e).__name__}: {str(e)}"
        )

# OCR Document Processing Endpoint
@app.post("/api/ocr/extract")
async def extract_data_from_document(
    files: List[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract property data from uploaded documents (survey plan, deed pages, etc.) using OCR.

    - **files**: Multiple image files (JPEG, PNG, WEBP, PDF) - max 10 files, 10MB each
    - **document_type**: Optional hint ('survey_plan', 'deed', 'title_certificate')

    Returns combined extracted data with confidence scores.
    """
    try:
        # 1. Check maximum number of files
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many files uploaded. Maximum {MAX_FILES_PER_UPLOAD} files allowed, got {len(files)} files"
            )

        # 2. Validate each file (size, extension, magic number)
        for file in files:
            await validate_upload_file(file)

        # Process all documents
        result = await process_multiple_documents(files, document_type)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'OCR processing failed')
            )

        # If extent data was extracted, calculate all derived fields
        extracted_data = result.get('extracted_data', {})
        if extracted_data.get('land_extent_acres') is not None:
            extent_data = calculate_extent_data(
                acres=extracted_data.get('land_extent_acres', 0),
                roods=extracted_data.get('land_extent_roods', 0),
                perches=extracted_data.get('land_extent_perches', 0)
            )
            # Add calculated fields to extracted data
            extracted_data.update(extent_data)
            result['extracted_data'] = extracted_data

        return {
            "status": "success",
            "message": "Document processed successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

# Autocomplete API Endpoints (Public - no authentication required)
@app.get("/api/autocomplete")
async def get_autocomplete_data():
    """
    Get all autocomplete data for professional credentials form
    Returns membership levels, banks, qualifications, designations, etc.
    """
    try:
        return get_all_autocomplete_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching autocomplete data: {str(e)}"
        )

@app.get("/api/autocomplete/{category}")
async def search_autocomplete_category(
    category: str,
    q: str = "",
    limit: int = 10
):
    """
    Search within a specific autocomplete category
    Categories: membership_levels, academic_qualifications, professional_designations,
               post_nominal_letters, sri_lankan_banks, office_departments, provinces
    """
    try:
        if limit > 50:
            limit = 50  # Prevent excessive results

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

# Administrative Divisions Endpoint
@app.get("/api/administrative-divisions")
async def get_administrative_divisions():
    """
    Get Sri Lankan administrative divisions (Districts and DS Divisions)
    Returns hierarchical data: {district: [{name, gn_count}, ...]}
    """
    try:
        import json
        import os

        # Load administrative divisions data
        json_path = os.path.join(os.path.dirname(__file__), "administrative_divisions.json")

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

@app.get("/api/administrative-divisions/{district}")
async def get_ds_divisions_by_district(district: str):
    """
    Get DS Divisions for a specific district
    Returns: [{name, gn_count}, ...]
    """
    try:
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), "administrative_divisions.json")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Find district (case-insensitive)
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

# Google Maps API Proxy Endpoints (Public - for frontend use)
@app.post("/api/maps/geocode")
async def geocode_address_endpoint(request: dict):
    """
    Geocode an address to get coordinates and location details
    Request body: {address: string}
    """
    try:
        from .maps_service import maps_service
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

@app.post("/api/maps/places/autocomplete")
async def places_autocomplete_endpoint(request: dict):
    """
    Get place suggestions using Google Places Autocomplete
    Request body: {input: string, location?: string}
    """
    try:
        from .maps_service import maps_service
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

@app.post("/api/maps/places/details")
async def place_details_endpoint(request: dict):
    """
    Get detailed information about a place from place_id
    Request body: {place_id: string}
    """
    try:
        from .maps_service import maps_service
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

@app.post("/api/maps/directions")
async def directions_endpoint(request: dict):
    """
    Get route directions between two points
    Request body: {origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float}
    """
    try:
        from .maps_service import maps_service
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

        # Also generate professional directions text
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

@app.post("/api/maps/static-map")
async def static_map_endpoint(request: dict):
    """
    Generate static map URL with route
    Request body: {origin_lat, origin_lng, dest_lat, dest_lng, polyline, width?, height?}
    """
    try:
        from .maps_service import maps_service
        import traceback

        print(f"[DEBUG] Received static map request: {request}")

        origin_lat = request.get("origin_lat")
        origin_lng = request.get("origin_lng")
        dest_lat = request.get("dest_lat")
        dest_lng = request.get("dest_lng")
        polyline = request.get("polyline")

        print(f"[DEBUG] Extracted params - origin: ({origin_lat}, {origin_lng}), dest: ({dest_lat}, {dest_lng}), polyline length: {len(polyline) if polyline else 0}")

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

        print(f"[DEBUG] Generated map URL: {url}")

        return {"map_url": url}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Static map generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating static map: {str(e)}"
        )

@app.post("/api/maps/transform-access")
async def transform_access_endpoint(request: dict):
    """
    Transform Google Maps directions with road condition details into professional valuation report format.
    Request body: {
        starting_point_name: str (e.g., "Clock tower junction of Kurunegala town"),
        property_position: str ("left" or "right"),
        total_distance_km: float,
        total_duration_mins: int,
        steps: [{instruction, distance, duration, maneuver}],  # Google Maps turn-by-turn steps
        road_conditions: [{  # NEW: Simplified road conditions
            road_type: str ("paved_road", "carpet_road", "gravel_road", "sand_road", "earth_road"),
            condition: str ("excellent", "good", "fair", "poor"),
            notes: str (optional)
        }],
        road_segments: [{...}]  # DEPRECATED: Old format (kept for backward compatibility)
    }
    """
    try:
        from .services.access_transformer import (
            transform_directions_to_professional,
            generate_fallback_access_text,
            extract_navigation_entities
        )

        starting_point_name = request.get("starting_point_name")
        steps = request.get("steps", [])  # Google Maps turn-by-turn steps
        road_conditions = request.get("road_conditions", [])  # NEW: Simplified road conditions
        road_segments = request.get("road_segments", [])  # OLD: For backward compatibility
        total_distance_km = request.get("total_distance_km", 0)
        total_duration_mins = request.get("total_duration_mins", 0)
        property_position = request.get("property_position", "right")

        # Log received data for debugging
        print(f"\n[TRANSFORM_ACCESS] Request received:")
        print(f"  Starting point: {starting_point_name}")
        print(f"  Steps count: {len(steps)}")
        if steps:
            print(f"  First step sample: {steps[0]}")
        print(f"  Road conditions count: {len(road_conditions)}")
        print(f"  Total distance: {total_distance_km} km")
        print(f"  Total duration: {total_duration_mins} mins")

        if not starting_point_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="starting_point_name is required"
            )

        try:
            # Try AI transformation with comprehensive data
            professional_text = transform_directions_to_professional(
                starting_point_name=starting_point_name,
                total_distance_km=total_distance_km,
                total_duration_mins=total_duration_mins,
                property_position=property_position,
                road_conditions=road_conditions,  # NEW: Simplified format
                road_segments=road_segments,  # OLD: Backward compatibility
                steps=steps  # Google Maps turn-by-turn steps
            )
        except Exception as ai_error:
            print(f"[WARN] AI transformation failed, using fallback: {ai_error}")
            # Extract navigation entities for enhanced fallback
            navigation_entities = extract_navigation_entities(steps) if steps else None

            # Fallback to enhanced text with navigation entities if available
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
        error_details = traceback.format_exc()
        print(f"[ERROR] Access transformation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transforming access directions: {str(e)}"
        )
# Locality Information Endpoints
@app.post("/api/locality/nearby-facilities")
async def get_nearby_facilities_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Fetch nearby facilities using Google Places API
    Request body: {
        latitude: float,
        longitude: float,
        radius_meters?: int (default 5000),
        facility_types?: string[] (optional, defaults to all)
    }
    """
    try:
        from .services.places_service import fetch_nearby_facilities, get_distance_to_major_town, find_nearest_transport

        latitude = request.get("latitude")
        longitude = request.get("longitude")
        radius_meters = request.get("radius_meters", 5000)
        facility_types = request.get("facility_types")

        if not latitude or not longitude:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and longitude are required"
            )

        # Fetch nearby facilities
        facilities = await fetch_nearby_facilities(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            facility_types=facility_types
        )

        # Get distance to major town
        major_town, distance = await get_distance_to_major_town(latitude, longitude)

        # Find nearest transport
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
        error_details = traceback.format_exc()
        print(f"[ERROR] Nearby facilities fetch failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching nearby facilities: {str(e)}"
        )


@app.post("/api/locality/generate-narrative")
async def generate_locality_narrative_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate professional locality description using AI
    Request body: All locality data fields (village, district, facilities, etc.)
    """
    try:
        from .services.locality_narrative import generate_locality_narrative

        # Extract all locality fields from request
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

        return {
            "status": "success",
            "narrative": narrative
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Locality narrative generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating locality narrative: {str(e)}"
        )


@app.post("/api/building/generate-description")
async def generate_building_description_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate professional building description using AI.
    Used during DOCX generation or when user manually requests it.
    """
    try:
        from .services.building_narrative import generate_building_narrative

        description = await generate_building_narrative(
            building_name=request.get("building_name", "Building"),
            building_type=request.get("building_type", "residential"),
            stories=request.get("stories", 1),
            floors=request.get("floors"),
            construction_materials=request.get("construction_materials"),
            utilities_services=request.get("utilities_services"),
            total_floor_area=request.get("total_floor_area"),
            age_description=request.get("age_description"),
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
        print(f"[API] Building description error: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Building description generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating building description: {str(e)}"
        )


@app.post("/api/land/generate-description")
async def generate_land_description_endpoint(
    request: dict,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate professional land description using AI.

    Takes land characteristic data and returns an AI-generated professional
    description with length proportional to the amount of data provided.
    """
    try:
        from .services.land_narrative import generate_land_narrative

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
        error_details = traceback.format_exc()
        print(f"[ERROR] Land description generation failed: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating land description: {str(e)}"
        )


# Legacy v0.0 endpoints removed for clean v0.1 implementation
# All functionality moved to authenticated user + report system
# Available endpoints: /api/auth/*, /api/reports/*, /api/profile, /api/autocomplete/*, /api/maps/*, /api/locality/*

