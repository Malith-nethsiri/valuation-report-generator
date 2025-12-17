-- Migration: Extend Legal Aspects Section
-- Description: Add 16 new optional fields to support professional paragraph-format legal aspects
-- Date: 2025-12-10

-- Ownership-related fields (6 fields)
ALTER TABLE reports ADD COLUMN IF NOT EXISTS title_search_conducted VARCHAR(3);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS pedigree_search_conducted VARCHAR(3);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_basis_note TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS property_encumbered VARCHAR(3);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS encumbrance_type VARCHAR(100);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS encumbrance_details TEXT;

-- Street Lines-related fields (3 fields)
ALTER TABLE reports ADD COLUMN IF NOT EXISTS street_lines_gazette_ref VARCHAR(100);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS street_lines_gazette_date VARCHAR(20);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS street_lines_impact_description TEXT;

-- Building Limits-related fields (5 fields)
ALTER TABLE reports ADD COLUMN IF NOT EXISTS building_distance_from_road VARCHAR(50);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS building_plan_approved VARCHAR(20);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS building_plan_reference VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS building_approval_authority VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS building_within_limits VARCHAR(3);

-- Local Authority-related fields (2 fields)
ALTER TABLE reports ADD COLUMN IF NOT EXISTS local_authority_rated VARCHAR(3);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS local_authority_tax_levy TEXT;

-- All fields are nullable to maintain backward compatibility
-- No default values needed as all fields are optional
