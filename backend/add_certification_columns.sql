-- Migration script to add certification fields to the reports table
-- Run this script on your PostgreSQL database if the reports table already exists

-- Add certification columns to reports table
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_text TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certificate_survey_plan_ref VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certificate_survey_plan_date VARCHAR(50);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certificate_identity_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_valuer_name VARCHAR(300);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_valuer_designation VARCHAR(200);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS certification_date VARCHAR(50);

-- Verify the columns were added
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'reports'
AND column_name LIKE 'certif%'
ORDER BY column_name;
