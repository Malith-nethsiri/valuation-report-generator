# Codebase Structure Review

## Executive Summary

This document identifies files that should be split for maintainability, provides logical split strategies, documents risks, and outlines key considerations for each refactoring.

---

## CRITICAL FILES (Immediate Attention Required)

### 1. `backend/app/docx_generator.py` - 6,623 LOC

**Current State:**
- Monolithic document generation module
- Contains: formatting helpers, section generators, image processors, narrative builders, table generators, and report orchestration
- Mixed concerns: low-level DOCX manipulation + business logic + text generation

**Why Split:**
- Impossible to understand full file at once
- High risk of unintended side effects when editing
- Merge conflicts are frequent
- Testing individual sections is difficult

**Logical Split Strategy:**

```
backend/app/docx/
├── __init__.py           # Re-export main generate_report function
├── constants.py          # FONT_SIZE_*, SPACING_*, IMAGE_* constants (~100 LOC)
├── helpers.py            # Utility functions: to_float, safe_get_*, format_currency (~200 LOC)
├── formatting.py         # add_border_to_paragraph, add_section_heading, format_material_list (~300 LOC)
├── images.py             # calculate_image_dimensions, apply_letterbox_to_image, insert_map_image (~400 LOC)
├── sections/
│   ├── __init__.py
│   ├── title_block.py        # generate_title_block, generate_applicant_statement (~300 LOC)
│   ├── situation.py          # generate_situation_text, generate_smart_address (~400 LOC)
│   ├── access.py             # Access and road conditions sections (~300 LOC)
│   ├── description.py        # Land and building descriptions (~500 LOC)
│   ├── valuation.py          # Valuation calculations and tables (~600 LOC)
│   ├── certification.py      # Certification section generation (~200 LOC)
│   └── invoice.py            # Invoice table generation (~300 LOC)
├── tables.py             # Generic table building utilities (~300 LOC)
└── generator.py          # Main orchestration: generate_user_data_docx (~500 LOC)
```

**Risks:**
- Circular imports between sections (mitigate: use helpers module for shared utilities)
- Breaking existing report generation (mitigate: comprehensive integration tests before/after)
- Import path changes break other modules (mitigate: re-export from `__init__.py`)

**Considerations:**
- Keep `generate_user_data_docx` as the single public entry point
- Sections should be independently testable
- Each section file should have clear inputs (report object) and outputs (modified doc)

---

### 2. `backend/app/main.py` - 3,296 LOC

**Current State:**
- All API routes in single file
- Contains: auth endpoints, report CRUD, property CRUD, vehicle CRUD, OCR endpoints, health checks, middleware setup
- Mixed concerns: route definitions + request validation + business orchestration

**Why Split:**
- Finding specific endpoint is difficult
- Related routes are scattered throughout file
- Changes to one domain affect entire file

**Logical Split Strategy:**

```
backend/app/
├── main.py               # FastAPI app setup, middleware, startup/shutdown (~300 LOC)
├── routes/
│   ├── __init__.py       # Router aggregation
│   ├── auth.py           # /api/auth/* endpoints (~400 LOC)
│   ├── reports.py        # /api/reports/* CRUD endpoints (~500 LOC)
│   ├── properties.py     # /api/properties/* endpoints (~400 LOC)
│   ├── vehicles.py       # /api/vehicles/* endpoints (~400 LOC)
│   ├── ocr.py            # /api/ocr/* endpoints (~200 LOC)
│   ├── health.py         # Health check endpoints (~100 LOC)
│   ├── users.py          # /api/users/*, /api/profile endpoints (~200 LOC)
│   └── ai.py             # AI generation endpoints (land, building narrative) (~300 LOC)
└── middleware/           # Already exists - good!
```

