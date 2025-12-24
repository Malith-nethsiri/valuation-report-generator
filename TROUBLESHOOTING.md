# OCR Error Troubleshooting Guide

## Issue: "NoneType object has no attribute 'get'" Error

### What Happened

On December 19, 2025, the OCR document upload feature encountered an error where Python threw:
```
'NoneType' object has no attribute 'get'
```

### Root Cause

1. **Server Reload Loop**: The backend's auto-reload feature detected code changes and attempted to reload
2. **Incomplete Reload**: The server got stuck in a reload state and never fully restarted
3. **Partial Module Loading**: During this stuck state, OCR functions returned `None` instead of proper data
4. **Frontend Error**: The frontend tried to call `.get()` on `None`, causing the error

### Solution Applied

The issue was resolved by **restarting the backend server**, which allowed all modules to load properly.

---

## Prevention Measures Implemented

### 1. Enhanced Error Handling (Backend)
**File**: `backend/app/main.py`

- Added comprehensive null checks before calling `.get()` on results
- Added specific error messages that indicate if server is reloading
- Added logging at all critical points to identify failures quickly

**What it does**: If the server is in a bad state, it now returns a clear error message like:
```
"OCR processing returned None - server may be reloading. Please try again in a few seconds."
```

### 2. Health Check Endpoint (Backend)
**File**: `backend/app/main.py`
**Endpoint**: `GET /api/health/detailed`

A new endpoint that validates:
- ✓ Database connection
- ✓ Anthropic API key configuration
- ✓ Google Vision API key configuration
- ✓ OCR service module imports

**Usage**:
```bash
curl http://localhost:8000/api/health/detailed
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-19T10:30:00",
  "checks": {
    "database": {"status": "healthy", "message": "Connected"},
    "anthropic_api": {"status": "configured", "message": "API key present"},
    "google_vision_api": {"status": "configured", "message": "API key present"},
    "ocr_service": {"status": "healthy", "message": "Modules loaded"}
  }
}
```

### 3. Automatic Retry Logic (Frontend)
**File**: `frontend/src/components/DocumentUploadOCR.tsx`

The frontend now automatically retries failed uploads:
- **Max retries**: 2 attempts
- **Retry delay**: 2 seconds between attempts
- **Smart detection**: Only retries transient errors (server reloading, 500 errors)
- **User-friendly**: Happens automatically without user intervention

**What it does**: If the server is reloading when you click "Process", it will automatically retry after 2 seconds, making the system more resilient.

### 4. Enhanced Logging
**Files**:
- `backend/app/services/ocr_service.py`
- `backend/app/services/ai_parser.py`

All OCR processing steps now log with `[OCR]` prefix:
```
INFO: [OCR] Extracting text from image using Google Vision API...
INFO: [OCR] Extracted 1523 characters of text
INFO: [OCR] Parsing text with Claude AI...
INFO: [OCR] Successfully extracted 12 fields with confidence 0.87
```

**Benefit**: Easy to track exactly where processing fails in the logs.

---

## How to Prevent This in the Future

### For Developers

1. **After making code changes**:
   - Watch the backend console to ensure reload completes
   - Look for "Application startup complete" message
   - If stuck, manually restart the server

2. **Before deploying**:
   - Check `/api/health/detailed` endpoint
   - Ensure all checks show "healthy" status

3. **When debugging**:
   - Check logs for `[OCR]` prefixed messages
   - Use `/api/health/detailed` to validate configuration

### For Users

1. **If you see "NoneType" error**:
   - Wait 5 seconds and click "Process Again"
   - The automatic retry will likely fix it

2. **If error persists**:
   - Refresh the page
   - Check if backend server is running
   - Contact developer to check `/api/health/detailed`

---

## Quick Diagnosis Checklist

If OCR is failing:

- [ ] Check backend console for "Application startup complete"
- [ ] Visit `http://localhost:8000/api/health/detailed`
- [ ] Verify all health checks show "healthy" or "configured"
- [ ] Check logs for `[OCR]` messages to see where it fails
- [ ] Verify `ANTHROPIC_API_KEY` is set in `.env`
- [ ] Verify `GOOGLE_VISION_API_KEY` is set in `.env`
- [ ] Restart backend server if needed

---

## Related Files

- Backend error handling: `backend/app/main.py` (lines 500-525)
- Health check: `backend/app/main.py` (lines 214-262)
- Frontend retry logic: `frontend/src/components/DocumentUploadOCR.tsx` (lines 111-205)
- Enhanced logging: `backend/app/services/ocr_service.py`, `backend/app/services/ai_parser.py`

---

*Last updated: December 19, 2025*
