# Backend Explanation

A comprehensive technical reference for the Property & Vehicle Valuation Platform backend. This document covers every file, relationship, flow, and architectural decision — everything needed to maintain or recreate the system.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Directory Structure](#2-directory-structure)
3. [Entry Point & App Startup](#3-entry-point--app-startup-appmainpy)
4. [Database Layer](#4-database-layer)
5. [Authentication & Security](#5-authentication--security-appauthpy)
6. [API Endpoints](#6-api-endpoints)
7. [Schemas & Validation](#7-schemas--validation-appschemaspy)
8. [CRUD Operations](#8-crud-operations)
9. [Services Layer](#9-services-layer)
10. [DOCX Generation](#10-docx-generation-appdocx_generatorpy)
11. [Middleware](#11-middleware-appmiddleware)
12. [Utilities](#12-utilities-apputils)
13. [Constants & Autocomplete Data](#13-constants--autocomplete-data)
14. [Maps Service](#14-maps-service-appmaps_servicepy)
15. [Key Business Flows](#15-key-business-flows)
16. [File Relationship Map](#16-file-relationship-map)
17. [Environment Variables Reference](#17-environment-variables-reference)
18. [Deployment & Infrastructure](#18-deployment--infrastructure)
19. [Testing](#19-testing)
20. [For Someone Recreating This Project](#20-for-someone-recreating-this-project)

---

## 1. Project Overview

### What This System Is

A **Property & Vehicle Valuation Platform** built for professional valuers in Sri Lanka. The system automates the creation of formal valuation reports (DOCX format) for properties, bare land, multi-property portfolios, and vehicles. It handles the full lifecycle: data entry, OCR document scanning, AI-assisted narrative generation, Google Maps integration, professional document generation with customizable letterheads, and user/report management.

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI 0.116.1 | Async Python web framework |
| **Database** | PostgreSQL (Neon serverless) | Primary data store |
| **ORM** | SQLAlchemy 2.0.41 | Database abstraction |
| **Migrations** | Alembic 1.16.4 | Schema version control |
| **Cache** | Redis (async) | Rate limiting, caching, login protection |
| **AI** | Claude 3.5 Haiku (Anthropic) | OCR parsing, narratives, valuations |
| **OCR** | Google Cloud Vision | Document text extraction |
| **Maps** | Google Maps APIs | Geocoding, directions, places, static maps |
| **Email** | SendGrid | Transactional emails |
| **Documents** | python-docx, Pillow | DOCX report generation |
| **Auth** | JWT (HS256), bcrypt, OAuth2 | Authentication & authorization |
| **Deployment** | Railway (Nixpacks/Docker) | Cloud hosting |
| **Monitoring** | Sentry | Error tracking |

### High-Level Architecture

```
                                    +------------------+
                                    |   Frontend SPA   |
                                    |   (React/Next)   |
                                    +--------+---------+
                                             |
                                             | HTTPS
                                             |
                              +--------------v--------------+
                              |          FastAPI App         |
                              |                              |
                              |  +--------+  +-----------+   |
                              |  | CORS   |  | Rate Limit|   |
                              |  +--------+  +-----------+   |
                              |  +--------+  +-----------+   |
                              |  | CSRF   |  | Security  |   |
                              |  +--------+  | Headers   |   |
                              |              +-----------+   |
                              +-----+------+------+----------+
                                    |      |      |
                     +--------------+  +---+  +---+-----------+
                     |                 |      |               |
              +------v------+  +------v--+ +-v---------+ +---v--------+
              | PostgreSQL  |  | Redis   | | Google    | | Claude AI  |
              | (Neon)      |  | Cache   | | APIs      | | (Anthropic)|
              |             |  |         | |           | |            |
              | - Users     |  | - Rate  | | - Vision  | | - OCR Parse|
              | - Reports   |  |   Limits| | - Maps    | | - Narrative|
              | - Properties|  | - Login | | - Places  | | - Valuation|
              | - Vehicles  |  |   Limit | | - Geocode | |            |
              | - Jobs      |  | - Cache | | - Direct. | |            |
              | - AuditLogs |  |         | | - Static  | |            |
              +-------------+  +---------+ +-----------+ +------------+
```

---

## 2. Directory Structure

```
backend/
+-- alembic/                          # Database migration system
|   +-- env.py                        # Migration environment config
|   +-- versions/                     # Migration files (6 versions)
|       +-- 001_baseline.py           # Initial schema (all tables)
|       +-- 002_expand_token.py       # Expand password_reset_token column
|       +-- 003_token_blacklist.py    # Add token_blacklist table
|       +-- 004_add_indexes.py        # Performance indexes
|       +-- 005_email_verification.py # Email verification fields
|       +-- 006_oauth_fields.py       # Google OAuth fields
+-- app/
|   +-- __init__.py
|   +-- main.py                       # FastAPI app, all endpoints, middleware, startup
|   +-- database.py                   # SQLAlchemy engine, session management
|   +-- models.py                     # All ORM models (10 models)
|   +-- schemas.py                    # Pydantic schemas & validation (40+ schemas)
|   +-- auth.py                       # JWT, bcrypt, OAuth, RBAC
|   +-- crud.py                       # All CRUD operations (1349 lines)
|   +-- base_crud.py                  # Generic CRUD base class
|   +-- docx_generator.py            # DOCX report generation (6620 lines)
|   +-- maps_service.py              # Google Maps integration (424 lines)
|   +-- constants.py                  # Predefined valuation purposes
|   +-- autocomplete.py              # Professional credentials data (295 lines)
|   +-- administrative_divisions.json # Sri Lankan districts/divisions
|   +-- letterhead_templates/         # Report letterhead designs
|   |   +-- __init__.py              # Template registry (get_template)
|   |   +-- base.py                  # Abstract base template
|   |   +-- classic.py              # Classic design
|   |   +-- compact.py             # Compact design
|   |   +-- executive.py           # Executive design
|   |   +-- minimal.py             # Minimal design
|   |   +-- modern.py              # Modern design
|   |   +-- premium.py             # Premium design
|   +-- middleware/
|   |   +-- __init__.py
|   |   +-- csrf_protection.py     # Double-submit cookie CSRF
|   |   +-- rate_limiting.py       # Token bucket rate limiting
|   +-- services/
|   |   +-- ocr_service.py         # Google Vision OCR pipeline
|   |   +-- ai_parser.py           # Claude AI structured data extraction
|   |   +-- ai_valuation.py        # AI vehicle valuation
|   |   +-- anthropic_client.py    # Singleton Anthropic client
|   |   +-- email_service.py       # SendGrid email service
|   |   +-- file_storage.py        # Ephemeral file storage with TTL
|   |   +-- job_service.py         # Background job processing
|   |   +-- redis_client.py        # Async Redis with fallback
|   |   +-- login_limiter.py       # Brute-force protection
|   |   +-- audit_service.py       # Security event logging
|   |   +-- google_oauth_service.py# Google auth flow
|   |   +-- places_service.py      # Nearby facilities search
|   |   +-- cache_service.py       # API response caching
|   |   +-- access_transformer.py  # Route-to-text transformation
|   |   +-- building_narrative.py  # AI building descriptions
|   |   +-- land_narrative.py      # AI land descriptions
|   |   +-- locality_narrative.py  # AI locality descriptions
|   |   +-- base_narrative.py      # Narrative base class
|   |   +-- narrative_constants.py # Shared narrative constants
|   +-- utils/
|       +-- extent_calculator.py   # Sri Lankan land measurements
|       +-- text_helpers.py        # Spelling corrections, labels
|       +-- error_responses.py     # Standardized error format
|       +-- json_validators.py     # JSON schema validation
|       +-- api_client.py          # HTTP client with circuit breaker
|       +-- fallbacks.py           # Graceful degradation defaults
+-- tests/
|   +-- conftest.py                # Test fixtures
|   +-- test_auth.py              # Authentication tests (471 lines)
|   +-- test_bare_land.py         # Bare land report tests (310 lines)
+-- alembic.ini                    # Alembic configuration
+-- requirements.txt               # Python dependencies (78 packages)
+-- Dockerfile                     # Container specification
+-- railway.json                   # Railway deployment config
+-- nixpacks.toml                  # Nixpacks build config
+-- Procfile                       # Heroku-style process file
+-- pytest.ini                     # Test runner configuration
```

---

## 3. Entry Point & App Startup (`app/main.py`)

### How the Server Starts

The application runs via **Uvicorn** ASGI server:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The FastAPI app instance is created in `main.py` with OpenAPI docs, CORS, and all middleware configured.

### Middleware Stack (Applied in Order)

Middleware executes in **reverse registration order** for requests (last registered = first to execute):

1. **CORS Middleware** — Handles cross-origin requests
   - Origins: from `CORS_ORIGINS` env variable
   - Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
   - Headers: Content-Type, Authorization, Accept, Origin, X-Requested-With, X-CSRF-Token
   - Credentials: Allowed

2. **Rate Limiting Middleware** — Token bucket per endpoint
   - Auth endpoints: 3-10 req/min
   - OCR endpoints: 10 req/min
   - Report endpoints: 30 req/min
   - Maps endpoints: 60 req/min

3. **CSRF Protection Middleware** — Double-submit cookie pattern
   - Validates X-CSRF-Token header against csrf_token cookie
   - Exempt: login, register, forgot-password, health, docs

4. **Security Headers Middleware** — Applied to all responses
   - Content-Security-Policy (restrictive)
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Referrer-Policy: strict-origin-when-cross-origin
   - HSTS (production only)

5. **Request ID Middleware** — Unique X-Request-ID per request for tracing

### Startup Events (`@app.on_event("startup")`)

1. **Auto-migrate database** — If `AUTO_MIGRATE=true`, runs Alembic migrations
2. **Configure rate limits** — Sets per-endpoint rate limit rules
3. **Initialize Redis** — Connects to Redis (required in production)
4. **Start background tasks**:
   - Periodic token bucket cleanup (hourly)
   - Expired token blacklist cleanup
   - Expired file storage cleanup

### Shutdown Events (`@app.on_event("shutdown")`)

1. Close Redis connection
2. Close database connections
3. Wait for pending async tasks (5-second timeout)

### File Upload Validation

The `validate_upload_file()` function enforces:
- **Max file size**: 10MB per file
- **Max files per upload**: 10
- **Extension whitelist**: .jpg, .jpeg, .jfif, .png, .webp, .pdf
- **Magic number verification**: Checks actual file bytes against declared content type (prevents spoofing)

---

## 4. Database Layer

### `app/database.py` — Connection Pooling & Session Management

**Engine Configuration**:
| Setting | Value | Purpose |
|---------|-------|---------|
| pool_pre_ping | True | Tests connections before use |
| pool_size | 10 | Base connection pool |
| max_overflow | 20 | Additional connections beyond pool_size |
| pool_recycle | 3600 | Recycles connections every hour |
| connect_args.connect_timeout | 10 | Connection timeout in seconds |

**Session Management** (`get_db()` dependency):
- Yields SQLAlchemy Session with `autocommit=False`, `autoflush=False`
- Handles `DisconnectionError` with rollback and reconnection
- Always closes session in `finally` block

### `app/models.py` — All Database Models

#### Model Relationship Diagram (ERD)

```
  +----------+       +----------------+       +------------+
  |  users   |<------| reports        |------>| vehicles   |
  |----------|  1:N  |----------------|  N:1  |------------|
  | id (PK)  |       | id (PK)        |       | id (PK)    |
  | email    |       | user_id (FK)   |       | user_id(FK)|
  | password |       | report_type    |       | make       |
  | role     |       | status         |       | model      |
  | ...      |       | primary_vehicle|       | reg_number |
  +----+-----+       | _id (FK)       |       | ...        |
       |              +---+------+-----+       +-----+------+
       |                  |      |                    |
       |          +-------+      +--------+           |
       |          |                       |           |
       |   +------v--------+    +--------v--------+  |
       |   |report_properties|  |report_vehicles   |  |
       |   |  (junction)    |    | (junction)      |  |
       |   |----------------|    |-----------------|  |
       |   | id (PK)        |    | id (PK)         |  |
       |   | report_id (FK) |    | report_id (FK)  |  |
       |   | property_id(FK)|    | vehicle_id (FK)-+--+
       |   | property_order |    | vehicle_order   |
       |   +------+---------+    +-----------------+
       |          |
       |   +------v--------+
       |   | properties    |
       |   |---------------|
       |   | id (PK)       |
       |   | user_id (FK)  |
       +-->| status        |
           | is_template   |
           | ...           |
           +---------------+

  +------------------+       +------------------+
  | token_blacklist  |       | audit_logs       |
  |------------------|       |------------------|
  | id (PK)          |       | id (PK)          |
  | jti (UNIQUE)     |       | user_id (FK)     |
  | user_id (FK)     |       | action           |
  | token_type       |       | resource_type    |
  | expires_at       |       | resource_id      |
  | revoked_at       |       | ip_address       |
  +------------------+       | created_at       |
                             +------------------+

  +------------------+
  | jobs             |
  |------------------|
  | id (PK, UUID)    |
  | user_id (FK)     |
  | report_id (FK)   |
  | job_type         |
  | status           |
  | result_url       |
  | progress_percent |
  +------------------+
```

#### User Model (`users` table)

| Field | Type | Constraints |
|-------|------|-------------|
| id | Integer | PK, auto-increment |
| email | String(255) | UNIQUE, NOT NULL |
| password_hash | String(255) | NOT NULL |
| honorific | String(10) | Nullable (Mr., Mrs., Dr., etc.) |
| full_name | String(255) | NOT NULL |
| phone | String(50) | Nullable |
| role | String(20) | NOT NULL, default='user' |
| email_verified | Boolean | NOT NULL, default=False |
| email_verification_token | String(255) | Nullable |
| email_verification_expires | DateTime(tz) | Nullable |
| google_id | String(255) | UNIQUE, Nullable |
| oauth_provider | String(50) | Nullable |
| password_reset_token | String(255) | Nullable |
| password_reset_expires | DateTime(tz) | Nullable |
| academic_qualifications | Text | Nullable |
| membership_level | String(100) | Nullable |
| membership_number | String(100) | Nullable |
| professional_designation | String(200) | Nullable |
| panel_valuer_banks | JSON | Array of bank names |
| house_number, area_development, village, locality | String | Address fields |
| phone_primary, phone_secondary | String(50) | Contact numbers |
| office_department, office_region, office_street_city, office_phone | String | Office info |
| preferred_letterhead_template | String(50) | Default='classic' |
| bank_accounts | JSON | Array of bank account objects |
| created_at, updated_at | DateTime(tz) | Timestamps |

**Relationships**: reports (1:N), properties (1:N), vehicles (1:N)

#### PropertyDataMixin (~132 shared columns)

Shared by both `Report` and `Property` models. Covers:

- **Property Identification**: lot_number, plan_number, plan_date, licensed_surveyor_name, deeds (JSON)
- **Location**: property_village, property_divisional_secretariat, property_district, property_province, property_latitude/longitude
- **Access Directions**: access_starting_point, access_route_data (JSON), access_directions_text, access_distance_km, access_road_conditions (JSON)
- **Land Extent**: acres, roods, perches, hectares, square_meters, land_extent_formatted
- **Boundaries**: boundaries (JSON - 8 directions), physical_boundaries_types, entrance_type
- **Land Description**: shape, type, frontage, level, soil_type, flood/inundation/earth_slip risk, elevation, drainage, vegetation
- **Buildings**: buildings (JSON array of building objects with floors, rooms, materials, photos)
- **Locality**: distance_to_major_town, nearby_facilities (JSON), infrastructure, transport
- **Legal**: ownership_type, street_lines_status, building_limits, encumbrances, plan approvals
- **Valuation**: land_extent, rate_per_perch, total_land_value, buildings_data, addons, market_value, forced_sale_value, insurance_value

#### Report Model (`reports` table)

Inherits all PropertyDataMixin fields, plus:

| Field | Type | Purpose |
|-------|------|---------|
| report_type | String(100) | Default='residential_property' |
| status | String(50) | Default='draft' |
| applicant_title/full_name/id_type/id_number | String | Applicant info |
| request_type | String(50) | 'client_request' or 'organization_request' |
| valuation_type/purpose | String | Valuation context |
| is_multi_property | Boolean | Default=False |
| property_count | Integer | Default=1 |
| total_valuation_amount | Numeric(15,2) | Aggregate for multi-property |
| primary_vehicle_id | Integer FK | For vehicle reports |
| vehicle_count | Integer | Number of vehicles |
| invoice_data | JSON | Invoice details |
| certification_text/valuer_name/date | Various | Certification section |

**Relationships**: user, property_associations (ReportProperty), vehicle_associations (ReportVehicle), primary_vehicle

#### Property Model (`properties` table)

Inherits all PropertyDataMixin fields, plus:

| Field | Type | Purpose |
|-------|------|---------|
| property_type | String(50) | Default='residential' |
| property_owner_title/full_name/id_type/id_number | String | Owner info |
| is_template | Boolean | Property library support |
| template_name | String(200) | Template identifier |
| last_valued_date | String(50) | Last valuation |

#### Vehicle Model (`vehicles` table)

| Category | Fields |
|----------|--------|
| **Identification** | registration_number, chassis_number, engine_number, provincial_council, class_of_vehicle |
| **Specs** | make, model, year_of_manufacture, cylinder_capacity, fuel_type, engine_type, transmission |
| **Condition** | running_condition, clutch_status, engine_condition, gear_box_condition, body_condition, chassis_condition |
| **Brakes** | foot_brake_condition, parking_brake_condition, abs_available, disc_brake_available |
| **Complex JSON** | features, suspension, tyres, electrical, lights |
| **History** | has_accidents, has_repairs, body_parts_replaced |
| **Valuation** | purchase_price, brand_new_price, market_value, forced_sale_value, valuation_summary |
| **Photos** | vehicle_photos (JSON), book_images (JSON for OCR) |
| **Meta** | is_template, is_deleted (soft delete), original_vehicle_id (for duplicates) |

**Unique Constraint**: (user_id, registration_number) per user

#### Junction Tables

**ReportProperty** (`report_properties`): report_id, property_id, property_order, override_market_value, override_forced_sale_value

**ReportVehicle** (`report_vehicles`): report_id, vehicle_id, vehicle_order, override_market_value

#### TokenBlacklist (`token_blacklist`)

Stores revoked JWT tokens by their JTI claim. Fields: jti (UNIQUE), user_id, token_type, expires_at, revoked_at.

#### AuditLog (`audit_logs`)

Security event logging. Fields: user_id, action, resource_type, resource_id, description, details (JSON), ip_address, user_agent, request_id, success, error_message.

#### Job (`jobs`)

Async job tracking. Fields: id (UUID), user_id, report_id, job_type, status, result_url, result_filename, progress_percent, progress_message, timestamps.

### Alembic Migrations

| # | Revision | Date | Description |
|---|----------|------|-------------|
| 1 | 001_baseline | 2026-02-03 | Initial schema — all tables (users, reports, properties, vehicles, jobs, report_properties, report_vehicles, audit_logs) |
| 2 | 002_expand_token | 2026-02-03 | Expand password_reset_token String(100) to String(255) for bcrypt hashes |
| 3 | 003_token_blacklist | 2026-02-03 | Add token_blacklist table for JWT revocation/logout |
| 4 | 004_add_indexes | 2026-02-03 | Add indexes on reports.report_type, reports.status, reports.created_at, report_vehicles.report_id/vehicle_id |
| 5 | 005_email_verification | 2026-02-06 | Add email_verified, email_verification_token, email_verification_expires to users |
| 6 | 006_oauth_fields | 2026-02-06 | Add google_id, oauth_provider to users (with unique index on google_id) |

**Migration Config** (`alembic/env.py`):
- Loads `.env` and `.env.local` files
- Uses NullPool for Neon serverless PostgreSQL
- Imports `Base.metadata` from models for autogenerate support
- Compare type and server default changes enabled

---

## 5. Authentication & Security (`app/auth.py`)

### Password Hashing

- **Algorithm**: bcrypt via `passlib.CryptContext`
- **Functions**: `get_password_hash()`, `verify_password()`

### Password Validation Rules

`validate_password_strength()` enforces:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character (`!@#$%^&*()_+-=[]{}|;:,.<>?`)
- Not in common passwords blacklist (~50 entries: password, 123456, qwerty, admin, etc.)

### JWT Token System

| Token Type | Secret | Lifetime | Purpose |
|-----------|--------|----------|---------|
| Access | `SECRET_KEY` | 30 minutes | API authentication |
| Refresh | `REFRESH_TOKEN_SECRET_KEY` | 4 hours | Token renewal with rotation |

Both tokens include a **JTI** (JWT ID) for revocation support.

**Token Flow**:
1. Login returns access token + refresh token (in HttpOnly cookie)
2. Access token used for API calls via Bearer header or cookie
3. When access token expires, client calls `/api/auth/refresh`
4. Refresh endpoint issues new access token + rotated refresh token
5. Old refresh token is blacklisted

### Token Blacklist

When a user logs out or a refresh token is rotated, the token's JTI is stored in the `token_blacklist` table. Every authenticated request checks whether the presented token's JTI has been revoked.

### HttpOnly Cookies

Access tokens are set as HttpOnly cookies (JS cannot read them). The `get_current_user` dependency checks the cookie first, then falls back to the Authorization header.

### Role-Based Access Control

Two roles: `user` and `admin`.

- `get_current_user()` — Extracts and validates the authenticated user
- `require_admin()` — Dependency that raises 403 if `user.role != 'admin'`

### Google OAuth Flow

1. Frontend calls `GET /api/auth/google/authorize` to get the Google auth URL
2. User authenticates with Google
3. Frontend receives auth code, sends to `POST /api/auth/google/callback`
4. Backend exchanges code for tokens, fetches user info from Google
5. Creates new user or links Google to existing account (by email match)
6. Returns JWT tokens

OAuth users have `email_verified=True` automatically (Google pre-verified).

---

## 6. API Endpoints

All 70+ endpoints from `app/main.py`, grouped by category.

### Health & System

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/` | None | Root health check |
| GET | `/api/health` | None | Basic health check |
| GET | `/api/health/detailed` | None | DB, Redis, API status |
| GET | `/api/csrf-token` | None | Get CSRF token |

### Authentication

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/auth/register` | None | Register new user |
| POST | `/api/auth/login` | None | Login, returns tokens |
| POST | `/api/auth/refresh` | None | Refresh access token (with rotation) |
| GET | `/api/auth/me` | Required | Get current user info |
| POST | `/api/auth/logout` | Optional | Logout, revoke tokens |
| POST | `/api/auth/forgot-password` | None | Request password reset email |
| POST | `/api/auth/reset-password` | None | Reset password with token |
| POST | `/api/auth/send-verification` | Required | Resend verification email |
| POST | `/api/auth/verify-email` | None | Verify email with token |
| GET | `/api/auth/google/authorize` | None | Get Google OAuth URL |
| POST | `/api/auth/google/callback` | None | Handle Google OAuth callback |

### Admin

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/admin/users` | Admin | List all users (paginated) |
| GET | `/api/admin/users/{user_id}` | Admin | Get specific user |
| PATCH | `/api/admin/users/{user_id}/role` | Admin | Change user role |

### User Profile

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| PUT | `/api/profile` | Required | Update user profile |
| GET | `/api/users/me/bank-accounts` | Required | List bank accounts |
| POST | `/api/users/me/bank-accounts` | Required | Add bank account |
| PATCH | `/api/users/me/bank-accounts/{id}` | Required | Update bank account |
| DELETE | `/api/users/me/bank-accounts/{id}` | Required | Delete bank account |
| GET | `/api/letterhead-templates` | Required | Get available templates |

### Reports

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/reports` | Required | Create new report |
| GET | `/api/reports` | Required | Get paginated reports (filters: reference, applicant_name, village, report_date) |
| GET | `/api/reports/adjacent-date` | Required | Get next/previous date with reports |
| GET | `/api/reports/{id}` | Required | Get specific report |
| PUT | `/api/reports/{id}` | Required | Update report |
| DELETE | `/api/reports/{id}` | Required | Delete report |
| POST | `/api/reports/{id}/duplicate` | Required | Duplicate report |

### DOCX Generation & Jobs

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/reports/{id}/generate` | Required | Sync DOCX generation (streaming download) |
| POST | `/api/reports/{id}/generate-async` | Required | Start async DOCX generation job |
| GET | `/api/jobs/{job_id}` | Required | Get job status/progress |
| GET | `/api/jobs/{job_id}/download` | Required | Download completed file |
| GET | `/api/jobs` | Required | List user's recent jobs |

### Properties

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/properties` | Required | Create property |
| GET | `/api/properties` | Required | List user's properties |
| GET | `/api/properties/templates` | Required | List property templates (library) |
| GET | `/api/properties/{id}` | Required | Get specific property |
| PUT | `/api/properties/{id}` | Required | Update property |
| DELETE | `/api/properties/{id}` | Required | Delete property (if not in reports) |
| PATCH | `/api/properties/{id}/status` | Required | Update property status |

### Multi-Property Report Operations

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/reports/multi-property` | Required | Create multi-property report |
| GET | `/api/reports/{id}/properties` | Required | Get report's properties |
| POST | `/api/reports/{id}/properties/{pid}` | Required | Add property to report |
| DELETE | `/api/reports/{id}/properties/{pid}` | Required | Remove property from report |
| PUT | `/api/reports/{id}/properties/reorder` | Required | Reorder properties (drag-drop) |
| PUT | `/api/reports/{id}/properties/{pid}` | Required | Update property within report |
| POST | `/api/reports/{id}/properties/{pid}/duplicate` | Required | Duplicate property in report |

### Vehicles

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/vehicles` | Required | Create vehicle |
| GET | `/api/vehicles` | Required | List user's vehicles |
| GET | `/api/vehicles/templates` | Required | List vehicle templates (library) |
| GET | `/api/vehicles/{id}` | Required | Get specific vehicle |
| PUT | `/api/vehicles/{id}` | Required | Update vehicle |
| DELETE | `/api/vehicles/{id}` | Required | Delete vehicle (soft/hard) |
| POST | `/api/vehicles/{id}/duplicate` | Required | Duplicate vehicle |
| POST | `/api/vehicles/{id}/suggest-valuation` | Required | Get AI valuation suggestion |

### Report-Vehicle Operations

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/reports/{id}/vehicles` | Required | Get report's vehicles |
| POST | `/api/reports/{id}/vehicles/{vid}` | Required | Add vehicle to report |
| DELETE | `/api/reports/{id}/vehicles/{vid}` | Required | Remove vehicle from report |
| PUT | `/api/reports/{id}/vehicles/reorder` | Required | Reorder vehicles |
| PUT | `/api/reports/{id}/vehicles/{vid}` | Required | Update vehicle in report |

### OCR & AI

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/ocr/extract` | Required | Extract data from documents (images/PDF) via OCR + AI |

### Autocomplete & Data

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/autocomplete` | None | Get all autocomplete data |
| GET | `/api/autocomplete/{category}` | None | Search within category |
| GET | `/api/administrative-divisions` | None | Get Sri Lankan districts/divisions |
| GET | `/api/administrative-divisions/{district}` | None | Get DS divisions for district |

### Google Maps Proxy

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/maps/geocode` | None | Geocode address to coordinates |
| POST | `/api/maps/places/autocomplete` | None | Place suggestions |
| POST | `/api/maps/places/details` | None | Place details from place_id |

---

## 7. Schemas & Validation (`app/schemas.py`)

### Validation Helper Functions

| Function | Purpose |
|----------|---------|
| `validate_password_strength()` | 8+ chars, upper, lower, digit, special, not common |
| `validate_sri_lankan_nic()` | Old: 9 digits + V/X; New: 12 digits |
| `validate_passport()` | 6-12 alphanumeric characters |
| `validate_date_format()` | DD-MM-YYYY with leap year awareness |
| `normalize_date_format()` | Converts DD/MM/YYYY, DD.MM.YYYY, YYYY-MM-DD to DD-MM-YYYY |
| `sanitize_dangerous_characters()` | Removes `<>{}();` |

### Key Schema Groups

**Authentication**: UserBase, UserCreate, UserLogin, UserResponse, UserUpdate, TokenResponse, RefreshTokenRequest

**Bank Accounts**: BankAccount, BankAccountCreate, BankAccountUpdate

**Buildings**: RoofDetails, WallDetails, FloorDetails, DoorsWindowsDetails, AccommodationSummary, ConstructionMaterials, UtilitiesServices, Room, Floor, Building, BuildingPhoto

**Reports**: ReportBase (combines all field group mixins, ~150+ fields), ReportCreate, ReportUpdate, ReportResponse, PaginatedReportResponse, ReportStats

**Properties**: PropertyBase, PropertyCreate, PropertyUpdate, PropertyResponse, PropertyTemplateResponse, PropertyStatusUpdate

**Vehicles**: VehicleCreate, VehicleUpdate, VehicleResponse, VehicleTemplateResponse, VehicleValuationSuggestion

**Multi-Property**: MultiPropertyReportCreate, MultiPropertyReportResponse

**Junction**: ReportPropertyBase, ReportPropertyCreate, ReportPropertyResponse, ReportVehicleResponse

**Invoice**: InvoiceItem, InvoiceData

### Field Validators (on ReportBase)

1. `applicant_full_name` / `plan_number` — Sanitize dangerous characters
2. `applicant_id_number` — Validate based on applicant_id_type (NIC, passport)
3. `plan_date`, `report_date`, `certification_date` — Normalize and validate DD-MM-YYYY
4. `property_latitude` — Range [-90, 90]
5. `property_longitude` — Range [-180, 180]
6. `land_extent_acres` — Non-negative
7. `boundaries`, `buildings`, `deeds`, `nearby_facilities` — JSON schema validation
8. `property_photos`, `access_road_conditions` — JSON validation
9. `water_supply_type`, `predominant_building_type` — Max 5 items, case-insensitive dedup
10. Boolean-to-string conversion: `has_deed_info`, `has_special_note` convert `true`/`false` to `"yes"`/`"no"`

### SQL Injection Prevention

The `ReportUpdateRequest` schema uses `Config: extra='forbid'` which prevents any extra fields from being passed, blocking field injection attacks.

---

## 8. CRUD Operations

### `app/base_crud.py` — Generic CRUD Pattern

The `BaseCRUD` class provides reusable CRUD operations with ownership verification:

```python
class BaseCRUD:
    def __init__(self, model, entity_name)
    def create(self, db, data, user_id, **extra_fields)
    def get(self, db, entity_id, user_id)
    def get_user_list(self, db, user_id, skip, limit)
    def update(self, db, entity_id, user_id, data)
    def delete(self, db, entity_id, user_id)
```

Used as: `report_crud = BaseCRUD(models.Report, "Report")`

### `app/crud.py` — Full CRUD Operations (1349 lines)

#### User Operations
- `create_user()` — Hash password, create user
- `get_user()` / `get_user_by_email()` — Lookup
- `update_user()` — Partial update (exclude_unset)

#### Bank Account Operations
- `add_bank_account()` — Append to user.bank_accounts JSON array with UUID
- `update_bank_account()` / `delete_bank_account()` — Modify array

#### Report Operations
- `create_report()` — Validate building photos, create
- `get_report()` — Optional eager loading for DOCX generation (joins user, vehicles, properties in single query)
- `get_user_reports_filtered()` — Paginated with ILIKE filters and stats (total, this_month, completed, draft counts)
- `get_adjacent_report_date()` — Date navigation for filter UI
- `update_report()` — Optional pessimistic locking (`SELECT FOR UPDATE`)
- `duplicate_report()` — Reflection-based deep copy, resets certification/status fields, duplicates multi-property associations
- `delete_report()`

#### Property Operations
- `create_property()` / `get_property()` / `update_property()`
- `get_property_templates()` — Property library (is_template=True)
- `delete_property()` — Cannot delete if used in any report (checks ReportProperty junction)
- `duplicate_property()` — Deep copy within report, handles property_order, updates report metadata
- `update_property_status()` — Toggle between 'draft' and 'completed'

#### Multi-Property Operations
- `create_multi_property_report()` — Atomic transaction: creates report + links existing/new properties
- `add_property_to_report()` / `remove_property_from_report()` — Junction management with auto property_count/total_valuation updates
- `reorder_report_properties()` — Drag-drop support
- `_update_report_total_valuation()` — Recalculates with `SELECT FOR UPDATE` to prevent race conditions

#### Vehicle Operations
- `create_vehicle()` / `get_vehicle()` — Filters out soft-deleted vehicles
- `get_vehicle_templates()` — Vehicle library
- `delete_vehicle()` — Soft delete by default; hard delete blocked if used in reports
- `duplicate_vehicle()` — Copies all 50+ fields including JSON fields

#### Report-Vehicle Junction Operations
- `add_vehicle_to_report()` / `remove_vehicle_from_report()`
- `reorder_report_vehicles()`
- `_update_report_total_valuation_with_vehicles()` — Sums both property and vehicle valuations

#### Key Implementation Pattern: Reflection-Based Duplication

```python
def _duplicate_entity_data(entity, exclude_fields=None, override_fields=None):
    """Uses SQLAlchemy inspection to auto-copy all columns"""
    # Eliminates manual field mappings that become outdated
    # Deep copies mutable types (dict, list)
```

---

## 9. Services Layer

### `app/services/ocr_service.py` — Google Vision OCR Pipeline

**Purpose**: Extract text from uploaded documents (survey plans, deeds, title certificates) using Google Cloud Vision.

**Pipeline**:
1. Read uploaded file bytes, determine media type
2. Call Google Vision API `document_text_detection` (or `text_detection` fallback)
3. Return raw OCR text with confidence scores
4. Process multiple documents: call `ai_parser.py` to structure the extracted text

**Key Functions**:
- `process_uploaded_document()` — Single document OCR
- `process_multiple_documents()` — Multi-file batch processing with merged results
- `extract_text_from_image()` — Google Vision API call

### `app/services/ai_parser.py` — Claude AI Structured Data Extraction

**Purpose**: Parse unstructured OCR text into structured property data fields.

**Key Functions**:
- `parse_with_claude()` — Send OCR text to Claude, get structured JSON
- `parse_property_data_from_text()` — Main parsing with schema-aware prompt
- `merge_extracted_data()` — Combine results from multiple documents (highest confidence wins)

**Extraction Targets**: plan_number, plan_date, lot_number, licensed_surveyor_name, boundaries, land_extent (A-R-P), deed information, property location

**AI Details**: Claude 3.5 Haiku, temperature 0.2 (deterministic), structured JSON output

### `app/services/ai_valuation.py` — AI Vehicle Valuation

**Purpose**: Generate AI-powered market value estimates for vehicles.

**Key Function**: `suggest_vehicle_valuation()` — Takes vehicle data, returns:
- `suggested_market_value`, `suggested_forced_sale_value`, `suggested_brand_new_price`
- `valuation_summary` (professional text)
- `confidence` (0.0-1.0), `reasoning`

**Factors Considered**: Age depreciation (10-15%/year first 5 years), mileage, condition ratings (7 fields + brakes), parts availability, accident history (20-30% reduction), fuel type.

### `app/services/anthropic_client.py` — Singleton Anthropic Client

Provides `get_anthropic_client()` cached via `lru_cache(maxsize=1)`. Loads API key from environment. `is_anthropic_configured()` checks key availability.

### `app/services/email_service.py` — SendGrid Email Service

**Functions**:
- `send_email()` — Generic sender
- `send_password_reset_email()` — Reset link with 1-hour expiry
- `send_welcome_email()` — New user welcome
- `send_verification_email()` — Email verification with 24-hour expiry

Graceful failure: logs warning if SendGrid not configured, returns False.

### `app/services/file_storage.py` — Ephemeral File Storage

**Purpose**: Temporary file storage for Railway deployment (ephemeral filesystem).

- `store_file()` — Generate UUID, store in `/tmp/valuation-files` with `.meta` companion file
- `get_file()` — Retrieve by ID, check TTL (default 1 hour)
- `cleanup_expired_files()` — Batch delete files past TTL
- `get_storage_stats()` — File count, size, expired count

### `app/services/job_service.py` — Background Job Processing

**Purpose**: Async DOCX generation with progress tracking.

**Flow**:
1. `create_job()` — Create Job record (status=PENDING)
2. `process_docx_job()` — Background task:
   - 10% → Start
   - 30% → Load report/user data
   - 50% → Generate DOCX
   - 80% → Store file
   - 100% → Complete
3. Frontend polls `get_job()` for status
4. `cleanup_old_jobs()` — Remove jobs older than 24h

### `app/services/redis_client.py` — Async Redis with Fallback

- `get_redis_client()` — Async singleton with connection pool (max 10 connections)
- **Production**: Redis required (raises RuntimeError if REDIS_URL missing)
- **Development**: Falls back to None (in-memory alternatives)
- `RedisCache` class: get/set/delete/exists/incr/expire + JSON support with graceful error handling

### `app/services/login_limiter.py` — Brute-Force Protection

- `check_rate_limit()` — Returns (is_allowed, remaining_attempts)
- `record_failed_attempt()` — MAX_ATTEMPTS=5, LOCKOUT_SECONDS=900 (15 min)
- Key format: `login_attempts:{ip}:{email_normalized}`
- Fails open if Redis down (development-friendly)

### `app/services/audit_service.py` — Security Event Logging

- `log()` — Main audit function: user_id, action, resource_type/id, IP, user-agent, request_id
- Specialized: `log_login()`, `log_password_change()`, `log_role_change()`, `log_resource_delete()`, `log_bank_account_change()`
- Non-blocking: failures don't break the application

### `app/services/google_oauth_service.py` — Google OAuth Flow

- `get_authorization_url()` — Generate Google auth URL (scope: openid email profile)
- `get_token_and_user_info()` — Exchange auth code for tokens + user info
- `create_or_link_user()` — Create new user or link Google to existing account (by email match)

### `app/services/places_service.py` — Nearby Facilities Search

- `fetch_nearby_facilities()` — Google Places Nearby Search for 11 facility types (hospitals, schools, banks, etc.)
- `get_distance_to_major_town()` — Distance calculation
- `find_nearest_transport()` — Nearest bus stop (2km) and railway station (10km)
- `haversine_distance()` — Great-circle distance calculation

### `app/services/cache_service.py` — Redis Caching Layer

| Cache | Key Pattern | TTL |
|-------|------------|-----|
| Geocoding | `geo:reverse:{lat}:{lng}` | 24 hours |
| Places Nearby | `places:nearby:{lat}:{lng}:{type}` | 1 hour |
| Place Details | `places:details:{place_id}` | 24 hours |
| Directions | `directions:{origin}:{dest}` | 24 hours |

Coordinates rounded to reduce cache misses (6 decimals for geocoding, 4 for places).

### `app/services/access_transformer.py` — Route-to-Text Transformation

- `transform_directions_to_professional()` — Convert Google Maps steps to professional prose
- Uses Claude 3.5 Haiku (temperature 0.5) with validation for hallucinated distances
- `generate_fallback_access_text()` — Template-based fallback if AI fails
- Road classification detection (Class A/B/C) for backend analytics

### Narrative Generation Services

All narrative services extend `BaseNarrativeService` (abstract base) which provides:
- Anthropic client integration
- Standard generate() method with prompt building and error handling
- Default model: Claude 3.5 Haiku

**`building_narrative.py`** — Generates ~150 word professional building descriptions. Covers: construction materials, accommodation layout, utilities, condition.

**`land_narrative.py`** — Adaptive-length land descriptions:
- Minimal (1-3 fields): 30-50 words
- Moderate (4-6 fields): 60-90 words
- Rich (7+ fields): 100-140 words

**`locality_narrative.py`** — 150-200 word locality descriptions covering area character, facilities, infrastructure, transport. Max tokens: 1024.

**`narrative_constants.py`** — Shared constants including `format_water_supply()` for normalizing water supply labels.

---

## 10. DOCX Generation (`app/docx_generator.py`)

The largest file in the codebase at **6620 lines**. Generates professional Word documents.

### Safe Data Access Pattern

Five defensive helper functions prevent crashes from null/missing data:

```python
to_float(value)              # Any value -> float, default 0.0
safe_get_json_field(obj, field)  # Safe attribute access
safe_get_array_item(arr, index)  # Bounds-checked array access
safe_parse_json_string(json_str) # Safe JSON parsing
safe_get_nested(obj, *keys)      # Deep nested dict traversal
```

### Document Type Constants

```
Font Sizes: Title=14pt, Section=13pt, Subsection=12pt, Body=12pt, Table=11pt, Caption=10pt
Image: Map=3.5"x2.75", Photos=2.0"x2.0"
Spacing: Major section before=10pt, Subsection=8pt, Body after=3pt
```

### Three Main Generation Functions

#### 1. `generate_multi_property_report_docx(report, user) -> BytesIO`

For multi-property valuation reports:

1. **Letterhead** — User's preferred template
2. **Title** — "VALUATION REPORT"
3. **Applicant Statement** — Client or organization format based on request_type
4. **Summary Page** — List of completed properties with totals
5. **Per-Property Sections** (for each completed property):
   - Property identification (plan, lot, surveyor)
   - Situation and location
   - Access directions (from Google Maps or manual)
   - Boundaries
   - Land extent and description
   - Building details with photos and construction materials
   - Locality and infrastructure
   - Legal aspects (ownership, street lines, building limits)
   - Comparable properties and market analysis
   - Valuation calculation
   - Certification (per-property, allows different valuers)
6. **Invoice Section** — Professional fees with bank details

Only properties with `status='completed'` are included; drafts are excluded.

#### 2. `generate_vehicle_report_docx(report, user) -> BytesIO`

For vehicle valuation reports:

1. **Letterhead**
2. **Title** — "VEHICLE VALUATION REPORT"
3. **Header Table** — Purpose, applicant, dates, folio number
4. **Vehicle Identification** — 14-row table (registration, make, model, chassis, engine, etc.)
5. **Condition Assessment** — Running condition, brakes, engine, body
6. **Features** — A/C, power windows, airbags, ABS
7. **Tyres** — Front/rear condition, spare availability
8. **Valuation** — Purchase price, market value, forced sale value, summary
9. **Vehicle Photos** — Embedded images
10. **Signature Block**

#### 3. `generate_user_data_docx(report, user) -> BytesIO`

Exports all user-entered data for verification/backup.

### 50+ Narrative Generation Functions

**Legal Paragraphs**:
- `generate_ownership_paragraph()` — Deed-based ownership with encumbrance status
- `generate_street_lines_paragraph()` — Street line regulations with gazette references
- `generate_building_limits_paragraph()` — Plan approval status, distance from road
- `generate_local_authority_paragraph()` — Pradeshiya Sabha, rating, tax levy
- `generate_rent_act_paragraph()` — Rent act applicability

**Location & Direction**:
- `generate_situation_text()` — Comprehensive location narrative
- `generate_smart_address()` — Address synthesis from available fields
- `generate_access_text()` — Professional access description
- `generate_locality_description()` — Neighborhood description
- `generate_boundary_summary_text()` — Directional boundary listing

**Valuation**:
- `generate_land_values_paragraph()` — Market analysis from comparables
- `_synthesize_location_context()` — Pattern extraction from comparable locations

**Certification & Identity**:
- `generate_simplified_certification_text()` — Professional certification statement
- `generate_certificate_of_identity_text()` — Identity confirmation certificate
- `add_signature_block()` — Blank signature line with credentials

### Letterhead Template System (`app/letterhead_templates/`)

7 templates implementing `render_letterhead(doc, user, report)`:

| Template | Style |
|----------|-------|
| classic | Traditional professional layout |
| compact | Minimal spacing, condensed |
| executive | Premium appearance, larger logos |
| minimal | Text-only, bare essentials |
| modern | Contemporary with color accents |
| premium | Highest visual appeal, decorative elements |

Template selected via `user.preferred_letterhead_template` (default: 'classic').

### Currency Formatting

```python
format_currency(1500000)           # "Rs. 1,500,000.00"
format_currency_words(1500000)     # "One Million Five Hundred Thousand"
format_currency_aligned(1500000)   # Right-padded for table alignment
round_for_say(1567000)             # 1,550,000 (round to nearest 50K for >= 1M)
```

---

## 11. Middleware (`app/middleware/`)

### `csrf_protection.py` — Double-Submit Cookie CSRF

**Mechanism**: Cryptographically secure token (32 bytes URL-safe) set as cookie and validated against X-CSRF-Token header on state-changing requests.

- **Cookie**: `csrf_token`, httponly=False (JS must read it), secure=prod-only, samesite=strict, max_age=8hrs
- **Exempt paths**: /api/auth/login, /api/auth/register, /api/auth/forgot-password, /api/health, /docs, /redoc
- **Token rotation**: After each successful unsafe method
- **Timing-safe comparison**: Uses `secrets.compare_digest` to prevent timing attacks

### `rate_limiting.py` — Token Bucket Rate Limiting

**Algorithm**: Token bucket per client per endpoint.

**Storage**: Redis in production, in-memory fallback in development.

**Configuration**:

| Endpoint Pattern | Limit (req/min) |
|-----------------|-----------------|
| `/api/auth/*` | 3-10 |
| `/api/ocr/*` | 10 |
| `/api/building/generate-description` | 20 |
| `/api/reports` | 30 |
| `/api/maps/*` | 60 |

**Key format**: `ratelimit:{client_id}:{endpoint_hash_md5}`

**Failure mode**:
- Production: FAIL CLOSED (deny if Redis down)
- Development: FAIL OPEN (allow if Redis down)

Returns **429 Too Many Requests** with `Retry-After` header when limit exceeded.

---

## 12. Utilities (`app/utils/`)

### `extent_calculator.py` — Sri Lankan Land Measurements

Converts between the **Acres-Roods-Perches (A-R-P)** system used in Sri Lanka and metric units.

**Constants**:
- 1 Rood = 40 Perches
- 1 Acre = 4 Roods = 160 Perches
- 1 Perch = 25.29 square meters
- 1 Acre = 0.404686 hectares

**Key Functions**:
- `calculate_extent_data(acres, roods, perches)` — One-call calculation returning all metrics
- `format_extent_string(a, r, p)` — "00A-0R-13.8P" format
- `normalize_extent()` — Converts excess perches/roods to proper format
- `parse_extent_string()` — Reverse parse from formatted string
- `validate_extent_values()` — Strict validation (roods 0-3, perches 0-40)

### `text_helpers.py` — Spelling Corrections & Labels

- `clean_spelling_errors()` — Fixes common misspellings (secratary -> Secretariat, pradeshiya saba -> Pradeshiya Sabha)
- `append_label_if_missing()` — Intelligently appends label (e.g., "Beligal" + "Korale" -> "Beligal Korale", but "Beligal Korale" + "Korale" -> "Beligal Korale")
- Case-insensitive with word boundaries to prevent false positives

### `error_responses.py` — Standardized Error Format

**Response format**:
```json
{
  "status": "error",
  "error": "ValidationError",
  "message": "Request validation failed...",
  "details": [{"field": "price", "message": "not_a_number", "type": "value_error"}],
  "request_id": "uuid-xxx",
  "timestamp": "2026-02-10T10:30:00Z",
  "path": "/api/reports"
}
```

**Exception handlers**:
- `validation_exception_handler()` — 422 with field-level errors
- `sqlalchemy_exception_handler()` — 500 with sanitized message (never leaks internals)
- `generic_exception_handler()` — 500 catch-all

**Request ID middleware**: Adds unique `X-Request-ID` header to all responses for tracing.

### `json_validators.py` — JSON Schema Validation

Validates complex JSON fields before database storage:

| Schema | Max Items | Key Validations |
|--------|-----------|-----------------|
| Boundaries | 8 directions | N/S/E/W required, diagonals optional |
| Buildings | 10 | Max 5 photos per building (5MB each) |
| Comparable Properties | 10 | Coordinates in valid range |
| Deeds | 10 | Date format DD-MM-YYYY |
| Nearby Facilities | - | Type, name, distance required |
| Property Photos | 20 | Base64 image_data, caption, order |
| Access Road Conditions | - | Road type enum, condition enum |

### `api_client.py` — HTTP Client with Circuit Breaker

**CircuitBreaker** — Three states:
1. **CLOSED** — Normal operation, requests pass through
2. **OPEN** — Too many failures, reject all requests immediately
3. **HALF_OPEN** — After timeout, test one request for recovery

**APIClient** — Wraps `requests.Session` with:
- Configurable timeout
- Automatic retry with exponential backoff (delay = base * 2^attempt, capped)
- Retry on status codes: 429, 500, 502, 503, 504
- Circuit breaker integration

**Pre-configured instances**:

| Client | Timeout | Retries | Circuit Breaker |
|--------|---------|---------|-----------------|
| google_maps_client | 30s | 3 | 5 failures / 60s recovery |
| google_vision_client | 45s | 3 | 5 failures / 60s recovery |
| anthropic_client | 60s | 2 | 3 failures / 120s recovery |

### `fallbacks.py` — Graceful Degradation

When external services fail, provides user-friendly fallback responses:

- `google_maps_geocoding_fallback()` — Null coordinates, "enter location manually"
- `google_maps_directions_fallback()` — Template text "[add directions manually]"
- `claude_ai_fallback()` — Task-specific placeholder templates
- `ocr_fallback()` — "Document scanning unavailable" with manual entry instructions
- `static_map_fallback()` — Google Maps alternative URL

**Helper**: `safe_api_call(func, fallback_func)` — Wrapper that auto-falls-back on exception.

---

## 13. Constants & Autocomplete Data

### `app/constants.py`

10 predefined valuation purposes:
- Bank Loan / Mortgage, Court-Ordered Valuation, Insurance, Investment Analysis, Legal Proceedings, Mortgage Refinancing, Partition, Sale / Purchase, Taxation / Estate Duty, Visa purpose

### `app/autocomplete.py` (295 lines)

Professional credentials and Sri Lankan data for form autocomplete:

| Category | Count | Examples |
|----------|-------|---------|
| Honorifics | 7 | Mr., Ms., Mrs., Dr., Prof., Rev., Hon. |
| Membership Levels | 7 | Student, Associate, Fellow, Corporate Member |
| Academic Qualifications | 14 | B.Sc. Estate Management, M.Sc. Real Estate |
| Professional Designations | 12 | Chartered Valuer, Government Valuer, Panel Valuer |
| Post-Nominal Letters | 12 | FRICS, MRICS, FIVSL, MIVSL |
| Professional Institutes | 7 | IVSL, RICS, IQSSL |
| Sri Lankan Banks | 30+ | Bank of Ceylon, Commercial Bank, Sampath, NDB |
| Provinces | 10 | Western, Central, Southern, etc. |
| Cities | 50+ | Colombo, Kandy, Galle, Jaffna, etc. |
| Residential Areas | 40+ | Colombo postal codes (C1-C15), suburbs |
| Universities | 23 | University of Colombo, Moratuwa, Peradeniya |
| Office Departments | 8 | Valuation Department, Regional Office |

**Functions**:
- `get_all_autocomplete_data()` — Returns all categories
- `search_autocomplete(category, query, limit)` — Case-insensitive substring search

---

## 14. Maps Service (`app/maps_service.py`)

### GoogleMapsService (424 lines)

Singleton class wrapping Google Maps APIs for the Sri Lankan context.

**Functions**:

| Function | API | Purpose |
|----------|-----|---------|
| `geocode_address()` | Geocoding | Address to coordinates + administrative components |
| `places_autocomplete()` | Places Autocomplete | Place suggestions (restricted to Sri Lanka) |
| `get_place_details()` | Place Details | Full place info from place_id |
| `get_directions()` | Directions | Route between two points with steps |
| `generate_professional_directions_text()` | - | Convert steps to professional paragraph |
| `calculate_direction_from_point()` | - | Compass bearing calculation |
| `generate_static_map_url()` | Static Maps | Map image URL with route and markers |
| `fetch_static_map_image()` | Static Maps | Fetch actual image bytes |

All external calls use the `google_maps_client` (APIClient with circuit breaker).

---

## 15. Key Business Flows

### Flow 1: Property Valuation Report Creation to DOCX Download

```
User creates report (POST /api/reports)
    |
    v
User fills in property data (PUT /api/reports/{id})
    |-- Property identification (plan, lot, surveyor)
    |-- Location (village, district, GPS coordinates)
    |-- Land extent (A-R-P system)
    |-- Buildings (JSON with floors, rooms, materials)
    |-- Locality (nearby facilities, infrastructure)
    |-- Legal aspects (ownership, street lines)
    |-- Valuation calculation
    |-- Certification
    |
    v
User requests DOCX (POST /api/reports/{id}/generate)
    |
    v
Backend: docx_generator.py
    |-- 1. Load letterhead template
    |-- 2. Generate title block
    |-- 3. Generate applicant statement
    |-- 4. Render property sections (50+ paragraph generators)
    |-- 5. Embed photos and maps
    |-- 6. Calculate valuations
    |-- 7. Add certification and signature
    |-- 8. Add invoice section
    |
    v
StreamingResponse returns DOCX file
```

### Flow 2: Multi-Property Report

```
User creates multi-property report
    POST /api/reports/multi-property
    |
    v
For each property:
    POST /api/properties (or link existing)
    POST /api/reports/{id}/properties/{pid}
    |
    v
User fills each property independently
    PUT /api/reports/{id}/properties/{pid}
    |
    v
Mark properties as completed
    PATCH /api/properties/{pid}/status {"status": "completed"}
    |
    v
Generate report (only COMPLETED properties included)
    POST /api/reports/{id}/generate
    |
    v
DOCX includes:
    - Summary page with all property totals
    - Individual property sections (ordered by property_order)
    - Per-property certification
    - Combined invoice
```

### Flow 3: Vehicle Valuation

```
User creates vehicle
    POST /api/vehicles
    |
    v
User fills vehicle data
    PUT /api/vehicles/{id}
    |-- Identification (registration, chassis, engine)
    |-- Specs (make, model, year, mileage)
    |-- Condition assessment (7 condition fields)
    |-- Features, brakes, suspension, tyres
    |
    v
Optional: Get AI valuation suggestion
    POST /api/vehicles/{id}/suggest-valuation
    |-- Claude AI analyzes: age, mileage, condition, features
    |-- Returns: market_value, forced_sale_value, summary
    |
    v
Create vehicle report
    POST /api/reports (report_type='vehicle')
    POST /api/reports/{id}/vehicles/{vid}
    |
    v
Generate DOCX
    POST /api/reports/{id}/generate
```

### Flow 4: OCR Document Processing

```
User uploads document images
    POST /api/ocr/extract
    files: [survey_plan.jpg, deed_page1.jpg, deed_page2.jpg]
    document_type: "survey_plan"
    |
    v
validate_upload_file() for each file
    |-- Check size (max 10MB)
    |-- Check extension whitelist
    |-- Verify magic bytes match content type
    |
    v
ocr_service.process_multiple_documents()
    |
    |-- For each file:
    |   |-- Google Vision API: document_text_detection
    |   |-- Returns: raw OCR text + confidence
    |
    v
ai_parser.parse_with_claude()
    |-- Send OCR text to Claude 3.5 Haiku
    |-- Prompt: "Extract structured property data"
    |-- Returns: JSON with fields:
    |   plan_number, plan_date, lot_number,
    |   boundaries, land_extent, deeds, etc.
    |
    v
merge_extracted_data()
    |-- Combine results from multiple documents
    |-- Highest confidence wins per field
    |
    v
calculate_extent_data() if land extent found
    |-- Convert A-R-P to hectares, sq meters
    |
    v
Return structured data for form pre-fill
```

### Flow 5: Authentication Lifecycle

```
Register: POST /api/auth/register
    |-- Validate password strength
    |-- Check email uniqueness
    |-- Hash password (bcrypt)
    |-- Create user (email_verified=False)
    |-- Send verification email (24hr expiry)
    |-- Return access + refresh tokens
    |
    v
Verify Email: POST /api/auth/verify-email
    |-- Validate token (bcrypt hash comparison)
    |-- Check expiry
    |-- Set email_verified=True
    |
    v
Login: POST /api/auth/login
    |-- Check login rate limit (5 attempts / 15 min)
    |-- Verify password
    |-- Clear login attempts on success
    |-- Return access token (30min) + refresh token (4hr)
    |-- Set HttpOnly cookies
    |
    v
API Calls: Bearer token or cookie
    |-- get_current_user() checks cookie first, then header
    |-- Verify JWT signature
    |-- Check token blacklist
    |-- Return user object
    |
    v
Token Refresh: POST /api/auth/refresh
    |-- Verify refresh token
    |-- Blacklist old refresh token
    |-- Issue new access + refresh tokens (rotation)
    |
    v
Logout: POST /api/auth/logout
    |-- Blacklist access token JTI
    |-- Blacklist refresh token JTI
    |-- Clear HttpOnly cookies
```

---

## 16. File Relationship Map

### Core Dependencies (who imports whom)

```
main.py
  +-- database.py (get_db, engine)
  +-- models.py (all models)
  +-- schemas.py (all schemas)
  +-- auth.py (get_current_user, require_admin)
  +-- crud.py (all CRUD operations)
  +-- docx_generator.py (generate_*_docx)
  +-- autocomplete.py (get_all_autocomplete_data, search_autocomplete)
  +-- constants.py (PREDEFINED_VALUATION_PURPOSES)
  +-- maps_service.py (maps_service singleton)
  +-- middleware/csrf_protection.py (CSRFMiddleware)
  +-- middleware/rate_limiting.py (RateLimitMiddleware, RateLimiter)
  +-- services/ocr_service.py (process_multiple_documents)
  +-- services/job_service.py (JobService)
  +-- services/redis_client.py (get_redis_client, close_redis_connection)
  +-- services/login_limiter.py (LoginLimiter)
  +-- services/audit_service.py (AuditService)
  +-- services/google_oauth_service.py (GoogleOAuthService)
  +-- services/email_service.py (EmailService)
  +-- services/places_service.py (fetch_nearby_facilities, find_nearest_transport)
  +-- utils/extent_calculator.py (calculate_extent_data)
  +-- utils/error_responses.py (exception handlers)

auth.py
  +-- database.py (get_db)
  +-- models.py (User, TokenBlacklist)

crud.py
  +-- models.py (all models)
  +-- schemas.py (all schemas)
  +-- auth.py (get_password_hash)
  +-- base_crud.py (BaseCRUD)
  +-- utils/json_validators.py (validate_report_buildings)

docx_generator.py
  +-- models.py (Report, User, Vehicle)
  +-- letterhead_templates/ (get_template)

services/ocr_service.py
  +-- services/ai_parser.py (parse_with_claude)

services/ai_parser.py
  +-- services/anthropic_client.py (get_anthropic_client)

services/ai_valuation.py
  +-- services/anthropic_client.py (get_anthropic_client)

services/access_transformer.py
  +-- services/anthropic_client.py (get_anthropic_client)

services/building_narrative.py
  +-- services/base_narrative.py (BaseNarrativeService)
  +-- services/narrative_constants.py

services/land_narrative.py
  +-- services/base_narrative.py (BaseNarrativeService)

services/locality_narrative.py
  +-- services/base_narrative.py (BaseNarrativeService)

services/base_narrative.py
  +-- services/anthropic_client.py (get_anthropic_client, is_anthropic_configured)

services/job_service.py
  +-- models.py (Job, Report, User)
  +-- services/file_storage.py (FileStorage)
  +-- docx_generator.py

services/cache_service.py
  +-- services/redis_client.py (RedisCache)

services/login_limiter.py
  +-- services/redis_client.py (get_redis_client)

middleware/rate_limiting.py
  +-- services/redis_client.py (get_redis_client)

maps_service.py
  +-- utils/api_client.py (google_maps_client)

utils/api_client.py
  (standalone - no internal imports)

utils/fallbacks.py
  (standalone - no internal imports)
```

---

## 17. Environment Variables Reference

| Variable | Required | Default | Used In | Purpose |
|----------|----------|---------|---------|---------|
| `DATABASE_URL` | Yes | - | database.py | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | auth.py | JWT access token signing |
| `REFRESH_TOKEN_SECRET_KEY` | No | SECRET_KEY | auth.py | JWT refresh token signing |
| `REDIS_URL` | Prod only | None | redis_client.py | Redis connection string |
| `CORS_ORIGINS` | Yes | - | main.py | Allowed CORS origins (comma-separated) |
| `GOOGLE_MAPS_API_KEY` | No | None | maps_service.py | Google Maps API key |
| `GOOGLE_CLOUD_VISION_API_KEY` | No | None | ocr_service.py | Google Vision OCR |
| `ANTHROPIC_API_KEY` | No | None | anthropic_client.py | Claude AI API key |
| `SENDGRID_API_KEY` | No | None | email_service.py | SendGrid email |
| `EMAIL_FROM` | No | noreply@propertyvaluation.com | email_service.py | Sender email address |
| `FRONTEND_URL` | No | http://localhost:3000 | email_service.py, auth.py | Frontend URL for links |
| `GOOGLE_CLIENT_ID` | No | None | google_oauth_service.py | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | None | google_oauth_service.py | Google OAuth client secret |
| `AUTO_MIGRATE` | No | false | main.py | Auto-run Alembic migrations on startup |
| `ENVIRONMENT` | No | development | middleware | Controls security strictness |
| `SENTRY_DSN` | No | None | job_service.py | Sentry error tracking |
| `PORT` | No | 8000 | Dockerfile/Procfile | Server port |

---

## 18. Deployment & Infrastructure

### Dockerfile

```dockerfile
FROM python:3.11-slim
# System deps: WeasyPrint (Pango, Cairo, Pixbuf), python-magic (libmagic1), fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
    shared-mime-info libmagic1 fonts-liberation fonts-dejavu-core gcc python3-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Railway Deployment (`railway.json`)

- Builder: NIXPACKS
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: GET `/api/health` (30s timeout)
- Restart policy: ON_FAILURE, max 3 retries

### Nixpacks (`nixpacks.toml`)

```toml
[phases.setup]
nixPkgs = ["python311", "gcc", "libffi", "openssl"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

### Procfile (Heroku-compatible)

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Production Requirements Checklist

- [ ] `DATABASE_URL` — PostgreSQL connection string (Neon recommended)
- [ ] `SECRET_KEY` — Strong random key for JWT signing
- [ ] `REDIS_URL` — Redis instance for rate limiting and caching
- [ ] `CORS_ORIGINS` — Frontend domain(s)
- [ ] `GOOGLE_MAPS_API_KEY` — For maps features
- [ ] `ANTHROPIC_API_KEY` — For AI features (OCR parsing, narratives, valuations)
- [ ] `SENDGRID_API_KEY` — For email (password reset, verification)
- [ ] `SENTRY_DSN` — For error monitoring
- [ ] `ENVIRONMENT=production` — Enables strict security (HSTS, fail-closed rate limiting)

### Scaling Considerations

- **Database**: NullPool configured for serverless PostgreSQL (Neon). Connection pooling via Neon's built-in pooler.
- **Redis**: Required for distributed rate limiting across multiple instances
- **File Storage**: Ephemeral (`/tmp`). Generated DOCX files have 1-hour TTL. For persistence, integrate S3/GCS.
- **Background Jobs**: Currently async tasks within the process. For heavy load, extract to Celery/RQ workers.
- **AI Calls**: Circuit breaker (3 failures / 120s recovery) prevents cascading failures during Anthropic outages.

---

## 19. Testing

### Configuration (`pytest.ini`)

Tests use pytest with asyncio support and coverage reporting.

### Test Files

#### `tests/test_auth.py` (471 lines)

9 test classes covering the complete authentication lifecycle:

| Class | Tests |
|-------|-------|
| TestRegistration | Success, duplicate email, weak passwords (uppercase, special, length) |
| TestLogin | Success, wrong password, nonexistent user |
| TestTokenRefresh | Success, revoked token rejection |
| TestLogout | Success, cookie clearing |
| TestPasswordReset | Email sending, token reset, expired token |
| TestEmailVerification | Sending, success, already-verified |
| TestGoogleOAuth | Callback handling, user creation |
| TestGetCurrentUser | Authenticated access, unauthenticated rejection |

#### `tests/test_bare_land.py` (310 lines)

6 test classes for bare land report CRUD:

| Class | Tests |
|-------|-------|
| TestCreateBareLandReport | Success, buildings=null, authentication required |
| TestGetBareLandReport | Retrieve by user, retrieve by ID |
| TestUpdateBareLandReport | Modify fields, preserve null buildings, auth required |
| TestDeleteBareLandReport | Delete, nonexistent handling |
| TestOwnershipValidation | Cross-user access prevention, unauthorized modifications |
| TestLandNarrative | Narrative generation, comparables, Claude mock |

### Test Patterns

- **Fixtures**: Test client, database session, test user, auth headers
- **Mocking**: OAuth services, email backends, Anthropic API
- **Async**: pytest-asyncio for async endpoint tests
- **Isolation**: Each test creates its own data, ownership verified across users

---

## 20. For Someone Recreating This Project

### Step-by-Step Setup

1. **Database Setup**
   ```bash
   # Create a PostgreSQL database (Neon recommended for serverless)
   # Set DATABASE_URL in .env
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

2. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Fill in: SECRET_KEY, DATABASE_URL, CORS_ORIGINS
   # Optional: REDIS_URL, API keys for Google/Anthropic/SendGrid
   ```

4. **Run Migrations**
   ```bash
   alembic upgrade head
   # Or set AUTO_MIGRATE=true for automatic migration on startup
   ```

5. **Start Server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Architecture Decisions Explained

**Why FastAPI?**
- Async support for external API calls (Google, Claude, SendGrid)
- Automatic OpenAPI documentation
- Pydantic validation built-in
- High performance ASGI server

**Why Junction Tables (report_properties, report_vehicles)?**
- A report can contain multiple properties or vehicles
- A property can appear in multiple reports
- Junction tables store per-association metadata (order, overrides)
- Enables multi-property report feature with independent property management

**Why Ephemeral File Storage?**
- Railway's filesystem is ephemeral (files lost on redeploy)
- TTL-based cleanup (1 hour) prevents storage exhaustion
- Files stored in `/tmp` with UUID naming and metadata companions
- For production persistence, integrate cloud object storage (S3/GCS)

**Why PropertyDataMixin?**
- Reports and Properties share ~132 identical data fields
- Mixin pattern avoids field duplication across two models
- Both tables get the same columns via SQLAlchemy mixin inheritance

**Why Reflection-Based Duplication?**
- Report/Property duplication needs to copy all fields
- Manual field lists become outdated when new fields are added
- `_duplicate_entity_data()` uses SQLAlchemy `inspect()` to auto-copy all columns
- Future-proof: new fields are automatically included in duplications

**Why Separate Narrative Services?**
- Building, land, and locality descriptions need different prompts and word limits
- Base class (`BaseNarrativeService`) handles Claude API boilerplate
- Subclasses define domain-specific prompt engineering
- Adaptive length based on data richness (land_narrative.py adjusts 30-140 words)

### Domain-Specific Knowledge

**Sri Lankan Land Measurements (Acres-Roods-Perches)**:
- 1 Acre = 4 Roods = 160 Perches
- 1 Perch = 25.29 square meters
- Format: "02A-3R-15.5P"
- Excess perches/roods auto-normalize (e.g., 45 perches = 1 rood + 5 perches)

**Sri Lankan Administrative Divisions**:
- Province -> District -> Divisional Secretariat (DS Division) -> Grama Niladari Division
- 9 Provinces, 25 Districts
- Loaded from `administrative_divisions.json`

**Professional Credentials**:
- IVSL = Institute of Valuers of Sri Lanka
- RICS = Royal Institution of Chartered Surveyors
- Membership levels: Student -> Associate -> Professional Associate -> Fellow -> Corporate
- Post-nominal letters: FIVSL, MIVSL, FRICS, MRICS

**Valuation Report Structure (Sri Lankan standard)**:
1. Letterhead with valuer credentials
2. Applicant information
3. Property identification (plan, lot, surveyor)
4. Situation and access directions
5. Boundaries and land extent
6. Building descriptions with construction details
7. Locality and infrastructure
8. Legal aspects (ownership, encumbrances, street lines)
9. Comparable properties and market analysis
10. Valuation calculation
11. Certification
12. Signature block with professional credentials
13. Certificate of identity
14. Invoice

**Vehicle Valuation Specifics**:
- Sri Lankan registration format
- Provincial council assignment
- Vehicle condition rated on 7+ dimensions
- Past valuation history tracking
- Office use data (civil/military number, approval position)
