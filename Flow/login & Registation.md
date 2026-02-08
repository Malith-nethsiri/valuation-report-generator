# USER REGISTRATION & AUTHENTICATION FLOW

## Database Schema

```sql
-- USERS TABLE
CREATE TABLE users (
  id                        INTEGER PRIMARY KEY AUTOINCREMENT,
  email                     VARCHAR(255) UNIQUE NOT NULL,
  password_hash             VARCHAR(255) NOT NULL,        -- Bcrypt (~60 chars)
  honorific                 VARCHAR(10),
  full_name                 VARCHAR(255) NOT NULL,
  phone                     VARCHAR(50),
  role                      VARCHAR(20) DEFAULT 'user',   -- 'user' | 'admin'
  password_reset_token      VARCHAR(255),                 -- Bcrypt hash
  password_reset_expires    DATETIME(tz),
  created_at                DATETIME(tz) DEFAULT now(),
  updated_at                DATETIME(tz) DEFAULT now()
);

-- TOKEN BLACKLIST TABLE (for logout/revocation)
CREATE TABLE token_blacklist (
  id          INTEGER PRIMARY KEY,
  jti         VARCHAR(36) UNIQUE NOT NULL,    -- JWT ID
  user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
  token_type  VARCHAR(20) NOT NULL,           -- 'access' | 'refresh'
  expires_at  DATETIME(tz) NOT NULL,
  revoked_at  DATETIME(tz) DEFAULT now()
);
```

## Example Data

| State | id | email | password_hash | full_name | role | created_at |
|-------|----|----|---------------|-----------|------|------------|
| Before Registration | - | - | - | - | - | - |
| After Registration | 1 | `john@example.com` | `$2b$12$K4x...` | John Doe | user | 2026-02-06 10:00:00 |

---

## COMPLETE FLOW TABLE

