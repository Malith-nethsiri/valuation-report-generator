# Legal Aspects Extension - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Verify Servers are Running
Both servers should already be running:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173

### Step 2: Open the Application
Navigate to: **http://localhost:5173**

### Step 3: Test the New Form
1. Create a new report or edit an existing one
2. Go to **Step 7: Legal Aspects**
3. You'll see 5 collapsible subsections (instead of the old 5 simple fields)

### Step 4: Try Adding Detailed Information
**Example - Test Ownership Section:**
- Expand "(a). Ownership & Title"
- Set "Property Encumbered": **Yes**
- Notice encumbrance fields appear with amber background
- Select "Encumbrance Type": **Mortgage**
- Enter details: **"Bank of Ceylon, Colombo Branch"**

**Example - Test Building Limits:**
- Expand "(c). Building Limits"
- Set "Building Plan Approved": **Yes**
- Enter distance: **"25 feet"**
- Enter authority: **"Rambukkana Pradeshiya Sabha"**

### Step 5: Generate Report
1. Save the report
2. Click "Generate Report"
3. Open the DOCX file
4. Navigate to **Section 6.0 LEGAL ASPECTS**
5. **Verify**: You should see paragraphs, not "Ownership: Freehold"

---

## ✅ What Changed?

### Before (Old Format):
```
6.0. LEGAL ASPECTS

(a). Ownership: Freehold
(b). Street lines: Not affected
(c). Building limits: Within limits
(d). Local authority data: Rambukkana Pradeshiya Sabha
(e). Rent act effectiveness: Not affected
```

### After (New Format):
```
6.0. LEGAL ASPECTS

(a). Ownership:
I did not search regarding the history and pedigree of the property.
Mr. D Indika Harshana Perera claims ownership to the property by
transfer deed No:1888 dated 22-03-2006 attested by Walira Swarni
Sri Bandara notary public in Kegalle district. This property is
already mortgaged to Bank of Ceylon, Colombo Branch. I valued
freehold interest of the property free from all legal encumbrance.

(b). Street lines:
Street lines are not affected to the property. Street lines are
affected to the properties which are located along roads within
Municipal Council Limits and imposed by a gazette.

[... and so on for other subsections]
```

---

## 🎯 Key Features

### 1. Collapsible Subsections
Click section headers to expand/collapse. All start expanded for easy access.

### 2. Conditional Fields
- **Encumbrance details** only show if "Property Encumbered" = Yes
- **Tax levy field** only shows if "Property Rated for Taxes" = Yes

### 3. Smart Defaults
System auto-pulls data from other sections:
- Owner name from Applicant section
- Deed details from Document Upload
- Pradeshiya Sabha from Location section
- District/Province from Location section

### 4. Backward Compatible
- Old reports still work perfectly
- Can mix old simple format with new detailed format
- No data loss when upgrading

---

## 📋 Testing Checklist

Quick verification (2 minutes):
- [ ] Open http://localhost:5173
- [ ] Navigate to Legal Aspects section (Step 7)
- [ ] See 5 collapsible subsections
- [ ] Expand "Ownership & Title"
- [ ] Set "Property Encumbered" to Yes → verify encumbrance fields appear
- [ ] Set back to No → verify fields disappear
- [ ] Fill some fields, save report
- [ ] Generate DOCX and check Section 6.0

---

## 🆘 Need Help?

### Form Not Updating?
**Solution**: Hard refresh browser (Ctrl + Shift + R)

### Database Error?
**Solution**: Re-run migration:
```bash
cd D:\project\backend
python migrations/extend_legal_aspects.py
```

### Still See Old Format in Report?
**Solution**:
1. Make sure you filled NEW fields (not just old ones)
2. Restart backend server
3. Regenerate report

---

## 📊 What Was Added?

### Form Changes:
- 16 new optional fields
- 5 organized subsections
- Conditional field visibility
- Professional UI with helper text

### Report Changes:
- Professional paragraph generation
- Smart template routing (deed/plan/certificate)
- Graceful handling of missing data
- Always maintains professional tone

### Database Changes:
- 16 new columns (all optional)
- Fully backward compatible
- No breaking changes

---

## 🎉 You're All Set!

The Legal Aspects section now generates professional paragraphs that align with:
- ✅ International Valuation Standards (IVS 2025)
- ✅ Sri Lankan Rating and Valuation Ordinance
- ✅ Professional valuation report best practices

**Start using it now**: http://localhost:5173

For detailed information, see: `LEGAL_ASPECTS_IMPLEMENTATION_SUMMARY.md`
