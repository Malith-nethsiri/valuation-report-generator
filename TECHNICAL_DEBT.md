# ValuerPro Technical Debt Registry

**Last Updated:** 2026-01-30
**Overall Risk Level:** Medium
**Total Estimated Effort:** 10-14 hours

---

## Priority Matrix

| ID | Item | Priority | Risk | Effort | Status |
|----|------|----------|------|--------|--------|
| TD-001 | Entity Duplication Functions | HIGH | High | 3-4 hrs | **COMPLETED** |
| TD-002 | Multi-Property Form Variants | MEDIUM | Medium | 4-6 hrs | Pending |
| TD-003 | Validation Schema Integration | LOW | Low | 2-3 hrs | Pending |
| TD-004 | Deprecated Database Columns | LOW | Low | 1 hr | Pending |

---

## TD-001: Entity Duplication Functions (COMPLETED - 2026-01-30)

### Problem (RESOLVED)
`duplicate_property()` in `backend/app/crud.py` had 150+ manual field mappings. Any schema change required updating this function manually, which was error-prone. For example, `hathpaththuwa` field was missing from the manual mapping.

### Current Implementation
```python
# Lines ~472-600 in crud.py
property_dict = {
    "property_lot_description": db_property.property_lot_description,
    "lot_number": db_property.lot_number,
    "plan_number": db_property.plan_number,
    # ... 100+ more fields manually listed
}
```

### Risk Assessment
- **Data Loss:** New fields added to Property model won't be duplicated
- **Maintenance:** Every schema change requires crud.py update
- **Testing:** Hard to verify all fields are copied correctly

### Proposed Solution
Create generic `duplicate_entity()` using SQLAlchemy reflection:

```python
def duplicate_entity(db: Session, entity: Base, exclude_fields: List[str] = None) -> Base:
    """
    Generic entity duplication using SQLAlchemy inspection.

    Args:
        db: Database session
        entity: SQLAlchemy model instance to duplicate
        exclude_fields: Fields to exclude (default: ['id', 'created_at', 'updated_at'])

    Returns:
        New entity instance (not yet committed)
    """
    from sqlalchemy import inspect

    exclude = set(exclude_fields or ['id', 'created_at', 'updated_at'])
    mapper = inspect(entity.__class__)

    # Copy all column values except excluded
    data = {}
    for column in mapper.columns:
        if column.key not in exclude:
            data[column.key] = getattr(entity, column.key)

    # Handle JSON fields (deep copy)
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            import copy
            data[key] = copy.deepcopy(value)

    return entity.__class__(**data)
```

### Files to Modify
- `backend/app/crud.py` - Add helper, refactor `duplicate_property()`, `duplicate_report()`

### Solution Implemented
Created `_duplicate_entity_data()` helper function in `crud.py` that:
- Uses SQLAlchemy `inspect()` to automatically get all columns
- Deep copies JSON/dict/list fields to avoid reference issues
- Supports field exclusions and overrides
- Refactored both `duplicate_property()` and `duplicate_report()` to use it

**Before:** 150+ manual field mappings (error-prone)
**After:** ~10 lines using reflection (auto-updates with schema)

### Testing Completed
- [x] Property model has 152 columns (all automatically included)
- [x] `hathpaththuwa` field now included (was missing before)
- [x] Helper function imports and works correctly
- [x] Syntax validation passed

---

## TD-002: Multi-Property Form Variants (MEDIUM PRIORITY)

### Problem
Three overlapping form implementations exist with divergent features:

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `MultiStepForm.tsx` | ~3000 | Single property (13 steps) | Active - Keep |
| `MultiPropertyStepForm.tsx` | ~800 | First multi-property attempt | Deprecated - Remove |
| `MultiPropertyRedesignedStepForm.tsx` | ~1200 | Current multi-property | Active - Keep |

### Risk Assessment
- **UX Inconsistency:** Different validation, styling, behavior
- **Maintenance:** Bug fixes must be applied to multiple files
- **Developer Confusion:** Unclear which form to use/modify

### Current Usage Analysis
```
MultiStepForm.tsx:
  - Used for: Single property residential & bare land reports
  - Routes: /reports/new, /reports/:id/edit (single property)

MultiPropertyStepForm.tsx:
  - Used for: UNKNOWN - may be orphaned
  - Routes: Need to verify

MultiPropertyRedesignedStepForm.tsx:
  - Used for: Multi-property reports
  - Routes: /reports/new/multi, /reports/:id/edit (multi property)
```

### Proposed Solution
1. Audit all route imports to confirm usage
2. Remove `MultiPropertyStepForm.tsx` if orphaned
3. Extract shared components (steps, validation) to reduce duplication
4. Document which form handles which use case

### Files to Modify
- `frontend/src/App.tsx` or router config - Verify routes
- `frontend/src/components/MultiPropertyStepForm.tsx` - Delete if unused
- Create `frontend/src/components/forms/shared/` for common steps

### Testing Required
- [ ] Single property flow still works
- [ ] Multi-property flow still works
- [ ] All routes resolve correctly
- [ ] No broken imports after deletion

---

## TD-003: Validation Schema Integration (LOW PRIORITY)

### Problem
Created centralized `schemas/validationSchemas.ts` but forms still define schemas inline, causing duplication.

