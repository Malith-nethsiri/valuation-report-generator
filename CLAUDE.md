# Project: Property & Vehicle Valuation Report Generator

## Overview
A production-ready, full-stack web application for Sri Lankan professional valuers.
Automates formal DOCX valuation reports for properties, land, multi-property portfolios,
and vehicles. Integrates Claude AI, Google Vision OCR, Google Maps, and PostgreSQL.

**Stack:** FastAPI (Python 3.11) + React 18 (TypeScript) + PostgreSQL (Neon) + Redis
**Deployment:** Backend → Render | Frontend → Vercel | DB → Neon

---

## Golden Rules (Read These First)

1. **Never create random files.** Every file must have a clear, singular purpose that fits the existing structure. If you're unsure where code belongs, find the right existing file first.
2. **Never add loose lines or orphan code.** Every function, class, or constant must live in the correct module.
3. **Never duplicate logic.** Before writing anything, search for it — utilities, helpers, and services already exist.
4. **Never exceed 600 LOC per file.** If a file needs to grow beyond that, split it along clear domain lines first.
5. **Follow existing patterns exactly.** Do not invent new patterns. Match the style, structure, and conventions already in use.
6. **No speculative code.** Only implement what is explicitly required. No "just in case" helpers, no unused exports, no forward-compatibility shims.

---

## Architecture: How the Code is Organized

### Backend: Layered, Domain-Driven
```
Request → Router (routers/) → Service (services/) → CRUD (crud/) → Model (models.py) → DB
```
- **Routers** handle HTTP: validation, auth, ownership checks, response shaping
- **Services** contain business logic: AI calls, OCR, narrative generation, file ops
- **CRUD** handles all database access via the `BaseCRUD` base class
- **Models** define the DB schema (SQLAlchemy ORM)
- **Utils** provide shared helpers: safe field access, error formatting, text tools

### Frontend: Feature-Based, Hook-Driven
```
Page → Multi-Step Form → Section Components → Custom Hooks → API Services → Backend
```
- **Pages** compose forms and layouts
- **Components** are pure UI; complex logic lives in hooks
- **Hooks** contain all business logic, API calls, and state management
- **Services (`api/`)** are the only place HTTP calls are made
- **Types** define all data shapes; never use `any`

---

## Critical File Map

### Backend

#### Core
| File | LOC | Role |
|------|-----|------|
| `backend/app/main.py` | ~242 | App factory, middleware registration, router mounting |
| `backend/app/models.py` | ~757 | SQLAlchemy ORM — 11 tables. Do not add columns here without a migration |
| `backend/app/auth.py` | — | JWT, bcrypt, OAuth2, RBAC |
| `backend/app/database.py` | ~85 | Engine, SessionLocal, `get_db` dependency |
| `backend/app/base_crud.py` | ~56 | `BaseCRUD` generic class — extend, never duplicate |
| `backend/app/constants.py` | — | Global enums (ValuationPurpose, PropertyType, etc.) |

#### Routers (`backend/app/routers/`) — 13 modules
Each router owns exactly one domain. Do not add cross-domain logic to a router.

| Router | Role |
|--------|------|
| `auth.py` | Login, register, password reset, email verification, Google OAuth, token refresh |
| `reports.py` | Report CRUD, DOCX download, status tracking |
| `properties.py` | Property CRUD, multi-property ops, duplicates |
| `vehicles.py` | Vehicle CRUD, valuation tracking, library |
| `maps.py` | Google Maps geocoding, place search |
| `admin.py` | User management, stats, audit logs |
| `ocr.py` | File upload, OCR processing |
| `narratives.py` | AI text generation for land/building/locality |
| `jobs.py` | Job polling, status, result retrieval |
| `autocomplete.py` | Credentials, designations, memberships |
| `locality.py` | Administrative divisions data |
| `users.py` | Profile and credentials updates |
| `health.py` | Health check |

#### CRUD (`backend/app/crud/`) — domain-specific files
| File | Role |
|------|------|
| `report_crud.py` | Report create/read/filter/soft-delete |
| `property_crud.py` | Property CRUD, bulk ops, ownership |
| `vehicle_crud.py` | Vehicle CRUD with valuation data |
| `user_crud.py` | User CRUD, roles, professional data |
| `building_helpers.py` | Floors, rooms, photos |

