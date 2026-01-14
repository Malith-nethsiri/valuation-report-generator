-- Migration: Add lot_number column to reports and properties tables
-- This must be run BEFORE migrate_lot_description_to_lot_number.py

-- Add lot_number column to reports table
ALTER TABLE reports ADD COLUMN IF NOT EXISTS lot_number VARCHAR(200);

-- Add lot_number column to properties table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS lot_number VARCHAR(200);

-- Verify columns were added
SELECT 'Migration complete: lot_number columns added to reports and properties tables' AS status;
