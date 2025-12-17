-- Migration: Add Legal Aspects, Land Values, Valuation, and Certification fields
-- Date: 2025-12-01

-- Legal Aspects fields
ALTER TABLE reports ADD COLUMN IF NOT EXISTS ownership_type VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS street_lines_status VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS building_limits_status VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS local_authority_data TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS rent_act_effectiveness VARCHAR(200);

-- Land Values fields
ALTER TABLE reports ADD COLUMN IF NOT EXISTS comparable_properties JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS land_market_analysis TEXT;

-- Valuation fields
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_land_extent NUMERIC(10, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_rate_per_perch NUMERIC(12, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_total_land_value NUMERIC(15, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_buildings_data JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_total_buildings_value NUMERIC(15, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_addons JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_total_addons_value NUMERIC(15, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_market_value NUMERIC(15, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_forced_sale_percentage NUMERIC(5, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_forced_sale_value NUMERIC(15, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_insurance_value NUMERIC(15, 2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS valuation_manual_overrides JSON;

-- Certification fields
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_text TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certificate_survey_plan_ref VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certificate_survey_plan_date VARCHAR(50);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certificate_identity_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_valuer_name VARCHAR(300);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_valuer_designation VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_date VARCHAR(50);

-- Success message
SELECT 'Migration completed successfully: Added 27 new columns to reports table' AS status;