#### Services (`backend/app/services/`)
| File / Folder | Role |
|------|------|
| `anthropic_client.py` | **Singleton** Anthropic client — always import from here, never instantiate directly |
| `ai_valuation.py` | Claude AI vehicle valuation |
| `ai/property_parser.py` | Claude AI property data extraction from OCR |
| `ai/vehicle_parser.py` | Claude AI vehicle spec extraction from OCR |
| `building_narrative.py` | Building description generation |
| `land_narrative.py` | Land description generation |
| `locality_narrative.py` | Locality/area description generation |
| `base_narrative.py` | Shared narrative base class |
| `ocr_service.py` | OCR orchestrator |
| `ocr/pipeline.py` | Multi-step OCR processing |
| `ocr/vision_client.py` | Google Cloud Vision wrapper |
| `ocr/preprocessor.py` | Image preprocessing |
| `places_service.py` | Google Places API |
| `file_storage.py` | S3/local DOCX storage |
| `job_service.py` | Async DOCX job tracking |
| `email_service.py` | SendGrid email |
| `google_oauth_service.py` | Google OAuth2 flow |
| `cache_service.py` | Redis caching |
| `redis_client.py` | Redis connection management |
| `audit_service.py` | Security event logging |

#### DOCX Generation (`backend/app/docx_generation/`)
All report generation lives here. The entry point is registered in `__init__.py`.

| File | Role |
|------|------|
| `single_property_generator.py` | Single property DOCX |
| `multi_property_generator.py` | Portfolio DOCX |
| `vehicle_generator.py` | Vehicle report DOCX |
| `invoice_generator.py` | Invoice/fee schedule |
| `property_section_generator.py` | Property detail sections |
| `building_renderer.py` | Building-specific sections |
| `text_generators.py` | Property description / valuation text |
| `paragraph_builders.py` | DOCX paragraph construction |
| `formatting.py` | Text formatting and styling |
| `images.py` | Image embedding |
| `styling.py` | DOCX style definitions |
| `helpers.py` | General utilities |
| `__init__.py` | Generator registry — register new generators here |

#### Utilities (`backend/app/utils/`)
These exist. Use them. Do not recreate them elsewhere.

| File | Role |
|------|------|
| `json_validators.py` | `safe_get_json_field()`, `to_float()` — always use these when reading report data |
| `extent_calculator.py` | Sri Lankan A-R-P land measurement conversions |
| `error_responses.py` | Standardized error formatting — never return raw dicts for errors |
| `api_client.py` | HTTP client with circuit breaker for external APIs |
| `fallbacks.py` | Fallback templates when AI/Maps fail |
| `text_helpers.py` | Text case, number formatting |
| `upload_validator.py` | File type/size validation |

#### Middleware (`backend/app/middleware/`)
| File | Role |
|------|------|
| `rate_limiting.py` | Token bucket rate limiting (Redis-backed) |
| `csrf_protection.py` | CSRF token validation |
| `security_headers.py` | CSP, X-Frame-Options, etc. |

#### Schemas (`backend/app/schemas/`)
Pydantic schemas are split by domain. Add to the correct file, never create a new schema file without a strong reason.

#### Letterhead Templates (`backend/app/letterhead_templates/`)
7 templates (classic, modern, premium, executive, compact, minimal + base).
Register new templates in `__init__.py`.

---

### Frontend

#### Pages (`frontend/src/pages/`) — 11 pages
Compose forms and layouts. Do not put business logic in pages — put it in hooks.

#### Components (`frontend/src/components/`) — 40+ components
Organized by domain:
- Multi-step forms: `MultiStepForm.tsx`, `MultiPropertyRedesignedStepForm.tsx`, `VehicleStepForm.tsx`
- Property sections: `ValuationSection.tsx`, `LocalityInformationSection.tsx`, `BoundaryInformationSection.tsx`, etc.
- Building: `building/BuildingConstructionSection.tsx`
- Vehicle: `vehicle/` folder
- Steps: `steps/` folder
- Shared: `AutocompleteInput.tsx`, `LandExtentInput.tsx`, `ManualAddressInput.tsx`, etc.

#### API Services (`frontend/src/services/api/`)
All HTTP calls go here. Never use `fetch()` directly anywhere in the codebase.

| File | Role |
|------|------|
| `client.ts` | Axios instance, token management, CSRF initialization |
| `reportApi.ts` | Report CRUD, DOCX generation |
| `vehicleApi.ts` | Vehicle library and CRUD |
| `authApi.ts` | Login, register, OAuth |
| `jobApi.ts` | Job polling and status |
| `ocrApi.ts` | OCR file upload |
| `letterheadApi.ts` | Letterhead selection |
| `bankAccountApi.ts` | Bank account submission |
| `index.ts` | Re-exports |

#### Custom Hooks (`frontend/src/hooks/`) — 11 hooks
Business logic lives in hooks, not components. Check here before adding logic to a component.