| # | User Action | Frontend View | Frontend Inputs | Frontend Processing | API Endpoint | Backend Handler | Backend Logic | DB Tables | DB Fields | Data Transformations | Security Measures | Failure Cases | Success Output |
|---|-------------|---------------|-----------------|--------------------|--------------|-----------------|--------------|-----------|-----------|--------------------|-------------------|---------------|----------------|
| **INITIAL ACCESS** |
| 1 | Enters website URL | `App.tsx` → Router | None | Check `AuthContext` for existing token in `secureStorage` | None initially | - | - | - | - | - | - | No token: redirect to login | Token exists: proceed to step 2 |
| 2 | Auto-auth check on mount | `AuthContext.tsx` | Existing `access_token` from sessionStorage | Decrypt token using browser fingerprint key, set `Authorization: Bearer {token}` header | `GET /api/auth/me` | `main.py:get_current_user_profile()` | 1. Decode JWT 2. Check not blacklisted 3. Fetch user by email | `users`, `token_blacklist` | `email`, `jti` | JWT decode (HS256) | Token signature verification, blacklist check | 401: Token invalid/expired/revoked | `UserResponse { id, email, full_name, role, ... }` |
| **REGISTRATION FLOW** |
| 3 | Clicks "Register" link | `LoginPage.tsx` | None | `navigate('/register')` | None | - | - | - | - | - | - | - | Redirect to RegisterPage |
| 4 | Fills Step 1: Personal Info | `RegisterPage.tsx` Step 1 | **full_name**: `<input type="text">`, min(2), max(100); **email**: `<input type="email">`, z.string().email(); **phone**: `<input type="tel">`, optional | Zod validation on blur/submit, real-time error display | None yet | - | - | - | - | - | Client-side validation | Validation errors shown inline | Proceed to Step 2 |
| 5 | Fills Step 2: Password | `RegisterPage.tsx` Step 2 | **password**: `<input type="password">`, min(8), regex: `/[A-Z]/`, `/[a-z]/`, `/\d/`, `/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/`; **confirmPassword**: must match | Calculate password strength (weak/medium/strong/excellent), show strength meter | None yet | - | - | - | - | - | Client-side strength validation | Weak password warning | Proceed to Step 3 |
| 6 | Accepts Terms (Step 3) | `RegisterPage.tsx` Step 3 | **termsAccepted**: `<input type="checkbox">`, required | Final validation of all fields | None yet | - | - | - | - | - | - | Checkbox not checked | Submit enabled |
| 7 | Clicks "Create Account" | `RegisterPage.tsx` | All fields collected | 1. Build `UserCreate` payload 2. Call `authContext.register()` | `POST /api/auth/register` | `main.py:register()` | 1. Pydantic validation 2. `SELECT * FROM users WHERE email = ?` (uniqueness) 3. `validate_password_strength()` 4. `bcrypt.hash(password)` 5. `INSERT INTO users` 6. Generate access_token (30min) + refresh_token (4hr) | `users` | `email`, `password_hash`, `full_name`, `phone`, `role`, `created_at` | Password → bcrypt hash, Email → lowercase | Rate limit: 5/min/IP, Input sanitization, Password strength validation, Block 48 common passwords | 400: Weak password; 409: Email exists; 422: Validation error | `TokenResponse { access_token, refresh_token, user }` |
| 8 | Auto-redirect after register | `AuthContext.tsx` | Token response | 1. `authTokenStorage.setToken(access_token)` 2. `authTokenStorage.setUserData(user)` 3. Init CSRF token | None | - | - | - | - | AES-256 encrypt token with browser fingerprint key | Tokens in sessionStorage only | - | Redirect to `/dashboard` |
| **LOGIN FLOW** |
| 9 | Navigates to login | `LoginPage.tsx` | None | Check if already authenticated | None | - | - | - | - | - | - | - | Show login form |
| 10 | Enters credentials | `LoginPage.tsx` | **email**: `<input type="email">`, z.string().email(); **password**: `<input type="password">`, min(6) | Zod validation, toggle password visibility | None | - | - | - | - | - | Client-side validation | Validation errors | Submit enabled |
| 11 | Clicks "Sign In" | `LoginPage.tsx` | email, password | 1. Validate inputs 2. Call `authContext.login()` 3. Show loading state | `POST /api/auth/login` | `main.py:login()` → `auth.py:authenticate_user()` | 1. `SELECT * FROM users WHERE email = ?` 2. `bcrypt.verify(plain_password, password_hash)` 3. Generate access_token + refresh_token 4. Set HttpOnly cookies | `users` | `email`, `password_hash` | Email → lowercase | Rate limit: 10/min/IP, Timing-safe password comparison | 401: Invalid credentials; 429: Rate limited | `TokenResponse { access_token, refresh_token, user }` |
| 12 | Auto-redirect after login | `AuthContext.tsx` | Token response | Same as step 8 | None | - | - | - | - | Same as step 8 | Same as step 8 | - | Redirect to `/dashboard` or `location.state.from` |
| **AUTHENTICATED REQUESTS** |
| 13 | Makes any API request | Any protected page | Request data | 1. Read CSRF cookie 2. Add `X-CSRF-Token` header 3. Cookies sent automatically | Any `POST/PUT/DELETE/PATCH` | `csrf_protection.py` middleware | 1. Extract X-CSRF-Token header 2. Compare with csrf_token cookie (constant-time) 3. Pass to route handler | - | - | - | CSRF double-submit cookie pattern, SameSite=strict | 403: CSRF token invalid | Request proceeds |
| 14 | Token approaching expiry | Any page | access_token nearing 30min | Axios interceptor detects 401 | `POST /api/auth/refresh` | `main.py:refresh_token()` | 1. Verify refresh_token type="refresh" 2. Check not blacklisted 3. Generate new access_token 4. Rotate refresh_token (new JTI) 5. Set new cookies | `token_blacklist` | `jti` | JWT decode/encode | Refresh token rotation, Blacklist check | 401: Refresh token invalid/expired | `RefreshTokenResponse { access_token, refresh_token }` |
| **FETCH USER PROFILE** |
| 15 | Page requests user data | Dashboard/Profile | None | Read from `AuthContext.user` or call API | `GET /api/auth/me` | `main.py:get_current_user_profile()` | 1. `get_current_user` dependency validates token 2. Return user data | `users` | All profile fields | - | Token validation | 401: Unauthorized | `UserResponse { id, email, full_name, phone, role, ... }` |
| **UPDATE USER PROFILE** |
| 16 | Edits profile fields | Profile page | Various profile fields | Validate locally, build update payload | `PUT /api/users/me` or `PATCH /api/users/profile` | `main.py:update_user_profile()` | 1. Validate input 2. `UPDATE users SET ... WHERE id = ?` | `users` | Updated fields + `updated_at` | Field normalization | Auth required, Input validation | 400: Invalid data; 401: Unauthorized | Updated `UserResponse` |
| **PASSWORD RESET FLOW** |
| 17 | Clicks "Forgot Password" | `LoginPage.tsx` | None | `navigate('/forgot-password')` | None | - | - | - | - | - | - | - | Show forgot password form |
| 18 | Enters email | Forgot Password Page | **email**: `<input type="email">` | Validate email format | `POST /api/auth/forgot-password` | `main.py:forgot_password()` | 1. `SELECT * FROM users WHERE email = ?` 2. Generate `secrets.token_urlsafe(32)` 3. `bcrypt.hash(token)` 4. `UPDATE users SET password_reset_token = ?, password_reset_expires = NOW() + 1hr` 5. Send email with plaintext token | `users` | `password_reset_token`, `password_reset_expires` | Token → bcrypt hash (stored), plaintext (emailed) | Rate limit: 3/min/IP, Email enumeration prevention (always returns success) | Email service failure (silent) | `{ success: true, message: "If email exists..." }` |
| 19 | Clicks email link | Email client | Token from URL params | Extract `token` and `email` from URL | None | - | - | - | - | - | - | - | Show reset password form |
| 20 | Enters new password | Reset Password Page | **new_password**: `<input type="password">`, same rules as registration; **confirm_password**: must match | Validate password strength | `POST /api/auth/reset-password` | `main.py:reset_password()` | 1. `SELECT * FROM users WHERE email = ?` 2. Check `password_reset_expires > NOW()` 3. `bcrypt.verify(token, password_reset_token)` 4. `validate_password_strength(new_password)` 5. `bcrypt.hash(new_password)` 6. `UPDATE users SET password_hash = ?, password_reset_token = NULL, password_reset_expires = NULL` | `users` | `password_hash`, `password_reset_token`, `password_reset_expires` | New password → bcrypt hash | Rate limit: 5/min/IP, Token expiry check, Password strength validation | 400: Invalid/expired token; 400: Weak password | `{ success: true, message: "Password reset" }` |
| **LOGOUT FLOW** |
| 21 | Clicks "Logout" | Any authenticated page | None | Call `authContext.logout()` | `POST /api/auth/logout` | `main.py:logout()` | 1. Extract JTI from token 2. `INSERT INTO token_blacklist (jti, user_id, token_type, expires_at)` 3. Clear cookies | `token_blacklist` | `jti`, `user_id`, `token_type`, `expires_at`, `revoked_at` | - | Token revocation via blacklist | Token already revoked (ignored) | `{ message: "Successfully logged out" }` |
| 22 | Frontend cleanup | `AuthContext.tsx` | None | 1. `authTokenStorage.clearAll()` 2. Clear `Authorization` header 3. `setUser(null)` | None | - | - | - | - | Clear encrypted sessionStorage | - | - | Redirect to `/login` |

