# Project Updates Roadmap

## Overview
This document captures the planned updates discussed for the Valuation Report Generator.
Items are listed in execution priority order.

---

## Current State (Baseline)

| Area | Status |
|------|--------|
| Property form (13 steps, 3 phases) | Complete |
| Vehicle data collection form (5 steps) | Complete |
| Vehicle DOCX generator (backend) | Complete — not yet wired to frontend pipeline |
| AI vehicle valuation suggestions | Complete |
| Property AI valuation | Not built — manual only |
| OCR pipeline (images + PDFs) | Complete |
| Email ingestion | Not built |
| Tablet responsive design | Partial — missing md: breakpoints in main forms |
| GPS location in property form | Not built — location is manual/map-click only |
| PDF generation/preview | Not built — DOCX only |

---

## Planned Updates (Priority Order)

---

### 1. Get Current Location Button
**Priority: High | Complexity: Low**

Add a "Use My Location" GPS button to the property location step so valuers
in the field can automatically populate coordinates without searching manually.

**What to build:**
- "Use My Location" button in `PropertyLocationMap.tsx` using `navigator.geolocation`
- When Google Maps is active: pan map to device position + drop marker + populate coordinates
- When in fallback mode (`ManualAddressInput.tsx`): auto-fill lat/lng fields
- Handle permission-denied gracefully with a user-friendly message
- Show accuracy indicator on map

**Files affected:**
- `frontend/src/components/PropertyLocationMap.tsx`
- `frontend/src/components/ManualAddressInput.tsx`

---

### 2. Tablet UX Optimization
**Priority: Very High | Complexity: Medium**

Valuers carry tablets during property inspections. The current UI uses only
`sm:` and `lg:` Tailwind breakpoints — the tablet range (`md:`, 768px) is largely
uncovered, resulting in layouts that are either too cramped or too spread out on tablets.

**What to build:**
- Add `md:` breakpoints throughout all main form components
- Larger touch targets for buttons, navigation dots, and input fields
- Two-column grid layouts for tablets where single-column is cramped
- Sticky PhaseTabBar so valuers can jump between phases without scrolling back to top
- Landscape/portrait handling for tablet form factor
- Touch-friendly photo upload (prominent camera button on tablet)
- Better step navigation for tablet (larger step indicators)

**Files affected:**
- `frontend/src/components/MultiStepForm.tsx`
- `frontend/src/components/VehicleStepForm.tsx`
- `frontend/src/components/steps/PhaseTabBar.tsx`
- All step components in `frontend/src/components/steps/`

---

### 3. Vehicle Report Generation (Frontend Pipeline)
**Priority: High | Complexity: Medium**

The vehicle DOCX generator (`vehicle_generator.py`, 614 LOC) is fully built on the backend
with all sections: vehicle ID, engine, body condition, features, tyres, electrical, history,
valuation, photos, and office use. However, the frontend vehicle form (VehicleStepForm.tsx)
only collects data — there is no final step that creates a Report record and triggers DOCX
generation.

**What to build:**
- Connect vehicle form data to the `Report` model (report_type = 'vehicle')
- Add a final "Generate Report" step to `VehicleStepForm.tsx`
- Wire to existing job service (`POST /api/reports/{id}/generate`)
- Use existing `useJobPolling.ts` hook for progress bar (PENDING → PROCESSING → COMPLETED)
- Show DOCX download button when job completes
- Match the pattern used in the property form's final step

**Files affected:**
- `frontend/src/components/VehicleStepForm.tsx`
- `frontend/src/hooks/useJobPolling.ts` (reuse existing)
- `frontend/src/services/api/reportApi.ts` (reuse existing)
- `backend/app/routers/vehicles.py` (may need minor updates)

---

### 4. PDF Preview + PDF Download
**Priority: High | Complexity: Medium**

Currently all reports are generated and downloaded as DOCX only. Adding PDF output
means valuers can share reports with clients who don't have Microsoft Word, and allows
previewing the report in the browser before downloading.

**What to build:**
- Server-side DOCX → PDF conversion using LibreOffice headless (free, runs on Render)
- New endpoint: `GET /api/reports/{id}/download?format=pdf`
- Browser preview: render PDF in `<iframe>` or PDF.js viewer in a modal
- "Preview Report" button that opens the PDF viewer before committing to download
- Download options: DOCX button + PDF button on report detail / generation completion screen
- Progress indicator during conversion (PDF conversion takes 2–5 seconds)

**Files affected:**
- `backend/app/services/job_service.py` (add PDF conversion step)
- `backend/app/routers/reports.py` (add format param to download endpoint)
- `backend/app/docx_generator.py` (add PDF conversion call)
- `frontend/src/components/` (new PDF preview modal component)
- `frontend/src/services/api/reportApi.ts` (add PDF download function)

---

### 5. AI Valuation Assistant (Properties)
**Priority: High | Complexity: Medium**

Vehicle valuation AI already exists (`ai_valuation.py`) — it suggests market value,
forced sale value, and brand new price with reasoning and confidence scores. The same
"vertical AI" capability needs to be extended to properties.

**What to build:**
- New service: `backend/app/services/ai_property_valuation.py` (mirrors ai_valuation.py)
- Inputs: district, GN division, land extent (A-R-P), property type, building quality,
  comparables entered by user, access/location data
- Outputs: suggested land value per perch, land total, building value, market value,
  forced sale value, confidence score, reasoning text