**Risks:**
- Dependency injection patterns may need adjustment (mitigate: use FastAPI's `Depends` consistently)
- Shared utilities need extraction (mitigate: create `routes/dependencies.py` for common deps)
- OpenAPI doc generation may be affected (mitigate: test API docs after split)

**Considerations:**
- Use FastAPI's `APIRouter` for each route file
- Keep middleware and startup logic in main.py
- Ensure consistent error handling across all route files

---

### 3. `frontend/src/components/MultiStepForm.tsx` - 2,709 LOC

**Current State:**
- Giant multi-step form component
- Contains: 13 step components defined inline, form state management, navigation logic, validation, submission handlers
- Mixed concerns: UI rendering + business logic + form orchestration

**Why Split:**
- Steps are logically independent but physically coupled
- Can't test individual steps in isolation
- Any change requires understanding the entire file

**Logical Split Strategy:**

```
frontend/src/components/MultiStepForm/
├── index.tsx                      # Main orchestration component (~400 LOC)
├── types.ts                       # StepComponentProps, FormData types (~50 LOC)
├── hooks/
│   ├── useFormNavigation.ts       # Step navigation, validation logic (~150 LOC)
│   ├── useFormPersistence.ts      # Draft save, auto-save logic (~100 LOC)
│   └── useFormSubmission.ts       # Submit handlers, deed transformation (~150 LOC)
├── steps/
│   ├── PropertyPlanStep.tsx       # Step 1: OCR + identification type (~350 LOC)
│   ├── ExtentBoundariesStep.tsx   # Step 2: Land extent (~100 LOC)
│   ├── PropertySearchStep.tsx     # Step 3: Google Maps (~150 LOC)
│   ├── PropertyLocationStep.tsx   # Step 4: Administrative divisions (~100 LOC)
│   ├── ApplicantPurposeStep.tsx   # Step 9: Applicant info (~200 LOC)
│   └── AdditionalDetailsStep.tsx  # Step 10 (~150 LOC)
├── components/
│   ├── StepIndicator.tsx          # Progress bar UI (~100 LOC)
│   ├── StepHeader.tsx             # Step title/subtitle (~50 LOC)
│   └── FormButtons.tsx            # Navigation buttons (~100 LOC)
└── utils/
    └── deedTransformer.ts         # Deed data transformation (~50 LOC)
```

**Risks:**
- Shared form state across steps (mitigate: pass via props or use form context)
- Step dependencies on watch/setValue (mitigate: create typed step props interface)
- Navigation state is complex (mitigate: extract to custom hook first)

**Considerations:**
- Extract navigation hook FIRST - it's the most interconnected
- Steps 5-8 and 11-13 already use external components (LocalityInformationSection, etc.) - good pattern
- Keep form methods (react-hook-form) at orchestrator level, pass to steps

---

### 4. `frontend/src/components/PropertyDescriptionStep.tsx` - 2,546 LOC

**Current State:**
- Combines land description AND building management
- Contains: tab navigation, building CRUD, floor/room management, photo upload handlers, AI description generation
- Mixed concerns: land UI + building UI + photo management + API calls

**Why Split:**

```
frontend/src/components/PropertyDescription/
├── index.tsx                      # Tab container + orchestration (~150 LOC)
├── LandDescriptionTab/
│   ├── index.tsx                  # Land form fields (~300 LOC)
│   ├── LandCharacteristics.tsx    # Shape, type, frontage selects (~200 LOC)
│   └── useGenerateLandDescription.ts  # AI generation hook (~100 LOC)
├── BuildingTab/
│   ├── index.tsx                  # Building list + add/remove (~200 LOC)
│   ├── BuildingCard.tsx           # Single building card (~400 LOC)
│   ├── FloorManager.tsx           # Floor add/edit/remove (~200 LOC)
│   ├── RoomManager.tsx            # Room CRUD with summary calc (~200 LOC)
│   └── BuildingPhotoUpload.tsx    # Photo upload/drag-drop (~250 LOC)
├── PropertyPhotos/
│   ├── index.tsx                  # Property-level photos (~200 LOC)
│   └── PhotoGrid.tsx              # Reusable photo grid (~100 LOC)
└── hooks/
    ├── useBuildingState.ts        # Building array state management (~150 LOC)
    └── usePhotoUpload.ts          # Shared upload logic (~100 LOC)
```

**Risks:**
- Building state is deeply nested (mitigate: extract useBuildingState hook first)
- Photo upload logic is duplicated for building/property (mitigate: create shared hook)
- Tab state coordination (mitigate: keep at orchestrator level)

**Considerations:**
- BuildingCard is itself 400+ LOC - may need further splitting later
- Photo upload handlers are nearly identical - prime candidate for shared hook
- Constants already extracted to `propertyDescriptionConstants.ts` - good!

---

### 5. `backend/app/schemas.py` - 2,116 LOC

**Current State:**
- All Pydantic schemas in single file
- Contains: User schemas, Report schemas (massive), Building schemas, Vehicle schemas, Auth schemas
- ReportBase alone is ~200 fields

**Why Split:**

```
backend/app/schemas/
├── __init__.py           # Re-export all schemas for backwards compatibility
├── auth.py               # UserBase, UserCreate, UserLogin, TokenResponse (~150 LOC)
├── user.py               # UserUpdate, UserResponse, BankAccount schemas (~150 LOC)
├── building.py           # Building, Floor, Room, ConstructionMaterials (~300 LOC)
├── report.py             # ReportBase, ReportCreate, ReportUpdate (~500 LOC)
├── property.py           # Property schemas for multi-property (~300 LOC)
├── vehicle.py            # Vehicle schemas (~200 LOC)
├── common.py             # Shared schemas (DeedInfo, RoadCondition, etc.) (~200 LOC)
├── responses.py          # API response schemas (HealthResponse, etc.) (~100 LOC)
└── validators.py         # Validation helper functions (~200 LOC)
```

**Risks:**
- Circular imports between schemas (mitigate: common.py for shared types, forward references)
- Breaking imports throughout codebase (mitigate: re-export from `__init__.py`)
- Pydantic model references (mitigate: use `TYPE_CHECKING` imports)

**Considerations:**
- Split by domain, not by schema type (Create/Update/Response)
- Keep validation helpers in separate file
- ReportBase/ReportCreate/ReportUpdate should stay together (same file)

---

### 6. `backend/app/crud.py` - 1,346 LOC

**Current State:**
- All database operations in single file
- Contains: User CRUD, Report CRUD, Property CRUD, Vehicle CRUD, Report-Property associations

**Why Split:**

```
backend/app/crud/
├── __init__.py           # Re-export all functions
├── base.py               # verify_ownership, _duplicate_entity_data utilities (~100 LOC)
├── users.py              # User CRUD + bank accounts (~200 LOC)
├── reports.py            # Report CRUD + filtering/pagination (~400 LOC)
├── properties.py         # Property CRUD + report associations (~300 LOC)
├── vehicles.py           # Vehicle CRUD + report associations (~300 LOC)
└── validation.py         # validate_report_buildings, etc. (~100 LOC)
```

**Risks:**
- Shared session handling patterns (mitigate: document session lifecycle expectations)
- Import changes break main.py (mitigate: re-export from `__init__.py`)

---

## HIGH PRIORITY FILES (Split Soon)

### 7. `frontend/src/components/InteractivePropertyMap.tsx` - 1,326 LOC

**Why Split:**
- Contains: Google Maps setup, autocomplete, markers, directions, route generation, manual coordinate input, road conditions, fallback mode
- Multiple distinct concerns mixed together

**Logical Split:**

```
frontend/src/components/InteractivePropertyMap/
├── index.tsx                  # Main component, map container (~200 LOC)
├── hooks/
│   ├── useGoogleMap.ts        # Map initialization (~150 LOC)
│   ├── useAutocomplete.ts     # Property/starting point autocomplete (~150 LOC)
│   ├── useDirections.ts       # Route calculation and rendering (~200 LOC)
│   └── useReverseGeocode.ts   # Geocoding utilities (~100 LOC)
├── components/
│   ├── SearchInputs.tsx       # Property and starting point inputs (~150 LOC)
│   ├── ManualCoordinates.tsx  # Manual lat/lng input (~100 LOC)
│   └── RouteDisplay.tsx       # Route info display (~100 LOC)
└── FallbackMode.tsx           # When Google Maps fails (~150 LOC)
```

**Risks:**
- Google Maps refs are shared across functionality
- Map instance coordination between hooks

---

### 8. `backend/app/models.py` - 941 LOC

**Why Split:**
- Report model alone is 300+ lines with 100+ fields
- Mixing Job, User, Report, Property, Vehicle models

**Logical Split:**

```
backend/app/models/
├── __init__.py           # Re-export all models
├── base.py               # Base class, common mixins
├── user.py               # User model (~100 LOC)
├── report.py             # Report model (~350 LOC)
├── property.py           # Property model (~300 LOC)
├── vehicle.py            # Vehicle model (~150 LOC)
└── job.py                # Job, TokenBlacklist models (~100 LOC)
```

**Risks:**
- SQLAlchemy relationships reference other models (use string references)
- Alembic migrations may need adjustment

---

### 9. `frontend/src/services/api.ts` - 680 LOC

**Why Split:**

```
frontend/src/services/
├── api/
│   ├── index.ts          # axios instance, interceptors (~150 LOC)
│   ├── auth.ts           # authApi object (~100 LOC)
│   ├── reports.ts        # reportApi object (~200 LOC)
│   ├── properties.ts     # propertyApi object (~100 LOC)
│   ├── vehicles.ts       # vehicleApi object (~100 LOC)
│   └── utils.ts          # filterReportData, retry helpers (~50 LOC)
```

---

## MEDIUM PRIORITY FILES (300-900 LOC)

| File | LOC | Suggested Split |
|------|-----|-----------------|
| `MultiPropertyRedesignedStepForm.tsx` | 915 | Extract step components, property list management |
| `ValuationSection.tsx` | 882 | Split land valuation, building valuation, addons into sub-components |
| `LocalityInformationSection.tsx` | 832 | Extract facility picker, infrastructure toggles, transport section |
| `VehicleFeaturesValuationStep.tsx` | 824 | Extract feature sections, valuation calculator |
| `PropertyLocationMap.tsx` | 713 | Merge with InteractivePropertyMap or extract shared hooks |
| `VehicleDescriptionStep.tsx` | 707 | Extract photo upload, specs form, condition assessment |
| `VehicleStepForm.tsx` | 649 | Follow same pattern as MultiStepForm split |
| `BoundaryInformationSection.tsx` | 632 | Extract boundary editor per direction, physical boundary selector |
| `ocr_service.py` | 784 | Split by document type handler |
| `access_transformer.py` | 643 | Extract road condition logic, distance calculations |
| `ai_parser.py` | 564 | Split by parsing strategy |
| `json_validators.py` | 574 | Split by validated entity type |

---

## RISKS SUMMARY

### Technical Risks

1. **Circular Imports** - Most common risk when splitting Python/TypeScript files
   - Mitigation: Create `common.py`/`types.ts` for shared definitions
   - Use lazy imports or TYPE_CHECKING blocks

2. **Breaking Existing Imports** - Other files import from old locations
   - Mitigation: Always re-export from `__init__.py` / `index.ts`
   - Use sed/grep to find and update all imports

3. **State Management Fragmentation** - React component state scattered across hooks
   - Mitigation: Keep state ownership clear (one source of truth)
   - Document which hook owns which state

4. **Test Coverage Gaps** - Existing tests may not cover all paths
   - Mitigation: Write characterization tests BEFORE refactoring
   - Run tests after each split, not at the end

### Process Risks

1. **Merge Conflicts** - Split during active development
   - Mitigation: Coordinate with team, split during low-activity periods

2. **Incomplete Splits** - Stopping halfway leaves codebase worse
   - Mitigation: Complete one file at a time, don't start multiple

3. **Over-engineering** - Creating too many tiny files
   - Mitigation: Keep related code together, split by responsibility not by line count

---

## RECOMMENDED ORDER OF OPERATIONS

### Phase 1: Backend Schemas & CRUD (Low Risk, High Impact)
1. Split `schemas.py` into domain modules
2. Split `crud.py` into domain modules
3. Both are pure data/logic - no UI side effects

### Phase 2: Backend Routes (Medium Risk)
4. Split `main.py` routes into router modules
5. Test each endpoint after split

### Phase 3: Frontend Services (Low Risk)
6. Split `api.ts` into domain modules

### Phase 4: Frontend Components (Higher Risk)
7. Split `PropertyDescriptionStep.tsx` (extract hooks first)
8. Split `MultiStepForm.tsx` (extract navigation hook first)
9. Split `InteractivePropertyMap.tsx` (extract Google Maps hooks)

### Phase 5: Document Generation (Highest Risk)
10. Split `docx_generator.py` (requires comprehensive testing)

---

## KEY PRINCIPLES FOR SPLITTING

1. **Extract Hooks Before Components** - Stateful logic is harder to untangle than UI
2. **One Responsibility Per File** - Can you explain it in one sentence?
3. **Re-export Everything** - Maintain backwards compatibility with `index.ts`/`__init__.py`
4. **Test Before AND After** - Characterization tests catch regressions
5. **Split Vertically by Feature** - Not horizontally by layer (all validators together)
6. **Keep Related Code Together** - CRUD operations for Report stay in one file

---

## METRICS TO TRACK

After splitting, these metrics should improve:

| Metric | Before | Target |
|--------|--------|--------|
| Largest file | 6,623 LOC | < 500 LOC |
| Average file size | ~400 LOC | ~150 LOC |
| Files > 500 LOC | 15+ | < 5 |
| Time to find code | ? | < 30 seconds |
| Test isolation | Poor | Good |

---

*Document generated: 2024*
*Review periodically as codebase evolves*
