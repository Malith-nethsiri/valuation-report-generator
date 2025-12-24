-- Migration: Add submission_recipient_position field
-- Date: 2025-12-23
-- Description: Adds optional field for recipient's position/title (e.g., Manager, Credit Officer)

ALTER TABLE reports
ADD COLUMN submission_recipient_position VARCHAR(200) NULL;

COMMENT ON COLUMN reports.submission_recipient_position IS 'Recipient position/title (e.g., Manager, Credit Officer, Branch Manager)';