| Hook | Role |
|------|------|
| `useBuildings.ts` | Building CRUD |
| `useFloors.ts` | Floor CRUD |
| `useRooms.ts` | Room CRUD |
| `useBuildingPhotos.ts` | Building photo management |
| `useBuildingManager.ts` | Building manager state |
| `useJobPolling.ts` | DOCX generation polling |
| `useDraftManager.ts` | Draft auto-save and recovery |
| `useReportsPagination.ts` | Report list pagination |
| `useGoogleMapsStatus.ts` | Maps API readiness |
| `useAdministrativeDivisions.ts` | Admin divisions lookup |
| `useNavigationBlocker.ts` | Unsaved changes warning |

#### Types (`frontend/src/types/`) — 13 files
Types are split by domain. Add to the correct file.

| File | Primary Types |
|------|---------------|
| `report.ts` | ReportState, PropertyData, AllReportData |
| `vehicle.ts` | VehicleData, VehicleCondition, VehicleFeatures |
| `building.ts` | BuildingData, Construction, Occupancy |
| `auth.ts` | User, AuthState, OAuthData |
| `valuation.ts` | ValuationPurpose, ValuationMethod |
| `property.ts` | PropertyLocation, PropertyStatus |
| `maps.ts` | GeocodeResult, PlaceDetails |
| `invoice.ts` | Invoice data |
| `admin.ts` | Admin-specific types |
| `misc.ts` | Utility types |
| `index.ts` | Re-exports |

#### Utils (`frontend/src/utils/`) — 14 utility modules
These exist. Use them. Do not recreate them.

| File | Role |
|------|------|
| `extentCalculator.ts` | A-R-P conversion (mirrors backend) |
| `currency.ts` | LKR formatting |
| `secureStorage.ts` | AES-256 encrypted sessionStorage for tokens |
| `errorTransformer.ts` | Backend errors → user messages |
| `validationErrorTransformer.ts` | Zod errors → user messages |
| `validators.ts` | Field validation functions |
| `landDescriptionGenerator.ts` | Land description from form data |
| `textFormatter.ts` | Text normalization |
| `fieldNameMapper.ts` | form ↔ API field name translation |
| `downloadHelper.ts` | DOCX download |
| `csrf.ts` | CSRF token helpers |

#### Schemas (`frontend/src/schemas/`)
| File | Purpose |
|------|---------|
| `validationSchemas.ts` | Zod schemas for all form fields |
| `multiStepFormSchemas.ts` | Step-specific validation |

---

## Domain Knowledge (Sri Lanka-Specific)

- **Land Measurement**: Acres-Roods-Perches (A-R-P). Use `backend/app/utils/extent_calculator.py` and `frontend/src/utils/extentCalculator.ts` — never reimplement
- **Administrative Divisions**: 9 provinces, 25 districts, divisional secretariats in `backend/app/administrative_divisions.json`
- **Currency**: Always format as LKR using `frontend/src/utils/currency.ts`
- **Professional Credentials**: IVSL/RICS memberships, post-nominal letters (FRICS, MRICS). Autocomplete data in `backend/app/autocomplete.py`
- **Report Types**: `property` (single), `bare_land` (land only), `multi_property` (portfolio), `vehicle`
- **Valuation Purposes**: `backend/app/constants.py` (ValuationPurpose enum) and `frontend/src/constants/valuationPurposes.ts`

---

## Security Rules (Non-Negotiable)

1. **Ownership Check**: Every endpoint that returns or modifies user data must verify `resource.user_id == current_user.id`
2. **CSRF**: Never disable CSRF middleware. The Axios interceptor in `client.ts` handles this automatically — do not add it manually
3. **Rate Limiting**: Auth: 3-10 req/min; OCR: 10/min; Reports: 30/min — defined in middleware, do not bypass
4. **Token Blacklist**: On logout or token refresh, both access and refresh tokens must be blacklisted via CRUD functions
5. **Password Rules**: 8+ chars, uppercase + lowercase + digit + special character — enforced by Pydantic schema, do not relax
6. **No Secrets in Code**: All keys (Anthropic, Google, SendGrid, DB) must come from environment variables only
7. **Token Storage**: AES-256 encrypted sessionStorage via `secureStorage.ts` — never `localStorage`

### Ownership Pattern
```python
report = db.query(Report).filter(
    Report.id == report_id,
    Report.user_id == current_user.id
).first()
if not report:
    raise HTTPException(status_code=404, detail="Report not found")
```

---

## Database

### Models (SQLAlchemy — `backend/app/models.py`)
- `User` — accounts, OAuth, professional credentials
- `Report` — inherits `PropertyDataMixin` (100+ columns)
- `Property` — inherits `PropertyDataMixin` (used in portfolios)
- `Vehicle` — vehicle specs and valuation
- `ReportProperty` / `ReportVehicle` — junction tables with ordering and overrides
- `TokenBlacklist` — JWT revocation
- `AuditLog` — security event logging
- `Job` — async DOCX generation tracking