- Frontend: "AI Assist" button in Step 8 (Land Values) of the property form
- Display AI suggestion alongside manual input — valuer can accept, modify, or ignore
- Vehicle side: ensure "Suggest Valuation" button in VehicleStepForm.tsx is visible and
  wired to the existing `ai_valuation.py` (may already be done)

**Files affected:**
- `backend/app/services/ai_property_valuation.py` (new file)
- `backend/app/routers/reports.py` or new `routers/valuation_ai.py`
- `frontend/src/components/steps/` (Step 8 Land Values component)
- `frontend/src/services/api/reportApi.ts`

---

### 6. Offline Draft Resilience
**Priority: Medium-High | Complexity: Low-Medium**

Field inspections often happen in areas with poor or no mobile connectivity.
The existing `useDraftManager.ts` auto-saves drafts but requires a network connection.
If connectivity drops mid-inspection, changes can be lost.

**What to build:**
- localStorage fallback in `useDraftManager.ts` when network is unavailable
- Auto-detect connectivity loss and switch to local save transparently
- On reconnect: sync local draft to server, resolve conflicts
- Visual indicator: "Saved locally — syncing..." when offline
- Works alongside PWA (item 9) for true offline support

**Files affected:**
- `frontend/src/hooks/useDraftManager.ts`
- Possibly a new utility in `frontend/src/utils/`

---

### 7. AI Email Agent (Gmail / Outlook Integration)
**Priority: High | Complexity: High**

Clients send valuation instructions, property documents, and supporting images/PDFs
via email. Currently valuers must manually re-enter all this information into the form.
An AI email agent would read emails from the valuer's inbox, extract attachments,
run them through the existing OCR + AI parsing pipeline, and pre-populate form fields.

**What to build:**
- Gmail OAuth integration (extends existing `google_oauth_service.py` with `gmail.readonly` scope)
- Microsoft OAuth integration for Outlook (`Mail.Read` scope)
- New backend service: `backend/app/services/email_agent_service.py`
  - Fetch recent emails from connected inbox
  - Extract text body + attachments (PDF, images)
  - Run attachments through existing OCR pipeline (`ocr/pipeline.py`)
  - Run through existing AI parsers (`ai/property_parser.py`, `ai/vehicle_parser.py`)
  - Return structured extracted data + confidence scores
- New router: `backend/app/routers/email_agent.py`
- Frontend:
  - "Import from Email" button in the form
  - Email picker modal: shows recent emails, user selects one
  - Review screen: shows extracted fields before populating the form
  - User confirms → fields populated (uses existing merge logic)

**Note on OAuth verification:** Gmail and Microsoft OAuth for inbox access require
app verification by Google/Microsoft before production use. Plan for this verification
process as part of the release timeline.

**Reuses:**
- `backend/app/services/ocr/pipeline.py` (OCR + merging, already built)
- `backend/app/services/ai/property_parser.py` (property extraction, already built)
- `backend/app/services/ai/vehicle_parser.py` (vehicle extraction, already built)
- `backend/app/services/google_oauth_service.py` (Google OAuth, extend scope)

---

### 8. Digital Signature Capture
**Priority: Medium | Complexity: Medium**

On tablets, valuers can sign reports directly using touch or stylus input.
The captured signature gets embedded in the generated DOCX/PDF report.

**What to build:**
- Signature capture canvas component (using `signature_pad` library or HTML5 Canvas)
- Save signature as PNG, store in report data
- Embed signature image in DOCX generation (property + vehicle generators)
- Option to clear and re-sign
- Placed in the certification step (Step 13) of the property form and final step of vehicle form

**Files affected:**
- `frontend/src/components/steps/` (certification step)
- `backend/app/docx_generation/` (embed signature image in report)

---

### 9. Progressive Web App (PWA)
**Priority: Medium | Complexity: Low**

Make the app installable on tablets with a native app-like experience:
full-screen mode, home screen icon, faster loading.

**What to build:**
- `frontend/public/manifest.json` with app name, icons, display mode
- Service worker for asset caching (Vite PWA plugin)
- App icons in multiple sizes
- Works best combined with offline draft resilience (item 6)

**Files affected:**
- `frontend/public/manifest.json` (new)
- `frontend/vite.config.ts`

---

### 10. Voice Input for Field Descriptions
**Priority: Medium | Complexity: Low**

Allow valuers to dictate narrative descriptions (locality, building, land) on tablet
instead of typing, using the device microphone.

**What to build:**
- Microphone button on narrative text fields (locality, building description, land description)
- Uses browser Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`)
- Dictated text inserted at cursor position in the field
- Works on Chrome/Android tablets (primary tablet platform)
- Graceful fallback: button hidden if Speech API not supported

**Files affected:**
- `frontend/src/components/LocalityInformationSection.tsx`
- `frontend/src/components/building/BuildingConstructionSection.tsx`
- Shared voice input hook/component

---

## Summary Table

| # | Feature | Complexity | User Impact | Field Impact |
|---|---------|------------|-------------|--------------|
| 1 | Get Current Location | Low | High | Very High |
| 2 | Tablet UX | Medium | Very High | Very High |
| 3 | Vehicle Report Generation | Medium | High | High |
| 4 | PDF Preview + Download | Medium | High | Medium |
| 5 | AI Valuation Assistant | Medium | High | High |
| 6 | Offline Drafts | Low-Med | High | Very High |
| 7 | AI Email Agent | High | Very High | High |
| 8 | Digital Signature | Medium | Medium | High |
| 9 | PWA | Low | Medium | High |
| 10 | Voice Input | Low | Medium | High |

---

*Last updated: 2026-03-02*