---

## INPUT FIELD SPECIFICATIONS

| Field | HTML Type | Frontend Validation | Backend Validation | DB Type |
|-------|-----------|--------------------|--------------------|---------|
| **email** | `<input type="email">` | `z.string().email()` | `EmailStr` (Pydantic), uniqueness check | `VARCHAR(255) UNIQUE NOT NULL` |
| **password** | `<input type="password">` | min(8), `/[A-Z]/`, `/[a-z]/`, `/\d/`, `/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/` | Same regex + not in 48 common passwords list | `VARCHAR(255) NOT NULL` (bcrypt hash) |
| **full_name** | `<input type="text">` | `z.string().min(2).max(100)` | `str`, min_length=2, max_length=100 | `VARCHAR(255) NOT NULL` |
| **phone** | `<input type="tel">` | Optional, any format | Optional `str`, max 50 chars | `VARCHAR(50)` |
| **confirmPassword** | `<input type="password">` | Must match password | Not sent to backend | - |
| **termsAccepted** | `<input type="checkbox">` | Required (true) | Not sent to backend | - |

---

## TOKEN SPECIFICATIONS

| Token Type | Algorithm | Expiry | Claims | Storage |
|------------|-----------|--------|--------|---------|
| **access_token** | HS256 | 30 minutes | `sub` (email), `exp`, `jti` (UUID), `type: "access"` | HttpOnly cookie + encrypted sessionStorage |
| **refresh_token** | HS256 | 4 hours | `sub` (email), `exp`, `jti` (UUID), `type: "refresh"` | HttpOnly cookie only (path: `/api/auth`) |
| **csrf_token** | Random bytes | 8 hours | 32 bytes urlsafe | Cookie (SameSite=strict) |
| **password_reset_token** | Random bytes | 1 hour | 32 bytes urlsafe (plaintext emailed, bcrypt stored) | DB only |

---

## KEY FILES

| Layer | File | Purpose |
|-------|------|---------|
| Frontend | `frontend/src/pages/LoginPage.tsx` | Login UI |
| Frontend | `frontend/src/pages/RegisterPage.tsx` | Multi-step registration UI |
| Frontend | `frontend/src/contexts/AuthContext.tsx` | Auth state management |
| Frontend | `frontend/src/services/api.ts` | Axios interceptors, CSRF handling |
| Frontend | `frontend/src/utils/secureStorage.ts` | AES-256 encrypted token storage |
| Backend | `backend/app/main.py` | API route handlers |
| Backend | `backend/app/auth.py` | JWT creation, password hashing, validation |
| Backend | `backend/app/models.py` | SQLAlchemy User model |
| Backend | `backend/app/schemas.py` | Pydantic request/response schemas |
| Backend | `backend/app/middleware/csrf_protection.py` | CSRF double-submit cookie |
| Backend | `backend/app/middleware/rate_limiting.py` | Token bucket rate limiting |
| Database | `backend/alembic/versions/001_baseline_schema.py` | Users table migration |
| Database | `backend/alembic/versions/003_add_token_blacklist.py` | Token blacklist migration |

---

## SECURITY SUMMARY

### Password Security
- Bcrypt hashing with automatic salt
- 48 commonly-used passwords blocked
- Strength requirements: 8+ chars, uppercase, lowercase, digit, special char

### Token Security
- Short-lived access tokens (30 min)
- Refresh token rotation on use
- Token blacklist for immediate revocation
- HttpOnly cookies prevent XSS token theft

### Request Security
- CSRF double-submit cookie pattern
- Rate limiting per endpoint per IP
- Input validation on both frontend and backend

### Storage Security
- Tokens encrypted with AES-256 in sessionStorage
- Browser fingerprint as encryption key component
- No tokens in localStorage (cleared on tab close)