### Migrations
- Run via Alembic: `alembic upgrade head`
- `AUTO_MIGRATE=true` env var triggers automatically on startup
- **Never modify an already-applied migration** — always create a new one

---

## AI Integration (Claude)

- **Client**: Singleton in `backend/app/services/anthropic_client.py` — import from here only
- **Model**: `claude-3-5-haiku-20241022` (default for all AI tasks)
- **Uses**:
  - OCR parsing: `services/ai/property_parser.py`, `services/ai/vehicle_parser.py`
  - Narratives: `services/building_narrative.py`, `land_narrative.py`, `locality_narrative.py`
  - Vehicle valuations: `services/ai_valuation.py`
- **Prompt style**: Structured prompts with JSON output — always include a fallback for malformed responses
- **Narrative lengths**: Adapt from 30–140 words based on data richness

---

## DOCX Generation

- All generation is in `backend/app/docx_generation/` (modular, by report type)
- Entry point: `__init__.py` generator registry
- 7 letterhead templates in `backend/app/letterhead_templates/`
- Async generation via `Job` model — use `services/job_service.py` for progress
- **Always** use `safe_get_json_field()` and `to_float()` when reading report data — never assume a field exists

---

## Code Style

### Python
- Type hints on all function signatures
- Pydantic update schemas use `extra='forbid'` to prevent mass-assignment
- Use `Optional[X]` not `X | None` (Python 3.9 compatibility)
- Import order: stdlib → third-party → local app
- Errors via `error_responses.py` — never raw dicts

### TypeScript
- Strict mode — no `any` without an explanatory comment
- `interface` over `type` for object shapes
- Zod schemas for all user-input validation
- All API response types defined in `frontend/src/types/`
- Use `cn()` from `lib/utils.ts` for class merging — never string concatenation

---

## Environment Variables

### Backend (`.env` or Render secrets)
```
DATABASE_URL, SECRET_KEY, REFRESH_TOKEN_SECRET_KEY, REDIS_URL, CORS_ORIGINS
GOOGLE_MAPS_API_KEY, GOOGLE_PLACES_API_KEY, GOOGLE_CLOUD_VISION_API_KEY
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
ANTHROPIC_API_KEY, SENDGRID_API_KEY, EMAIL_FROM, FRONTEND_URL
AUTO_MIGRATE, ENVIRONMENT, SENTRY_DSN, PORT
```

### Frontend (`.env`)
```
VITE_API_URL, VITE_GOOGLE_MAPS_API_KEY, VITE_SENTRY_DSN
```

---

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
pytest tests/
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # Vite dev server
npm run build      # Production build
npm run test       # Vitest
npm run lint       # ESLint
```

---

## CI/CD (GitHub Actions)
- `ci.yml` — Lint + test on every push/PR
- `deploy-backend.yml` — Deploy to Render after CI passes on main
- `deploy-frontend.yml` — Deploy to Vercel after CI passes on main

---

## Things to Never Do

### Structure
- Do NOT create new files without a clear reason that fits the existing architecture
- Do NOT add standalone utility functions outside of `utils/` or `services/`
- Do NOT add types outside of `frontend/src/types/`
- Do NOT add a new router without registering it in `main.py`
- Do NOT add a new DOCX generator without registering it in `docx_generation/__init__.py`
- Do NOT add a new letterhead template without registering it in `letterhead_templates/__init__.py`

### Logic
- Do NOT re-implement A-R-P or LKR utilities — use the existing ones
- Do NOT create a new Anthropic client — import the singleton from `anthropic_client.py`
- Do NOT use `fetch()` in frontend — use `services/api/` methods
- Do NOT put API calls inside React components — put them in hooks
- Do NOT use `useState` for form fields — use React Hook Form

### Security
- Do NOT skip ownership verification on any protected endpoint
- Do NOT disable CSRF middleware or rate limiting
- Do NOT use `localStorage` for tokens — use `secureStorage.ts`
- Do NOT store credentials or API keys in source code
- Do NOT amend already-applied Alembic migrations — create a new one
- Do NOT commit `.env` files (already in `.gitignore`)

### Code Quality
- Do NOT add error handling for scenarios that cannot happen
- Do NOT add speculative features, helpers, or abstractions for hypothetical future use
- Do NOT add backwards-compatibility code when the old code is gone
- Do NOT add docstrings or comments to code you didn't change
- Do NOT leave dead code, unused imports, or commented-out blocks
