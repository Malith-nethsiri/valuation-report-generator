# BARE LAND REPORT: DATA COLLECTION & REPORT GENERATION FLOW

> **Internal Engineering Documentation** | Last Updated: 2026-02-07
> Covers the complete lifecycle from user opening the form to downloading the generated DOCX report.

---

## TABLE OF CONTENTS

1. [Folder Structure](#1-folder-structure)
2. [System Flow Table (16-Column)](#2-system-flow-table)
3. [Database Schema](#3-database-schema)
4. [Example Data: Before & After](#4-example-data-before--after)
5. [External Service Map](#5-external-service-map)
6. [Duplicates & Redundancy Audit](#6-duplicates--redundancy-audit)

---

## 1. FOLDER STRUCTURE

Files involved in this flow only (excludes vehicle, multi-property-only files):

```
project/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── BareLandForm.tsx                          # Entry point page (368 lines)
│   │   ├── components/
│   │   │   ├── MultiStepForm.tsx                         # 13-step form orchestrator (2,709 lines)
│   │   │   ├── DocumentUploadOCR.tsx                     # OCR document processing (462 lines)
│   │   │   ├── InteractivePropertyMap.tsx                # Google Maps interactive (1,326 lines)
│   │   │   ├── PropertyDescriptionStep.tsx               # Land description + photos (2,546 lines)
│   │   │   ├── PropertyLocationMap.tsx                   # Map display (713 lines)
│   │   │   ├── AccessDirectionsSection.tsx               # Access route builder (component)
│   │   │   ├── LocalityInformationSection.tsx            # Nearby facilities (832 lines)
│   │   │   ├── PropertyComparisonStep.tsx                # Comparable properties
│   │   │   ├── BoundaryInformationSection.tsx            # 8-direction boundaries (632 lines)
│   │   │   ├── LandValuesSection.tsx                     # Market comparisons (510 lines)
│   │   │   ├── LegalAspectsSection.tsx                   # Legal info (456 lines)
│   │   │   ├── ValuationSection.tsx                      # Value calculator (882 lines)
│   │   │   ├── InvoiceDataStep.tsx                       # Invoice builder
│   │   │   └── CertificationSection.tsx                  # Valuer certification
│   │   ├── schemas/
│   │   │   ├── validationSchemas.ts                      # Zod schemas (applicant, details)
│   │   │   └── multiStepFormSchemas.ts                   # Step-level schemas
│   │   ├── constants/
│   │   │   ├── multiStepFormConstants.ts                 # Step definitions, deed types
│   │   │   └── propertyDescriptionConstants.ts           # Land shapes, types, soils
│   │   ├── types/
│   │   │   ├── index.ts                                  # Shared types (Report, User, etc.)
│   │   │   ├── multiStepForm.ts                          # Form-specific types
│   │   │   └── propertyDescription.ts                    # Description types
│   │   ├── hooks/
│   │   │   ├── useDraftManager.ts                        # Auto-save hook
│   │   │   └── useAdministrativeDivisions.ts             # District/DS lookup hook
│   │   ├── services/
│   │   │   └── api.ts                                    # Axios API client + reportApi
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx                            # Auth state + token management
│   │   ├── utils/
│   │   │   └── fieldNameMapper.ts                        # snake_case -> Label mapper
│   │   └── tests/
│   │       ├── auth.test.tsx
│   │       ├── components/MultiStepForm.test.tsx
│   │       └── schemas/stepSchemas.test.ts
│   └── ...
├── backend/
│   ├── app/
│   │   ├── main.py                                       # FastAPI routes (all endpoints)
│   │   ├── models.py                                     # SQLAlchemy models (950 lines)
│   │   ├── schemas.py                                    # Pydantic schemas (2,142 lines)
│   │   ├── crud.py                                       # CRUD operations (1,346 lines)
│   │   ├── auth.py                                       # JWT auth, password hashing
│   │   ├── docx_generator.py                             # DOCX report builder
│   │   ├── maps_service.py                               # Google Maps integration
│   │   ├── middleware/
│   │   │   ├── csrf_protection.py                        # CSRF double-submit cookies
│   │   │   └── rate_limiting.py                          # Token bucket rate limiter
│   │   ├── services/
│   │   │   ├── base_narrative.py                         # Abstract narrative base class
│   │   │   ├── land_narrative.py                         # AI land description generator
│   │   │   ├── locality_narrative.py                     # AI locality narrative generator
│   │   │   ├── building_narrative.py                     # AI building narrative (NOT used for bare land)
│   │   │   ├── ocr_service.py                            # Google Vision OCR processor
│   │   │   ├── email_service.py                          # SendGrid email sender
│   │   │   ├── access_transformer.py                     # Access directions text transformer
│   │   │   ├── anthropic_client.py                       # Claude API client wrapper
│   │   │   ├── places_service.py                         # Google Places API wrapper
│   │   │   ├── file_storage.py                           # Generated file storage
│   │   │   ├── job_service.py                            # Async job queue
│   │   │   ├── cache_service.py                          # Redis cache wrapper
│   │   │   ├── redis_client.py                           # Redis connection
│   │   │   └── ai_valuation.py                           # AI-assisted valuation
│   │   └── utils/
│   │       └── json_validators.py                        # JSON field validators
│   ├── alembic/                                          # Database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                                   # Test fixtures
│       └── test_auth.py                                  # Auth tests
└── ...
```

---

## 2. SYSTEM FLOW TABLE

### Phase A: Authentication & Page Load

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 1 | User clicks "New Bare Land Report" or navigates to `/bare-land-form` | Click navigation link or type URL | `BareLandForm.tsx` at route `/bare-land-form` (new) or `/bare-land-form/:reportId` (edit) | None | React Router resolves route. `useParams()` extracts `reportId` if present. Sets `isEditMode = !!reportId`. | None (client-side routing) | N/A | N/A | N/A | N/A | N/A | N/A | Route guard: `AuthContext` checks `user` object exists. If `user === null && !isLoading`, redirect to `/login`. | User not authenticated -> redirect to `/login`. Token expired -> `AuthContext` auto-refreshes via refresh token cookie. | BareLandForm component mounts. `isEditMode` and `reportId` state set. |
| 2 | BareLandForm mounts with `reportId` in URL (edit mode only) | None (automatic) | `BareLandForm.tsx` loading spinner | None | Sets `isLoadingReport = true`, `isEditMode = true`. Calls `loadReportForEdit()`. | `GET /api/reports/{reportId}` via `reportApi.getReport(parseInt(reportId))` | `main.py` -> `crud.get_report()` | 1. Decode JWT from cookie/header. 2. Query `Report` by ID with `user_id` ownership check. 3. Eager-load associated properties if `is_multi_property`. 4. Return full report JSON. | N/A | `reports` (read) | All report columns | Response JSON mapped to `Report` TypeScript type. `property_photos` ensured to be array (default `[]`). Buildings data cleaned for type safety. | JWT validation. User can only load own reports (`report.user_id === current_user.id`). CSRF not needed (GET request). | Report not found -> 404 -> toast "Failed to load report", redirect to `/dashboard`. Wrong `report_type` (not `bare_land`) -> toast error, redirect. Network error -> toast error, redirect. | `existingReport` state populated. Form pre-fills with loaded data. `isLoadingReport = false`. |
| 3 | BareLandForm mounts (new mode, no reportId) | None (automatic) | `BareLandForm.tsx` renders `MultiStepForm` | None | `isEditMode = false`. No API call. Form initialized with empty `defaultValues`. `MultiStepForm` renders Step 1. | None | N/A | N/A | N/A | N/A | N/A | N/A | Auth check via `useAuth()` hook. | N/A | Empty MultiStepForm rendered at Step 1. |

### Phase B: Step 1 - Applicant & Purpose

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 4 | MultiStepForm renders Step 1 (index 0, originalId 9) | User fills applicant details | `MultiStepForm.tsx` -> Step 1 inline rendering. Step config: `{ id: 9, title: "Applicant & Purpose", icon: User, color: "from-emerald-500 to-green-600" }` | `applicant_title`: `<select>` (Mr./Mrs./Ms./Dr./Rev.) -- `applicant_full_name`: `<input type="text">` required -- `applicant_id_type`: `<select>` (NIC/Passport/Other) -- `applicant_id_number`: `<input type="text">` with real-time validation -- `applicant_address_line1`: `<input type="text">` -- `applicant_address_line2`: `<input type="text">` -- `applicant_district`: `<select>` from admin divisions -- `applicant_province`: `<select>` -- `applicant_country`: `<input type="text">` default "Sri Lanka" -- `applicant_contact_number`: `<input type="tel">` -- `has_additional_owner`: `<select>` (Yes/No) -- `additional_owner_names`: `<textarea>` (shown if has_additional_owner=Yes) -- `valuation_type`: `<select>` (Market Value, etc.) -- `valuation_purpose`: `<select>` from `PREDEFINED_VALUATION_PURPOSES` -- `property_type_valued`: `<select>` (immovable property, etc.) | React Hook Form `register()` binds all fields. `mode: 'onChange'` enables real-time validation. ID number validated with 500ms debounce via `useFieldValidation()`. Color-coded feedback: red=error, amber=warning, green=success. `watch('has_additional_owner')` controls conditional rendering of `additional_owner_names`. | None (local state only) | N/A | N/A | N/A | N/A | N/A | N/A | **Zod schema**: `applicantPurposeSchema`. NIC format: old format `^\d{9}[VvXx]$`, new format `^\d{12}$`. Passport: `^[A-Za-z0-9]{6,12}$`. `applicant_full_name`: required, min 1 char. `additional_owner_names`: required if `has_additional_owner === "yes"`. | Invalid ID format -> field-level error message shown inline (non-blocking, warning only). Missing required fields -> prevents "Next" if strict validation enabled. | Step 1 data stored in React Hook Form state. User can proceed to Step 2. |

### Phase C: Step 2 - Additional Details

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 5 | User clicks "Next" from Step 1 | Click "Save and Continue" or "Next" | `MultiStepForm.tsx` -> Step 2 (index 1, originalId 10). Step config: `{ id: 10, title: "Additional Details", icon: FileText, color: "from-purple-500 to-violet-600" }` | `submission_organization`: `<input type="text">` -- `submission_address`: `<textarea>` -- `submission_recipient_position`: `<input type="text">` -- `inspection_date`: `<DatePicker>` component (DD-MM-YYYY format) -- `report_reference`: `<input type="text">` optional -- `report_date`: `<DatePicker>` -- `has_special_note`: `<select>` (Yes/No) -- `special_note_text`: `<textarea>` (shown if has_special_note=Yes) | `step2AdditionalDetailsSchema` validates dates. DatePicker enforces DD-MM-YYYY format. `watch('has_special_note')` controls conditional rendering. Step navigation updates `currentStep` state and saves progress to localStorage (`bareLandFormStep`). | Draft auto-save triggered via `useDraftManager` if form is dirty (300ms debounce). Calls `reportApi.createReport()` for first save or `reportApi.updateReport()` for subsequent. | `main.py` -> `crud.create_report()` or `crud.update_report()` | Creates/updates Report row with `status='draft'`. All provided fields persisted. Missing fields stored as `null`. | N/A | `reports` (insert or update) | `submission_organization` String(200), `submission_address` Text, `inspection_date` String(50), `report_reference` String(100), `report_date` String(50), `has_special_note` String(10), `special_note_text` Text | Dates stored as DD-MM-YYYY strings (not SQL date). `has_special_note` stored as "yes"/"no" string. | `step2AdditionalDetailsSchema`: `inspection_date` must match `^\d{2}-\d{2}-\d{4}$`. Backend Pydantic also validates date format. JWT + CSRF token required for POST/PUT. | Date format mismatch -> Zod validation error. Auto-save network failure -> retry with exponential backoff (3 retries). | Step 2 data persisted. Draft report exists in DB. User proceeds to Step 3. |

### Phase D: Step 3 - Property & Plan (with OCR)

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 6 | User clicks "Next" from Step 2 | Click Next | `MultiStepForm.tsx` -> Step 3 (index 2, originalId 1). Step config: `{ id: 1, title: "Property & Plan", icon: Home, color: "from-blue-500 to-indigo-600" }`. Renders `DocumentUploadOCR` component + property identification fields. | **OCR Upload**: `<input type="file" multiple accept="image/jpeg,image/png,image/webp">` (3-5 deed pages + 1-2 plan pages, max 10MB each) -- **Identification Type**: Card-based selection (4 options): `plan` (blue), `deed` (green), `plan_and_deed` (purple), `certificate_of_sale` (orange) -- **Plan fields** (if plan/hybrid): `lot_number` `<input>`, `plan_number` `<input>` required, `plan_date` `<DatePicker>` required, `licensed_surveyor_name` `<input>` -- **Deed fields** (if deed/hybrid): `deed_type` `<select>` from `COMMON_DEED_TYPES` (14 types), `deed_number` `<input>` required, `deed_date` `<DatePicker>` required, `notary_name` `<input>`, `notary_location` `<input>` -- **Certificate fields** (if certificate): `certificate_number` `<input>`, `certificate_date` `<DatePicker>`, `certificate_notary_name` `<input>`, `certificate_notary_district` `<input>` | Card selection sets `property_identification_type` via `setValue()`. Conditional field groups rendered via `watch('property_identification_type')`. OCR extracted data auto-fills fields via `onDataExtracted` callback with `smartTitleCase()` transformation (preserves acronyms/initials). Confidence scoring: High >= 90%, Medium >= 70%, Low < 70%. | **OCR**: `POST /api/ocr/extract` with `FormData` (files + document_type). Called from `DocumentUploadOCR` component. | `main.py` -> `services/ocr_service.py` -> `process_multiple_documents()` | 1. Validate file count (max 10), size (max 10MB), type (JPEG/PNG/WEBP/PDF via magic number). 2. Send images to Google Cloud Vision API for text extraction. 3. Send OCR text to Claude AI for structured field parsing. 4. Return structured data with per-field confidence scores. | **Google Cloud Vision API** (OCR text extraction) + **Anthropic Claude API** (intelligent field parsing) | N/A (OCR is read-only) | N/A | OCR text -> Claude parses into: `plan_number`, `lot_number`, `lot_description`, `land_extent_acres/roods/perches`, `boundaries` JSON, `property_village`, `property_district`. All text fields get `smartTitleCase()` on frontend. | File upload: magic number verification prevents spoofing (e.g., renamed .exe to .jpg). Max 10MB per file. Rate limit: 10 req/min on `/api/ocr/extract`. JWT + CSRF required. | OCR API failure -> retry up to 2 times with 2s delay. Transient "server reloading" error -> auto-retry. Persistent failure -> toast error, user enters data manually. File too large -> 413 error. Invalid file type -> rejected before upload. | Property identification type selected. Plan/deed/certificate fields populated (from OCR or manual entry). Form state updated. |

### Phase E: Step 4 - Extent & Boundaries

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 7 | User clicks "Next" from Step 3 | Click Next | `MultiStepForm.tsx` -> Step 4 (index 3, originalId 2). Step config: `{ id: 2, title: "Extent & Boundaries", icon: Compass, color: "from-green-500 to-emerald-600" }`. Renders `LandExtentInput` + `BoundaryInformationSection`. | **Land Extent**: `land_extent_acres` `<input type="number">`, `land_extent_roods` `<input type="number">` (0-3), `land_extent_perches` `<input type="number">` (0-39.99) -- **Auto-calculated** (read-only display): `land_extent_hectares`, `land_extent_square_meters`, `land_extent_formatted` (e.g., "01A-02R-15.00P") -- **Boundaries** (8 directions, each has): `boundaries.north.description` `<input>`, `boundaries.north.length` `<input>`, `boundaries.north.adjoins` `<input>`, `boundaries.north.notes` `<input>` (repeat for: north, north_east, east, south_east, south, south_west, west, north_west) -- `physical_boundaries_types` `<multi-select>` (wall, fence, hedge, etc.) -- `physical_boundaries_description` `<textarea>` -- `land_traditional_name` `<input>` (Sinhala/Tamil name) | **Extent conversion**: 1 acre = 4 roods = 160 perches = 4,046.86 m^2 = 0.4047 hectares. Auto-calc runs on any extent field change: `hectares = (acres + roods/4 + perches/160) * 0.4047`, `sqm = hectares * 10000`, `formatted = "${acres}A-${roods}R-${perches}P"`. Boundary data stored as nested JSON object. | None (local state only, persisted on draft save) | N/A | N/A | N/A | N/A | N/A | On change: raw inputs (acres, roods, perches) -> derived fields (hectares, sqm, formatted). Boundary data: flat inputs -> nested `boundaries` JSON object `{ north: { description, length, adjoins, notes }, ... }`. | `extentBoundariesSchema` validates: `land_extent_perches` range 0-39.99, `land_extent_roods` range 0-3, `land_extent_acres` >= 0. At least one extent field required. Boundary descriptions optional but recommended. | Invalid extent values -> inline error (e.g., perches > 39.99). Missing all extent fields -> validation warning on submit. | Extent and boundary data stored in form state. Derived fields auto-calculated. |

### Phase F: Step 5 - Property Search (Interactive Map)

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 8 | User clicks "Next" from Step 4 | Click Next | `MultiStepForm.tsx` -> Step 5 (index 4, originalId 3). Step config: `{ id: 3, title: "Property Search", icon: MapPin, color: "from-orange-500 to-red-600" }`. Renders `InteractivePropertyMap` component (1,326 lines). | **Map interactions** (click-based): Click map to set property location -> sets `property_latitude`, `property_longitude`. Click map to set starting point -> sets `access_starting_point_latitude`, `access_starting_point_longitude`. -- `access_starting_point_name` `<input>` with Google Places autocomplete -- **Road conditions** array: each entry has `road_type` `<select>` (paved_road, concrete_road, carpet_road, gravel_road, sand_road, earth_road), `condition` `<select>` (excellent, good, fair, poor), `distance_km` `<input type="number">`, `notes` `<input>` -- `property_road_position` `<select>` (left side, right side) | Map click -> reverse geocode to get village/district/province via Google Geocoding API. Starting point set via Places Autocomplete (restricted to Sri Lanka `country:lk`). Route generated between start and property via Directions API. Polyline decoded for map display. Nearby facilities pre-fetched within configurable radius (2km/5km/10km). Direction calculated (N/NE/E/SE/S/SW/W/NW) from bearing. | **Multiple API calls**: 1. `POST /api/maps/geocode` (reverse geocode property click) 2. `POST /api/maps/places/autocomplete` (starting point search) 3. `POST /api/maps/places/details` (get coords from place_id) 4. `POST /api/maps/directions` (route calculation) 5. `POST /api/maps/static-map` (static map image URL) 6. `POST /api/maps/transform-access` (professional directions text) 7. `POST /api/locality/nearby-facilities` (facility detection) | `main.py` -> `maps_service.py` for 1-5. `services/access_transformer.py` for 6. `services/places_service.py` for 7. | **Geocode**: Google Geocoding API -> extract `lat`, `lng`, `district` (admin_area_level_2), `province` (admin_area_level_1), `village` (locality). **Directions**: Google Directions API -> extract `distance_km`, `duration_minutes`, `polyline`, `steps[]`. **Transform**: Takes Google steps + road conditions -> Claude AI generates professional narrative (3-5 key turns, landmarks, distance/duration). **Facilities**: Google Places API -> search within radius for hospitals, schools, banks, police, post offices, religious places, bus/train stations. | **Google Maps Platform**: Geocoding API, Directions API, Static Maps API, Places API (Autocomplete + Details + Nearby Search). **Anthropic Claude**: Access directions text transformation. | N/A (read-only lookups) | N/A | Google Geocoding response -> extract `address_components` by type. Directions `steps[]` -> filtered to 3-5 major turns. Compass bearing calculated: `atan2(sin(dLon)*cos(lat2), cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dLon))` -> 8-point direction. Road conditions: frontend `RoadCondition[]` format -> backend stores as JSON array. | Rate limit: 60 req/min on all `/api/maps/*` endpoints. JWT required. CSRF required for POST. Google API key validated server-side (never exposed to client). | Google API quota exceeded -> 429 error. API key invalid -> 403. Network timeout -> toast error. Map not loading -> fallback text entry. Transform API failure -> fallback local text generation. | `property_latitude`, `property_longitude`, `property_village`, `property_district`, `property_province` auto-filled. Route data: `access_directions_text`, `access_distance_km`, `access_duration_minutes`, `access_road_conditions`, `location_map_image_data`. Nearby facilities pre-loaded for Step 7. |

### Phase G: Step 6 - Property Details

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 9 | User clicks "Next" from Step 5 | Click Next | `MultiStepForm.tsx` -> Step 6 (index 5, originalId 4). Step config: `{ id: 4, title: "Property Details", icon: Building, color: "from-cyan-500 to-blue-600" }`. Renders `PropertyLocationSection` with autocomplete dropdowns. | `property_village` `<input type="text">` (pre-filled from map) -- `property_district` `<select>` from `useAdministrativeDivisions()` hook -- `property_province` `<select>` (auto-set from district) -- `grama_niladari_division` `<input>` with autocomplete (GN division lookup from selected district) -- `property_divisional_secretariat` `<select>` from `useDSDivisions(district)` (DS divisions filtered by district) -- `korale` `<input>` (traditional admin division) -- `pradeshiya_sabha` `<input>` (local authority) -- `ward_number` `<input>` -- `is_municipal_limit` `<checkbox>` -- `assessment_number` `<input>` -- `property_latitude` `<input type="number" readonly>` (from map) -- `property_longitude` `<input type="number" readonly>` (from map) | Pre-filled values from Step 5 map interaction displayed. `useAdministrativeDivisions()` fetches all Sri Lankan districts + DS divisions on mount. `useDSDivisions(district)` filters DS divisions when district changes. Province auto-selected based on district mapping. Case-insensitive autocomplete matching. | `GET /api/administrative-divisions` (all districts) -- `GET /api/administrative-divisions/{district}` (DS divisions for selected district) | `main.py` -> returns static JSON data | Returns pre-loaded administrative division data. Structure: `{ [district]: [{ name: "DS Division Name", gn_count: 42 }] }`. | N/A | N/A | N/A | District -> Province mapping applied automatically. GN division autocomplete filtered by selected DS division. | Latitude: Decimal(10,8) range -90 to 90. Longitude: Decimal(11,8) range -180 to 180. District must exist in administrative data. DS division must belong to selected district. | Admin divisions API failure -> cached data used. Invalid coordinates -> manual entry allowed. | Property location details confirmed and stored in form state. Administrative hierarchy complete. |

### Phase H: Step 7 - Locality Information

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 10 | User clicks "Next" from Step 6 | Click Next | `MultiStepForm.tsx` -> Step 7 (index 6, originalId 5). Step config: `{ id: 5, title: "Locality Information", icon: MapPin, color: "from-pink-500 to-rose-600" }`. Renders `LocalityInformationSection` component (832 lines). | **Infrastructure**: `has_electricity` `<checkbox>`, `water_supply_type` `<multi-select>` (Pipe-borne NWSDB, Well, Bore/Tube Well, Rainwater Harvesting, Spring/Stream), `telecommunication_types` `<multi-select>`, `internet_types` `<multi-select>` -- **Transport**: `has_public_transport` `<checkbox>`, `public_transport_routes` `<input>`, `nearest_bus_stop_name` `<input>`, `nearest_bus_stop_distance_km` `<input type="number">`, `nearest_railway_station` `<input>`, `nearest_railway_distance_km` `<input type="number">` -- **Facilities**: `nearby_facilities` array (auto-fetched from Step 5 or manually added). Each: `type` (hospital, school, bank, etc.), `name`, `distance_km`, `selected` checkbox -- `distance_to_major_town_km` `<input type="number">`, `major_town_name` `<input>` -- **Area**: `area_type` `<select>` (residential, commercial, agricultural, mixed, industrial), `development_level` `<select>` (well_developed, developing, underdeveloped), `predominant_building_type` `<multi-select>`, `is_tourist_area` `<checkbox>`, `tourist_attractions_nearby` `<textarea>` -- **Narrative**: `locality_description_text` `<textarea>` (auto-generated or manual) | Facilities pre-loaded from Step 5 map search. User can toggle `selected` checkbox per facility for report inclusion. Radius selector (2km/5km/10km) triggers re-fetch. "Generate Narrative" button calls AI endpoint. Generated narrative is editable. | **Facility fetch**: `POST /api/locality/nearby-facilities` (if not pre-loaded). **Narrative generation**: `POST /api/locality/generate-narrative` with all locality data. | `main.py` -> `services/places_service.py` (facilities) -> `services/locality_narrative.py` (narrative) | **Facilities**: Google Places Nearby Search for each category type within radius. Returns `[{ type, name, distance_km, latitude, longitude }]`. **Narrative**: `LocalityNarrativeService.generate()` extends `BaseNarrativeService`. Builds prompt with all locality data. Calls Claude API with adaptive length: minimal data (1-3 fields) = 30-50 words, moderate (4-6) = 60-90 words, rich (7+) = 100-140 words. | **Google Places API** (Nearby Search). **Anthropic Claude API** (narrative generation). | N/A | `nearby_facilities`: JSON array. `water_supply_type`, `telecommunication_types`, `internet_types`: JSON arrays. `locality_description_text`: Text. | Facilities array filtered to `selected: true` items only for report. Multi-select values stored as string arrays. Distance values in km (decimal). | Rate limit: 20 req/min on `/api/locality/generate-narrative`. JWT + CSRF required. | Places API quota -> graceful degradation (manual facility entry). Claude API failure -> toast error, user writes narrative manually. Empty facility list -> narrative still generates from infrastructure data. | Locality information complete: infrastructure, transport, facilities, area characteristics, and professional narrative text. |

### Phase I: Step 8 - Property Description (Land Only)

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 11 | User clicks "Next" from Step 7 | Click Next | `MultiStepForm.tsx` -> Step 8 (index 7, originalId 6). Step config: `{ id: 6, title: "Property Description", icon: ClipboardList, color: "from-amber-500 to-orange-600" }`. Renders `PropertyDescriptionStep` with `isBareLand={true}` -> buildings tab hidden, only "Land" tab active. | **Land characteristics**: `land_shape` `<select>` (rectangular, square, irregular, triangular, L-shaped - from `LAND_SHAPES` constant), `land_type` `<select>` (high_land, low_land, flat_land, paddy_land, marshy_land - from `LAND_TYPES`), `land_level` `<select>` (at_road_level, above_road_level, below_road_level - from `LAND_LEVELS`), `soil_type` `<select>` (laterite, sandy, clay, loam, gravel, rocky - from `SOIL_TYPES`), `flood_risk` `<select>` (not_subject, occasionally_floods, frequently_floods), `land_condition` `<select>` (developed, bare_land, scrub_jungle, cultivated), `land_frontage_type` `<select>`, `land_frontage_width` `<input type="number">` meters, `land_frontage_description` `<textarea>`, `water_table_depth` `<input type="number">` feet -- **Topography**: `elevation_changes` `<select>` (relatively_flat, gentle_slope, steep_slope, undulating), `drainage_pattern` `<select>` (well_drained, moderate, poor_drainage, waterlogged), `vegetation_type` `<select>` (bare, grass_coverage, scrub_vegetation, mature_trees, dense_jungle), `natural_features` `<textarea>` -- **Narrative**: `land_description_text` `<textarea>` (auto-generated or manual) -- **Photos**: `property_photos` multi-file upload (JPEG/PNG/WEBP, max 10MB each) with captions, ordering, delete | `isBareLand` flag hides buildings tab and all building-related fields. Only land characteristics + property photos shown. "Generate Description" button calls AI endpoint. Photo upload creates preview thumbnails. Drag-drop photo reordering supported. | **Narrative generation**: `POST /api/land/generate-description` with all land characteristic data. | `main.py` -> `services/land_narrative.py` -> `LandNarrativeService.generate()` | `LandNarrativeService` extends `BaseNarrativeService`. Builds prompt with: `format_land_value()` function maps enum values to readable labels (e.g., `high_land` -> "High Land", `laterite` -> "Laterite Soil"). Adaptive length: 30-140 words proportional to data richness. Mandates ALL provided fields must appear in narrative. Professional Sri Lankan valuation style enforced in prompt. | **Anthropic Claude API** (land narrative generation) | N/A | `land_shape`, `land_type`, `land_level`, `soil_type`, `flood_risk`, `land_condition`: all String(50). `land_frontage_width`, `water_table_depth`: Numeric. `land_description_text`: Text. `property_photos`: JSON array `[{ url, caption, order }]`. `elevation_changes`, `drainage_pattern`, `vegetation_type`: String(50). `natural_features`: Text. | Enum values (snake_case) -> readable labels via `format_land_value()` mapping dict (85 entries in `land_narrative.py` lines 10-87). Photos encoded as base64 or uploaded to file storage -> URL references stored. | Rate limit: 20 req/min on `/api/land/generate-description`. `propertyDescriptionSchema` validates field types. Photo size/type validation client-side + server-side magic number check. | Claude API failure -> toast error, manual narrative entry. Photo upload failure -> retry, user can skip photos. Invalid photo format -> rejected before upload. | Land description complete with characteristics, topography, narrative text, and property photos. |

### Phase J: Step 9 - Legal Aspects

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 12 | User clicks "Next" from Step 8 | Click Next | `MultiStepForm.tsx` -> Step 9 (index 8, originalId 7). Step config: `{ id: 7, title: "Legal Aspects", icon: Gavel, color: "from-purple-500 to-violet-600" }`. Renders `LegalAspectsSection`. | `ownership_type` `<select>` (freehold, leasehold, state_grant, etc.) -- `title_search_conducted` `<select>` (Yes/No) -- `pedigree_search_conducted` `<select>` (Yes/No) -- `valuation_basis_note` `<textarea>` (custom basis statement) -- `property_encumbered` `<select>` (Yes/No) -- `encumbrance_type` `<select>` (Mortgage, Life Interest, Fidei Commissum, etc.) shown if encumbered=Yes -- `encumbrance_details` `<textarea>` shown if encumbered=Yes -- `street_lines_status` `<select>` (BARE LAND: may skip or show as N/A) -- `local_authority_rated` `<select>` (Yes/No) -- `local_authority_tax_levy` `<input>` -- `assessment_number` `<input>` -- `rent_act_effectiveness` `<select>` | Conditional rendering: `encumbrance_type` and `encumbrance_details` shown only when `property_encumbered === "yes"`. For bare land: street lines and building limits sections may be hidden or marked N/A since there are no buildings. All fields optional for draft save, but completeness shown in data quality warnings. | None (local state only) | N/A | N/A | N/A | N/A | `ownership_type`, `title_search_conducted`, `pedigree_search_conducted`: String(50). `valuation_basis_note`: Text. `property_encumbered`: String(10). `encumbrance_type`: String(100). `encumbrance_details`: Text. `local_authority_rated`: String(10). | `property_encumbered` "yes"/"no" string. `encumbrance_type` enum value stored as-is. | None beyond field type validation. | N/A (all fields optional at this stage). | Legal aspects data stored in form state. |

### Phase K: Step 10 - Land Values (Comparable Properties)

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 13 | User clicks "Next" from Step 9 | Click Next | `MultiStepForm.tsx` -> Step 10 (index 9, originalId 8). Step config: `{ id: 8, title: "Land Values", icon: TrendingUp, color: "from-green-500 to-teal-600" }`. Renders `LandValuesSection` component (510 lines). | **Comparable Properties** (dynamic array, add/remove): Each entry: `property_type` `<select>` (Commercial, Residential, Agricultural), `location_description` `<textarea>`, `extent` `<input type="number">` (perches), `rate_per_perch` `<input type="number">` (LKR), `total_value` `<input type="number" readonly>` (auto-calc: extent * rate_per_perch) -- "Add Comparable" button adds new entry. Delete icon removes entry. -- `land_market_analysis` `<textarea>` (free-text market analysis or AI-generated) | Each comparable property gets a unique `id` (UUID). `total_value` auto-calculated on extent or rate change. Market analysis can be manually entered or AI-generated. Comparable data maintained as array in form state. | None (local state) | N/A | N/A | N/A | N/A | `comparable_properties`: JSON array `[{ property_type: string, location_description: string, extent: number, rate_per_perch: number, total_value: number }]`. `land_market_analysis`: Text. | Frontend format: `{ id, property_type, location_description, extent, rate_per_perch, total_value }`. Backend format: `{ property_address, property_type, land_extent_acres, price_per_perch, sale_price }`. Transformation happens in `handleFormSubmit()` before API call. | Numeric fields validated as positive numbers. At least 0 comparables allowed (recommended 3+). | Empty comparable list -> data quality warning (non-blocking). Rate or extent negative -> inline error. | Comparable properties array and market analysis stored in form state. |

### Phase L: Step 11 - Valuation

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 14 | User clicks "Next" from Step 10 | Click Next | `MultiStepForm.tsx` -> Step 11 (index 10, originalId 11). Step config: `{ id: 11, title: "Valuation", icon: Scale, color: "from-indigo-500 to-blue-600" }`. Renders `ValuationSection` component (882 lines). | **Land Valuation**: `valuation_land_extent` `<input type="number">` (perches, pre-filled from Step 4), `valuation_rate_per_perch` `<input type="number">` (LKR), `valuation_total_land_value` `<input type="number">` (auto-calc or manual override) -- **Addons** (dynamic array): Each: `description` `<input>` (e.g., "Mature Trees", "Bore Well", "Retaining Wall"), `value` `<input type="number">` (LKR). `valuation_total_addons_value` auto-summed. -- **Summary**: `valuation_market_value` `<input type="number">` (auto-calc: land + addons, or manual override), `valuation_forced_sale_percentage` `<input type="number">` (default 75%), `valuation_forced_sale_value` `<input type="number">` (auto-calc: market * percentage), `valuation_insurance_value` `<input type="number">` -- **Override tracking**: `valuation_manual_overrides` object tracks which auto-calc fields were manually edited. | Auto-calculations: `total_land_value = extent * rate_per_perch`. `total_addons_value = sum(addon.value)`. `market_value = total_land_value + total_addons_value`. `forced_sale_value = market_value * (forced_sale_percentage / 100)`. Manual override sets `valuation_manual_overrides[fieldName] = true` to prevent auto-recalculation. For bare land: `valuation_buildings_data = null`, `valuation_total_buildings_value = null` (no buildings). | None (local state with calculations) | N/A | N/A | N/A | N/A | `valuation_land_extent`: Numeric. `valuation_rate_per_perch`, `valuation_total_land_value`: Numeric (LKR). `valuation_addons`: JSON array `[{ description, value }]`. `valuation_total_addons_value`: Numeric. `valuation_market_value`, `valuation_forced_sale_value`, `valuation_insurance_value`: Numeric. `valuation_forced_sale_percentage`: Numeric (0-100). `valuation_manual_overrides`: JSON object `{ field_name: boolean }`. | Currency values in LKR (Sri Lankan Rupees). All numeric. `valuation_manual_overrides` tracks user edits vs auto-calc. Bare land: building-related valuation fields explicitly set to `null`. | All valuation amounts must be >= 0. `forced_sale_percentage` must be 0-100. Market value must be > 0 for completed reports (warning only for drafts). | Auto-calc conflict if user edits derived field then changes source -> override flag prevents unexpected changes. | Valuation complete: land value, addons, market value, forced sale value, insurance value. |

### Phase M: Step 12 - Invoice

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 15 | User clicks "Next" from Step 11 | Click Next | `MultiStepForm.tsx` -> Step 12 (index 11, originalId 12). Step config: `{ id: 12, title: "Invoice", icon: Receipt, color: "from-amber-500 to-orange-600" }`. Renders `InvoiceDataStep` component. | **Invoice Items** (dynamic array): Each: `description` `<input>` (e.g., "Professional Fees", "Report Preparation"), `total` `<input type="number">` (LKR). -- `subtotal` auto-summed. -- `traveling_charges` `<input type="number">` (LKR, optional). -- `discount` `<input type="number">` (LKR, optional). -- `total` auto-calc: `subtotal + traveling_charges - discount`. -- **Bank Details**: `bank_account_ids` from user profile bank accounts `<select>`. `manual_bank_details` `<textarea>` (fallback if no saved accounts). | Invoice items managed as dynamic array. Subtotal auto-summed on item change. Total auto-calculated. Bank accounts loaded from user profile (`user.bank_accounts` JSON array). | None (local state) | N/A | N/A | N/A | N/A | `invoice_data`: JSON object `{ items: [{ description, total }], subtotal: number, traveling_charges: number, discount: number, total: number, bank_account_ids: string[], manual_bank_details: string }`. | Currency values in LKR. Bank account selection uses pre-saved account IDs from user profile. | Invoice total must be >= 0. | Empty invoice -> warning only (non-blocking). | Invoice data stored in form state. |

### Phase N: Step 13 - Certification

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 16 | User clicks "Next" from Step 12 | Click Next | `MultiStepForm.tsx` -> Step 13 (index 12, originalId 13). Step config: `{ id: 13, title: "Certification", icon: Award, color: "from-amber-500 to-yellow-600" }`. Renders `CertificationSection` component. "Generate Report" button appears on this final step. | `certification_text` `<textarea>` (pre-filled with standard certification template) -- `certificate_identity_confirmed` `<input type="checkbox">` (must be checked to submit) -- `certification_valuer_name` `<input>` (auto-filled from `user.full_name`) -- `certification_valuer_designation` `<input>` (auto-filled from `user.professional_designation`) -- `certification_date` `<DatePicker>` (DD-MM-YYYY) | Standard certification text pre-populated. Valuer name and designation pulled from AuthContext user profile. Identity confirmation checkbox must be checked for final submission. Data quality warnings panel shown (non-blocking list of incomplete/missing optional fields across all steps). | None (local state) | N/A | N/A | N/A | N/A | `certification_text`: Text. `certificate_identity_confirmed`: Boolean. `certification_valuer_name`, `certification_valuer_designation`: String(200). `certification_date`: String(50). | Date stored as DD-MM-YYYY string. Boolean stored as true/false. | `certificate_identity_confirmed` must be `true` for final submission. All required fields across all 13 steps validated before submission allowed. | Unchecked identity confirmation -> cannot submit. Validation errors in any step -> error summary panel shown with clickable links to jump to error locations. | Certification complete. "Generate Report" button enabled. |

### Phase O: Form Submission & Report Creation

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 17 | User clicks "Generate Report" on Step 13 | Click "Generate Report" button | `MultiStepForm.tsx` -> calls parent `onSubmit(data)` -> `BareLandForm.handleFormSubmit(data)` | All form data from Steps 1-13 aggregated by React Hook Form | **Pre-submission data cleaning** (BareLandForm lines 82-123): 1. Ensure `property_photos` is always `[]` (never null). 2. Convert `utilities_services` string values to arrays (water_supply, electricity_supply, telephone_connection). 3. Remove root-level deed fields (`deed_type`, `deed_number`, `deed_date`, `notary_name`, `notary_location`) from `fieldsToRemove` list. 4. **Bare land specific**: Set `buildings: null`, `occupier_name: null`, `occupier_relationship: null`, `valuation_buildings_data: null`, `valuation_total_buildings_value: null`. 5. Set `report_type: "bare_land"`. 6. Set `status: "completed"`. 7. Clear localStorage: `bareLandFormDraft`, `bareLandFormStep`. | **New report**: `POST /api/reports` via `reportApi.createReport(reportData)`. **Edit mode**: `PUT /api/reports/{reportId}` via `reportApi.updateReport(reportId, reportData)`. | `main.py` -> `crud.create_report()` or `crud.update_report()` | **Create**: 1. Validate JWT. 2. Parse request body via `ReportCreate` Pydantic schema (200+ optional fields). 3. Create `Report` SQLAlchemy model instance with `user_id` from JWT. 4. `db.add()`, `db.commit()`, `db.refresh()`. 5. Return created report with ID. **Update**: 1. Validate JWT. 2. `SELECT FOR UPDATE` on report row (pessimistic locking). 3. Verify `report.user_id === current_user.id`. 4. Apply field updates from `ReportUpdate` schema. 5. `db.commit()`, `db.refresh()`. 6. Return updated report. | N/A | `reports` (insert or update) | All columns listed in Database Schema section below. Key fields: `report_type='bare_land'`, `status='completed'`, `user_id` from JWT, `created_at`/`updated_at` timestamps. | **Frontend -> Backend**: Comparable properties transformed from `{ extent, rate_per_perch }` to `{ land_extent_acres, price_per_perch }`. Deed data from root-level fields to `deeds` JSON array. Building fields explicitly nulled. Date strings kept as DD-MM-YYYY. Numeric values as-is. JSON arrays (facilities, boundaries, photos, addons) serialized. | **JWT validation**: Access token from cookie or Authorization header. **CSRF**: X-CSRF-Token header must match csrf_token cookie (compare_digest). **Pydantic**: `ReportCreate`/`ReportUpdate` schema validation with `extra='forbid'` on sensitive schemas. **Rate limit**: 30 req/min on `/api/reports`. **Ownership**: Update only allowed if `report.user_id === jwt.user_id`. **Concurrency**: `SELECT FOR UPDATE` prevents lost updates. | 401 Unauthorized -> session expired, redirect to login. 403 Forbidden -> CSRF token mismatch, prompt re-login. 429 Too Many Requests -> rate limit, retry after header. 422 Validation Error -> Pydantic schema rejection. 500 Server Error -> retry with exponential backoff (3 retries). Network failure -> toast error, data preserved in form state for retry. | Report persisted in database with `status='completed'`. `reportCreated` state set with report data including `report.id`. Success screen displayed. |

### Phase P: DOCX Generation & Download

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 18 | Success screen displayed after report creation | User sees success screen with "Download Report (DOCX)" button | `BareLandForm.tsx` -> success screen rendering. Shows: report reference, creation date, report type badge, download button, "Create Another Report" link. | None (display only) | `setReportCreated(response)` shows success UI. `isGeneratingDocx = false` initially. | None | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Success screen visible with report details and download option. |
| 19 | User clicks "Download Report (DOCX)" | Click download button | `BareLandForm.tsx` -> `handleDownloadReport()` function | None | Sets `isGeneratingDocx = true`. Shows loading spinner on button. | **Sync**: `POST /api/reports/{reportId}/generate` via `reportApi.generateReportDocx(reportId)`. Returns binary DOCX file. **Async alternative**: `POST /api/reports/{reportId}/generate-async` returns `{ job_id }`, then poll `GET /api/jobs/{job_id}` until `status='completed'`, then `GET /api/jobs/{job_id}/download`. | `main.py` -> `docx_generator.py` -> `generate_user_data_docx(report, user)` | **DOCX Generation Pipeline**: 1. Load Report with eager loading (all relationships). 2. Load User profile (valuer credentials, bank accounts). 3. Create python-docx Document from template. 4. **Build sections in order**: a. Letterhead (from `user.preferred_letterhead_template`). b. Title block: "VALUATION REPORT of The Property Depicted as [lot] in [plan]". c. Applicant statement: "At the request of [applicant_full_name]...". d. **Section 1.0**: Inspection & Situation (date, location, admin divisions). e. **Section 2.0**: Description of Property - LAND ONLY (extent in A-R-P, boundaries, shape, type, level, soil, water table, flood risk, topography, condition, narrative). f. **Section 3.0**: Photographs (property_photos, location maps). g. **Section 4.0**: Situation/Locality (distance to town, facilities, infrastructure, narrative). h. **Section 5.0**: Legal Aspects - BARE LAND SIMPLIFIED (ownership, title search, encumbrances; SKIP street lines, building limits). i. **Section 6.0**: Valuation - LAND ONLY (extent * rate = land value; NO buildings; addons if any; market value summary). j. **Section 7.0**: Certification (standard text, valuer name, designation, date). k. Invoice section (items, totals, bank details). 5. Apply formatting (fonts, margins, tables, headers). 6. Return BytesIO stream. | **Pillow** (image processing for photos in DOCX). File storage service for caching generated files. | `reports` (read), `users` (read), `jobs` (insert/update for async) | Report: all columns read. User: `full_name`, `professional_designation`, `academic_qualifications`, `bank_accounts`, `preferred_letterhead_template`, address fields. Job: `id`, `status`, `result_url`, `progress_percent`. | Report data -> formatted DOCX sections. Dates: DD-MM-YYYY displayed as-is. Currency: formatted with thousand separators (e.g., "Rs. 1,500,000.00"). Extent: "01A-02R-15.00P" format. Boundaries: direction labels (North, South, etc.) with descriptions. Photos: resized/letterboxed for uniform dimensions in document. Enum values: snake_case -> readable labels (e.g., "high_land" -> "High Land"). | JWT required. Report ownership verified. Rate limit: 5 req/min on `/api/submit-and-generate`. DOCX generation runs in thread pool (doesn't block event loop). | DOCX generation failure -> 500 error, toast "Failed to generate report". Image processing failure -> DOCX generated without images, warning logged. Template not found -> fallback to default template. Async job failure -> job.status='failed', job.error_message set, user notified. Memory exhaustion (large photos) -> handled by Pillow resize. | DOCX file downloaded to user's device. `isGeneratingDocx = false`. File named: `report_{reference}_{date}.docx` or `valuation_report_{id}.docx`. |

### Phase Q: Ongoing Background Operations

| # | Trigger | User Action | Frontend View / Component / Route | Frontend Inputs | Frontend Processing | API / Function Called | Backend File / Module | Backend Logic | External Services | DB Tables Touched | DB Fields / Schema | Data Transformations | Security / Validation / Permissions | Failure Modes | Success Output |
|---|---------|-------------|-----------------------------------|-----------------|---------------------|----------------------|----------------------|---------------|-------------------|-------------------|--------------------|---------------------|-------------------------------------|---------------|----------------|
| 20 | Form field changes during Steps 1-13 (continuous) | Any field edit | `MultiStepForm.tsx` via `useDraftManager` hook | Any field | `useDraftManager` detects `isDirty` state. Debounces saves (300ms minimum between saves). Duplicate prevention via ref-based flags. On save: creates/updates report with `status='draft'`. Stores current step in localStorage (`bareLandFormStep`). Form data cached in localStorage (`bareLandFormDraft`). | `POST /api/reports` (first save) or `PUT /api/reports/{draftId}` (subsequent saves) | `main.py` -> `crud.create_report()` or `crud.update_report()` | Same as Step 17 but with `status='draft'`. Partial data accepted (all fields optional in draft). | N/A | `reports` (insert/update) | `status='draft'`, partial field data | N/A | Same JWT + CSRF as Step 17 | Network failure -> retry with exponential backoff (3 retries, 2^n * 1000ms delay). All retries fail -> data preserved in localStorage for recovery. | Draft saved. `lastSaved` timestamp updated in UI. |
| 21 | Browser window close/navigate away (continuous) | Close tab or navigate away | `MultiStepForm.tsx` `beforeunload` event handler | None | Detects `isDirty` flag. If unsaved changes: sends keepalive beacon request to save draft. Shows browser's native "unsaved changes" confirmation dialog. | `PUT /api/reports/{draftId}` via `navigator.sendBeacon()` or `fetch({ keepalive: true })` | `main.py` -> `crud.update_report()` | Same draft update logic. Keepalive ensures request completes even after tab closes. | N/A | `reports` (update) | Same as Step 20 | N/A | Keepalive requests bypass some CSRF checks (browser limitation). | Beacon fails silently -> data in localStorage as fallback. Browser kills request before completion -> localStorage recovery on next visit. | Draft saved before unload. |
| 22 | Keyboard shortcut (continuous) | `Ctrl+S` / `Cmd+S` | `MultiStepForm.tsx` keydown event handler | None | Prevents default browser save dialog. Triggers same save logic as "Save and Continue" button. | Same as Step 20 | Same as Step 20 | Same as Step 20 | N/A | Same as Step 20 | Same as Step 20 | N/A | Same as Step 20 | Same as Step 20 | Draft saved. Toast notification confirms save. |

---

## 3. DATABASE SCHEMA

### 3.1 Report Table (Primary)

```sql
CREATE TABLE reports (
    -- Primary Key
    id                              SERIAL PRIMARY KEY,
    user_id                         INTEGER NOT NULL REFERENCES users(id),

    -- Report Metadata
    report_type                     VARCHAR(50) DEFAULT 'bare_land',  -- 'bare_land', 'residential_property', 'multi_property', 'vehicle_report'
    status                          VARCHAR(20) DEFAULT 'draft',      -- 'draft', 'completed'
    report_reference                VARCHAR(100),
    inspection_date                 VARCHAR(50),                       -- DD-MM-YYYY
    report_date                     VARCHAR(50),
    has_special_note                VARCHAR(10),                       -- 'yes' / 'no'
    special_note_text               TEXT,

    -- Applicant Information
    applicant_title                 VARCHAR(20),
    applicant_full_name             VARCHAR(200),
    applicant_id_type               VARCHAR(50),                       -- 'NIC', 'Passport', 'Other'
    applicant_id_number             VARCHAR(100),
    applicant_address_line1         VARCHAR(300),
    applicant_address_line2         VARCHAR(300),
    applicant_district              VARCHAR(100),
    applicant_province              VARCHAR(100),
    applicant_country               VARCHAR(100) DEFAULT 'Sri Lanka',
    applicant_contact_number        VARCHAR(50),
    has_additional_owner            VARCHAR(10),
    additional_owner_names          TEXT,

    -- Valuation Purpose
    valuation_type                  VARCHAR(100),
    valuation_purpose               TEXT,
    property_type_valued            VARCHAR(200),

    -- Submission Details
    submission_organization         VARCHAR(200),
    submission_address              TEXT,
    submission_recipient_position   VARCHAR(200),

    -- Property Identification
    property_identification_type    VARCHAR(50),                       -- 'plan', 'deed', 'plan_and_deed', 'certificate_of_sale'
    lot_number                      VARCHAR(100),
    plan_number                     VARCHAR(100),
    plan_date                       VARCHAR(50),
    licensed_surveyor_name          VARCHAR(200),
    deeds                           JSON,                              -- [{deed_type, deed_number, deed_date, notary_name, notary_location}]
    property_identification_documents JSON,

    -- Land Extent
    land_extent_acres               NUMERIC(10,4),
    land_extent_roods               NUMERIC(10,4),
    land_extent_perches             NUMERIC(10,4),
    land_extent_hectares            NUMERIC(10,6),                     -- Auto-calculated
    land_extent_square_meters       NUMERIC(12,4),                     -- Auto-calculated
    land_extent_formatted           VARCHAR(50),                       -- "01A-02R-15.00P"

    -- Boundaries
    boundaries                      JSON,                              -- {north: {description, length, adjoins, notes}, ...}
    boundary_types_per_direction    JSON,
    physical_boundaries_types       JSON,                              -- ["brick_wall", "fence", ...]
    physical_boundaries_description TEXT,
    land_traditional_name           VARCHAR(200),
    entrance_type                   VARCHAR(100),
    boundaries_summary_text         TEXT,
    has_multiple_lots               BOOLEAN DEFAULT FALSE,
    lots_data                       JSON,

    -- Property Location
    property_village                VARCHAR(200),
    property_district               VARCHAR(100),
    property_province               VARCHAR(100),
    property_latitude               NUMERIC(10,8),
    property_longitude              NUMERIC(11,8),
    grama_niladari_division         VARCHAR(200),
    property_divisional_secretariat VARCHAR(200),
    hathpaththuwa                   VARCHAR(200),
    korale                          VARCHAR(200),
    pradeshiya_sabha                VARCHAR(200),
    ward_number                     VARCHAR(50),
    is_municipal_limit              BOOLEAN DEFAULT FALSE,
    assessment_number               VARCHAR(100),
    location_direction              VARCHAR(50),                       -- 'north-east', 'south', etc.

    -- Access Directions
    access_starting_point_name      VARCHAR(300),
    access_starting_point_latitude  NUMERIC(10,8),
    access_starting_point_longitude NUMERIC(11,8),
    access_directions_text          TEXT,
    access_distance_km              NUMERIC(8,2),
    access_duration_minutes         NUMERIC(8,2),
    access_road_type                VARCHAR(100),
    property_road_position          VARCHAR(50),
    access_road_conditions          JSON,                              -- [{road_type, condition, distance_km, notes}]
    location_map_image_data         TEXT,                               -- Static map URL or base64

    -- Land Description (BARE LAND CORE)
    land_shape                      VARCHAR(50),
    land_type                       VARCHAR(50),
    land_level                      VARCHAR(50),
    land_level_difference           VARCHAR(100),
    land_frontage_type              VARCHAR(100),
    land_frontage_width             NUMERIC(8,2),
    land_frontage_description       TEXT,
    soil_type                       VARCHAR(50),
    water_table_depth               NUMERIC(8,2),
    flood_risk                      VARCHAR(50),
    inundation_risk                 VARCHAR(50),
    earth_slip_risk                 VARCHAR(50),
    land_condition                  VARCHAR(50),
    land_condition_description      TEXT,
    land_description_text           TEXT,                               -- AI-generated or manual narrative

    -- Topography
    elevation_changes               VARCHAR(50),
    drainage_pattern                VARCHAR(50),
    vegetation_type                 VARCHAR(50),
    natural_features                TEXT,
    ongoing_construction_notes      TEXT,

    -- Property Photos
    property_photos                 JSON,                              -- [{url, caption, order}]

    -- Buildings (NULL for bare land)
    buildings                       JSON,                              -- NULL for bare_land
    occupier_name                   VARCHAR(200),                      -- NULL for bare_land
    occupier_relationship           VARCHAR(100),                      -- NULL for bare_land

    -- Locality Information
    distance_to_major_town_km       NUMERIC(8,2),
    major_town_name                 VARCHAR(200),
    nearby_facilities               JSON,                              -- [{type, name, distance_km, lat, lng, selected}]
    has_electricity                 BOOLEAN,
    water_supply_type               JSON,                              -- ["Pipe-borne", "Well"]
    telecommunication_types         JSON,
    internet_types                  JSON,
    has_public_transport            BOOLEAN,
    public_transport_routes         TEXT,
    public_transport_frequency      VARCHAR(100),
    nearest_bus_stop_distance_km    NUMERIC(8,2),
    nearest_bus_stop_name           VARCHAR(200),
    nearest_railway_station         VARCHAR(200),
    nearest_railway_distance_km     NUMERIC(8,2),
    area_type                       VARCHAR(50),
    development_level               VARCHAR(50),
    predominant_building_type       JSON,
    is_tourist_area                 BOOLEAN,
    tourist_attractions_nearby      TEXT,
    locality_description_text       TEXT,

    -- Legal Aspects
    ownership_type                  VARCHAR(100),
    title_search_conducted          VARCHAR(10),
    pedigree_search_conducted       VARCHAR(10),
    valuation_basis_note            TEXT,
    property_encumbered             VARCHAR(10),
    encumbrance_type                VARCHAR(100),
    encumbrance_details             TEXT,
    street_lines_status             VARCHAR(50),
    street_lines_gazette_ref        VARCHAR(100),
    street_lines_gazette_date       VARCHAR(50),
    street_lines_impact_description TEXT,
    building_limits_status          VARCHAR(50),
    building_distance_from_road     VARCHAR(100),
    building_plan_approved          VARCHAR(10),
    building_plan_reference         VARCHAR(100),
    building_approval_authority     VARCHAR(200),
    building_within_limits          VARCHAR(10),
    local_authority_rated           VARCHAR(10),
    local_authority_tax_levy        VARCHAR(100),
    rent_act_effectiveness          VARCHAR(100),

    -- Valuation (LAND ONLY for bare land)
    comparable_properties           JSON,                              -- [{property_type, location, extent, rate, total}]
    land_market_analysis            TEXT,
    valuation_land_extent           NUMERIC(10,4),
    valuation_rate_per_perch        NUMERIC(12,2),
    valuation_total_land_value      NUMERIC(15,2),
    valuation_buildings_data        JSON,                              -- NULL for bare_land
    valuation_total_buildings_value NUMERIC(15,2),                     -- NULL for bare_land
    valuation_addons                JSON,                              -- [{description, value}]
    valuation_total_addons_value    NUMERIC(15,2),
    valuation_market_value          NUMERIC(15,2),
    valuation_forced_sale_percentage NUMERIC(5,2),
    valuation_forced_sale_value     NUMERIC(15,2),
    valuation_insurance_value       NUMERIC(15,2),
    valuation_manual_overrides      JSON,

    -- Certification
    certification_text              TEXT,
    certificate_identity_confirmed  BOOLEAN,
    certification_valuer_name       VARCHAR(200),
    certification_valuer_designation VARCHAR(200),
    certification_date              VARCHAR(50),

    -- Invoice
    invoice_data                    JSON,

    -- Multi-Property (not used for single bare land)
    is_multi_property               BOOLEAN DEFAULT FALSE,
    property_count                  INTEGER DEFAULT 1,
    total_valuation_amount          NUMERIC(15,2),

    -- Timestamps
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at                      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_report_type ON reports(report_type);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_created_at ON reports(created_at);
```

### 3.2 Users Table

```sql
CREATE TABLE users (
    id                              SERIAL PRIMARY KEY,
    email                           VARCHAR(255) UNIQUE NOT NULL,
    password_hash                   VARCHAR(255) NOT NULL,
    full_name                       VARCHAR(200),
    honorific                       VARCHAR(20),
    phone                           VARCHAR(50),
    role                            VARCHAR(20) DEFAULT 'user',
    academic_qualifications         TEXT,
    membership_level                VARCHAR(100),
    professional_designation        VARCHAR(200),
    bank_accounts                   JSON,                              -- [{bank_name, branch, account_number, account_name}]
    house_number                    VARCHAR(100),
    area_development                VARCHAR(200),
    village                         VARCHAR(200),
    locality                        VARCHAR(200),
    office_department               VARCHAR(200),
    office_region                   VARCHAR(200),
    office_phone                    VARCHAR(50),
    preferred_letterhead_template   VARCHAR(100),
    is_email_verified               BOOLEAN DEFAULT FALSE,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at                      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.3 Jobs Table (Async DOCX Generation)

```sql
CREATE TABLE jobs (
    id                  VARCHAR(100) PRIMARY KEY,   -- UUID
    user_id             INTEGER REFERENCES users(id),
    report_id           INTEGER REFERENCES reports(id),
    job_type            VARCHAR(50),                 -- 'docx_generation'
    status              VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    result_url          TEXT,
    result_filename     VARCHAR(300),
    error_message       TEXT,
    progress_percent    INTEGER DEFAULT 0,
    progress_message    VARCHAR(300),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE
);
```

### 3.4 Token Blacklist Table

```sql
CREATE TABLE token_blacklist (
    id          SERIAL PRIMARY KEY,
    jti         VARCHAR(255) UNIQUE NOT NULL,        -- JWT ID
    user_id     INTEGER REFERENCES users(id),
    token_type  VARCHAR(20),                          -- 'access', 'refresh'
    expires_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.5 Audit Log Table

```sql
CREATE TABLE audit_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    action          VARCHAR(100),
    resource_type   VARCHAR(50),
    resource_id     VARCHAR(100),
    description     TEXT,
    details         JSON,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    request_id      VARCHAR(100),
    success         BOOLEAN DEFAULT TRUE,
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 4. EXAMPLE DATA: BEFORE & AFTER

### 4.1 Example Report Row - Draft (after Step 5 auto-save)

```json
{
  "id": 42,
  "user_id": 7,
  "report_type": "bare_land",
  "status": "draft",
  "applicant_full_name": "K.D.A. Nimalsiri",
  "applicant_id_type": "NIC",
  "applicant_id_number": "199512345678",
  "valuation_purpose": "For Mortgage Purposes",
  "property_identification_type": "plan",
  "plan_number": "1035",
  "plan_date": "15-06-2020",
  "lot_number": "Lot 15",
  "property_village": "Rambukkana",
  "property_district": "Kegalle",
  "property_province": "Sabaragamuwa",
  "property_latitude": 7.32456789,
  "property_longitude": 80.39876543,
  "land_extent_acres": null,
  "boundaries": null,
  "land_description_text": null,
  "valuation_market_value": null,
  "buildings": null,
  "created_at": "2026-02-07T03:15:00+05:30",
  "updated_at": "2026-02-07T03:22:00+05:30"
}
```

### 4.2 Example Report Row - Completed (after final submission)

```json
{
  "id": 42,
  "user_id": 7,
  "report_type": "bare_land",
  "status": "completed",
  "report_reference": "BL/2026/0042",
  "inspection_date": "05-02-2026",
  "report_date": "07-02-2026",

  "applicant_title": "Mr.",
  "applicant_full_name": "K.D.A. Nimalsiri",
  "applicant_id_type": "NIC",
  "applicant_id_number": "199512345678",
  "applicant_address_line1": "No. 45, Temple Road",
  "applicant_address_line2": "Rambukkana",
  "applicant_district": "Kegalle",
  "applicant_province": "Sabaragamuwa",
  "applicant_country": "Sri Lanka",
  "applicant_contact_number": "0771234567",
  "has_additional_owner": "no",

  "valuation_type": "Market Value",
  "valuation_purpose": "For Mortgage Purposes",
  "property_type_valued": "immovable property",
  "submission_organization": "Bank of Ceylon",
  "submission_address": "No. 1, Bank Street, Kegalle",
  "submission_recipient_position": "Manager",

  "property_identification_type": "plan",
  "lot_number": "Lot 15",
  "plan_number": "1035",
  "plan_date": "15-06-2020",
  "licensed_surveyor_name": "R.M.P. Bandara, L.S.",

  "land_extent_acres": 0,
  "land_extent_roods": 0,
  "land_extent_perches": 13.8,
  "land_extent_hectares": 0.0349,
  "land_extent_square_meters": 349.19,
  "land_extent_formatted": "00A-0R-13.80P",

  "boundaries": {
    "north": { "description": "Land of Mr. Perera", "length": "45ft", "adjoins": "Plan No. 1034 Lot 14" },
    "south": { "description": "Temple Road (20ft wide tarred road)", "length": "30ft" },
    "east": { "description": "Land of Mrs. Silva", "length": "50ft" },
    "west": { "description": "Paddy field", "length": "50ft" }
  },
  "physical_boundaries_types": ["brick_wall", "wire_fence"],
  "physical_boundaries_description": "Brick wall on north and south, wire fence on east and west",

  "property_village": "Rambukkana",
  "property_district": "Kegalle",
  "property_province": "Sabaragamuwa",
  "property_latitude": 7.32456789,
  "property_longitude": 80.39876543,
  "grama_niladari_division": "Rambukkana South",
  "property_divisional_secretariat": "Rambukkana",
  "pradeshiya_sabha": "Rambukkana",

  "access_starting_point_name": "Rambukkana Railway Station",
  "access_directions_text": "From Rambukkana Railway Station, proceed along Station Road in a northerly direction for approximately 0.5 km. Turn left onto Temple Road and continue for 200 meters. The subject property is located on the left side of the road.",
  "access_distance_km": 0.7,
  "access_duration_minutes": 3,
  "access_road_conditions": [
    { "road_type": "paved_road", "condition": "good", "distance_km": 0.5 },
    { "road_type": "concrete_road", "condition": "good", "distance_km": 0.2 }
  ],

  "land_shape": "rectangular",
  "land_type": "high_land",
  "land_level": "at_road_level",
  "soil_type": "laterite",
  "water_table_depth": 15,
  "flood_risk": "not_subject",
  "land_condition": "developed",
  "elevation_changes": "relatively_flat",
  "drainage_pattern": "well_drained",
  "vegetation_type": "grass_coverage",
  "land_description_text": "The subject property is a rectangular shaped high land of extent 13.8 perches situated at road level along Temple Road. The land comprises laterite soil with a water table depth of approximately 15 feet. The terrain is relatively flat with well-drained conditions and grass coverage. The property is not subject to flooding.",
  "land_frontage_type": "tarred",
  "land_frontage_width": 9.14,

  "property_photos": [
    { "url": "/uploads/report_42_photo_1.jpg", "caption": "Front view from Temple Road", "order": 1 },
    { "url": "/uploads/report_42_photo_2.jpg", "caption": "Boundary wall (north side)", "order": 2 }
  ],

  "buildings": null,
  "occupier_name": null,
  "occupier_relationship": null,

  "nearby_facilities": [
    { "type": "hospital", "name": "Rambukkana Base Hospital", "distance_km": 1.2, "selected": true },
    { "type": "school", "name": "Rambukkana Central College", "distance_km": 0.8, "selected": true },
    { "type": "bank", "name": "Bank of Ceylon - Rambukkana", "distance_km": 0.5, "selected": true }
  ],
  "has_electricity": true,
  "water_supply_type": ["Pipe-borne (NWSDB)"],
  "area_type": "residential",
  "development_level": "developing",
  "locality_description_text": "The subject property is situated in the Rambukkana area within the Kegalle District. The locality is a developing residential area approximately 0.5 km from the Rambukkana town center. Essential amenities including Rambukkana Base Hospital (1.2 km), Rambukkana Central College (0.8 km), and Bank of Ceylon (0.5 km) are within close proximity.",

  "ownership_type": "freehold",
  "title_search_conducted": "Yes",
  "pedigree_search_conducted": "No",
  "property_encumbered": "No",
  "local_authority_rated": "Yes",

  "comparable_properties": [
    { "property_type": "Residential", "location_description": "Temple Road, 200m north", "extent": 10, "rate_per_perch": 350000, "total_value": 3500000 },
    { "property_type": "Residential", "location_description": "Station Road, Rambukkana", "extent": 15, "rate_per_perch": 320000, "total_value": 4800000 },
    { "property_type": "Commercial", "location_description": "Main Street, Rambukkana", "extent": 8, "rate_per_perch": 500000, "total_value": 4000000 }
  ],

  "valuation_land_extent": 13.8,
  "valuation_rate_per_perch": 350000,
  "valuation_total_land_value": 4830000,
  "valuation_buildings_data": null,
  "valuation_total_buildings_value": null,
  "valuation_addons": [
    { "description": "Mature Jak Tree", "value": 25000 }
  ],
  "valuation_total_addons_value": 25000,
  "valuation_market_value": 4855000,
  "valuation_forced_sale_percentage": 75,
  "valuation_forced_sale_value": 3641250,
  "valuation_insurance_value": 0,

  "certification_text": "I hereby certify that I have personally inspected the above described property...",
  "certificate_identity_confirmed": true,
  "certification_valuer_name": "P.B. Gunasekara",
  "certification_valuer_designation": "Chartered Valuation Surveyor",
  "certification_date": "07-02-2026",

  "invoice_data": {
    "items": [{ "description": "Professional Fees", "total": 15000 }],
    "subtotal": 15000,
    "traveling_charges": 2500,
    "discount": 0,
    "total": 17500,
    "bank_account_ids": ["acc_001"]
  },

  "created_at": "2026-02-07T03:15:00+05:30",
  "updated_at": "2026-02-07T04:45:00+05:30"
}
```

---

## 5. EXTERNAL SERVICE MAP

| Service | Provider | Usage in Bare Land Flow | API Key Env Var | Rate Limits (App-Level) | Failure Fallback |
|---------|----------|------------------------|-----------------|------------------------|------------------|
| Google Geocoding API | Google Cloud | Reverse geocode map clicks -> village, district, province | `GOOGLE_MAPS_API_KEY` | 60 req/min | Manual coordinate + address entry |
| Google Directions API | Google Cloud | Route from starting point to property | `GOOGLE_MAPS_API_KEY` | 60 req/min | Manual access directions text |
| Google Static Maps API | Google Cloud | Generate route map image for report | `GOOGLE_MAPS_API_KEY` | 60 req/min | Report generated without map image |
| Google Places API | Google Cloud | Starting point autocomplete + nearby facility search | `GOOGLE_MAPS_API_KEY` | 60 req/min | Manual facility entry |
| Google Cloud Vision | Google Cloud | OCR text extraction from survey plans/deeds | `GOOGLE_VISION_API_KEY` | 10 req/min | Manual field entry |
| Anthropic Claude API | Anthropic | Land narrative, locality narrative, OCR field parsing, access text transformation | `ANTHROPIC_API_KEY` | 20 req/min (per narrative type) | Manual text entry, fallback local text generation |
| SendGrid | Twilio SendGrid | Email verification, password reset emails | `SENDGRID_API_KEY` | N/A | Logged error, user notified |
| Redis | Self-hosted/Cloud | Rate limiting storage, caching, job queue | `REDIS_URL` | N/A | In-memory fallback (dev), fail-closed (prod) |
| PostgreSQL | Self-hosted/Cloud | Primary data storage | `DATABASE_URL` | N/A | Application cannot function |

---

## 6. DUPLICATES & REDUNDANCY AUDIT

### 6.1 Active Duplications Found

| Issue | Files Involved | Estimated Duplicate Lines | Severity | Safe to Refactor | Impact on Bare Land |
|-------|---------------|--------------------------|----------|-----------------|-------------------|
| **Form page handlers are 90% identical** | `BareLandForm.tsx` (368 lines) vs `ResidentialPropertyForm.tsx` (393 lines) | ~340 lines | MEDIUM | YES - merge with `reportType` parameter, conditional building cleanup | NONE - same data flow, different `report_type` string |
| **Report & Property models duplicate 150+ field definitions** | `models.py` lines 126-443 (Report) vs lines 446-649 (Property) | ~150 columns | HIGH | POST-LAUNCH - requires data migration | MEDIUM - single bare land uses Report model, multi-property uses Property model, data could diverge |
| **ReportBase Pydantic schema covers ALL report types in one class** | `schemas.py` lines 458-1060 | ~600 lines | MEDIUM | POST-LAUNCH - split into per-type schemas | LOW - validation happens in frontend forms |
| **CRUD operations repeat create/get/update/delete/duplicate patterns** | `crud.py`: Report ops ~400 lines vs Property ops ~300 lines | ~200 lines | LOW | POST-LAUNCH - extract BaseCRUD class | NONE |
| **Narrative services share water supply / label mapping code** | `building_narrative.py` lines 263-286, `locality_narrative.py` lines 95-114 | ~40 lines | LOW | YES - extract to `narrative_constants.py` | NONE |

### 6.2 Successfully Consolidated Items (Already Done)

| Item | What Happened | Current State |
|------|--------------|---------------|
| `PropertyEditFormBareLand.tsx` + `PropertyEditFormResidential.tsx` | Both deleted in commit `dcaab1e`. Replaced by `MultiPropertyRedesignedStepForm.tsx` | Consolidated into single component with `propertyType` parameter |
| `MultiPropertyStepForm.tsx` (old multi-property form) | Deleted. Replaced by `MultiPropertyRedesignedStepForm.tsx` | Clean replacement, no orphaned imports |
| `MultiStepForm.tsx.backup` | Deleted. Was an 80KB backup of the form | Removed |
| Narrative service base class | Created `base_narrative.py` with shared Claude API client management | `building_narrative.py`, `land_narrative.py`, `locality_narrative.py` all extend `BaseNarrativeService` |

### 6.3 Dead / Garbage Files

| File | Status | Action Needed |
|------|--------|---------------|
| `nul` (project root) | Empty Windows artifact, 0 bytes, untracked | DELETE - garbage file |
| `workflow plan.md` | 1 blank line, untracked | DELETE - empty artifact |
| `structure review.md` | 425 lines of component split recommendations, untracked | KEEP - useful internal reference |
| `updates to do.md` | 976 lines of comprehensive status tracking, untracked | KEEP - active tracking document |
| `DEPLOYMENT.md`, `DEVELOPMENT.md`, `IMPLEMENTATION_SUMMARY.md`, `QUICK_START_GUIDE.md`, `TECHNICAL_DEBT.md`, `docs/MONITORING.md`, `plan.md` | All deleted in current branch | SAFE - info consolidated into `updates to do.md` |
| `backend/tests/test_health.py`, `backend/tests/test_reports.py` | Deleted in cleanup | WARNING - no replacement tests created for these endpoints |

### 6.4 Bare Land Specific: Unnecessary Code Paths

| Location | Code | Issue | Risk |
|----------|------|-------|------|
| `BareLandForm.tsx` lines 82-101 | Building `utilities_services` cleanup loop | This code iterates over `buildings` array converting string values to arrays. For bare land, `buildings` is always `null`/empty, so this loop never executes. | NONE - dead code path, safe but wasteful |
| `MultiStepForm.tsx` | Building tab in `PropertyDescriptionStep` | Hidden via `isBareLand` prop, but component still mounts with building-related state. | NONE - hidden, doesn't affect behavior. Could improve performance by lazy-loading building tab only for residential. |
| `schemas.py` ReportBase | Building fields (`buildings`, `occupier_name`, etc.) accepted for bare land type | Backend accepts building data even for `bare_land` reports. Frontend nulls them out, but API doesn't enforce. | LOW - frontend enforces, but no server-side schema enforcement per report type. |

### 6.5 Recommendations Priority

**Immediate (Safe, No Risk)**:
1. Delete `nul` and `workflow plan.md` files
2. Extract shared label mappings to `backend/app/services/narrative_constants.py`

**Short Term (Phase 3)**:
3. Merge `BareLandForm.tsx` + `ResidentialPropertyForm.tsx` into single `PropertyReportForm.tsx` with `reportType` parameter
4. Add automated tests for bare land form flow (currently 0 dedicated tests)

**Medium Term (Post-Launch)**:
5. Normalize Report/Property models - move all property data to Property table only
6. Split `ReportBase` schema into per-type schemas with cross-type validation
7. Extract `BaseCRUD` class to eliminate CRUD pattern duplication

---

*End of Document*