### Current State
```
Centralized (NEW - not yet used):
  frontend/src/schemas/validationSchemas.ts
    - baseApplicantPurposeSchema
    - applicantPurposeSchema
    - baseAdditionalDetailsSchema
    - buildingSchema, etc.

Still Inline (DUPLICATED):
  frontend/src/components/MultiStepForm.tsx (lines 78-370)
  frontend/src/components/MultiPropertyRedesignedStepForm.tsx (lines 91-200)
```

### Risk Assessment
- **Low Risk:** Current code works, just duplicated
- **Technical Debt:** Changes must be made in multiple places

### Proposed Solution
Update form imports to use centralized schemas:

```typescript
// Before (inline)
const applicantPurposeSchema = z.object({
    applicant_title: z.string().min(1, 'Please select a title'),
    // ... 15 more fields
});

// After (centralized)
import { applicantPurposeSchema } from '../schemas/validationSchemas';
```

### Files to Modify
- `frontend/src/components/MultiStepForm.tsx` - Replace inline schemas
- `frontend/src/components/MultiPropertyRedesignedStepForm.tsx` - Replace inline schemas
- `frontend/src/schemas/validationSchemas.ts` - Add any missing schemas

### Testing Required
- [ ] Form validation still works
- [ ] Error messages display correctly
- [ ] All field validations trigger appropriately

---

## TD-004: Deprecated Database Columns (LOW PRIORITY)

### Problem
4 deprecated columns still exist in the database schema, consuming space and causing confusion.

### Deprecated Columns

| Table | Column | Replacement | Migration Exists |
|-------|--------|-------------|------------------|
| reports | `property_lot_description` | `lot_number` | Yes - `migrate_lot_description_to_lot_number.py` |
| properties | `property_lot_description` | `lot_number` | Yes - `migrate_lot_description_to_lot_number.py` |
| reports | `access_road_segments` | `access_road_conditions` | No |
| reports | `certificate_survey_plan_ref` | `plan_number` | Yes - `migrate_certificate_to_plan_number.py` |
| reports | `certificate_survey_plan_date` | `plan_date` | Yes - `migrate_certificate_to_plan_number.py` |

### Risk Assessment
- **Low Risk:** Columns are not used in application code
- **No Data Loss:** Replacement columns contain the data

### Proposed Solution
Create migration script to drop deprecated columns:

```python
# backend/migrations/drop_deprecated_columns.py
from sqlalchemy import text
from app.database import engine

def drop_columns():
    with engine.connect() as conn:
        # Drop from reports table
        conn.execute(text("ALTER TABLE reports DROP COLUMN IF EXISTS property_lot_description"))
        conn.execute(text("ALTER TABLE reports DROP COLUMN IF EXISTS access_road_segments"))
        conn.execute(text("ALTER TABLE reports DROP COLUMN IF EXISTS certificate_survey_plan_ref"))
        conn.execute(text("ALTER TABLE reports DROP COLUMN IF EXISTS certificate_survey_plan_date"))

        # Drop from properties table
        conn.execute(text("ALTER TABLE properties DROP COLUMN IF EXISTS property_lot_description"))

        conn.commit()
        print("Deprecated columns dropped successfully")

if __name__ == "__main__":
    drop_columns()
```

### Files to Modify
- `backend/app/models.py` - Remove column definitions
- `backend/app/schemas.py` - Remove field definitions
- Create `backend/migrations/drop_deprecated_columns.py`

### Pre-Migration Checklist
- [ ] Verify no code references these columns (grep search)
- [ ] Backup database before running
- [ ] Run on staging first
- [ ] Verify application still works after migration

---

## Completed Technical Debt (This Session)

| Item | Description | Completed |
|------|-------------|-----------|
| File Download Consolidation | 5 implementations → 1 utility | 2026-01-30 |
| toTitleCase Duplication | 2 files → 1 file | 2026-01-30 |
| Anthropic Client Singleton | 6 clients → 1 singleton | 2026-01-30 |
| Building Validation Helper | 4 patterns → 1 helper | 2026-01-30 |
| Valuation N+1 Query | Added joinedload | 2026-01-30 |
| docx_generator Cleanup | Removed deprecated fallbacks | 2026-01-30 |
| PropertyInReport Interface | Moved to central types | 2026-01-30 |
| Environment Loading | Added .env.local support | 2026-01-30 |
| **TD-001: Entity Duplication** | **150 manual fields → reflection-based** | **2026-01-30** |

---

## How to Use This Document

### When Adding New Debt
1. Assign next ID (TD-XXX)
2. Assess priority based on risk and impact
3. Document problem, solution, files, and tests
4. Update priority matrix

### When Addressing Debt
1. Update status to "In Progress"
2. Follow proposed solution
3. Complete all testing items
4. Move to "Completed" section with date

### Priority Guidelines
- **HIGH:** Causes bugs, data loss, or security issues
- **MEDIUM:** Maintenance burden, UX inconsistency
- **LOW:** Code cleanliness, minor duplication

---

## Next Steps

When ready to address technical debt, work through items in priority order:

1. **TD-001** - Entity Duplication (HIGH) - Prevents future data loss bugs
2. **TD-002** - Form Variants (MEDIUM) - Reduces maintenance burden
3. **TD-003** - Validation Schemas (LOW) - Code cleanliness
4. **TD-004** - Database Columns (LOW) - Schema cleanliness
