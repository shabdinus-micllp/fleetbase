-- Fleetbase v0.7.75 staging-only schema correction.
-- Based on fleetbase/core-api/migrations/2026_01_13_000001_add_onboarding_fields_to_companies_table.php
-- Run only against fleetbase_v075_stage. BACKUP FIRST.
-- Inspect before alteration:
SELECT DATABASE() AS connected_database;
SHOW COLUMNS FROM companies LIKE 'onboarding_completed_at';
SHOW COLUMNS FROM companies LIKE 'onboarding_completed_by_uuid';
SHOW INDEX FROM companies WHERE Column_name = 'onboarding_completed_at';
-- If both columns are missing, run the following statement ONE TIME:
-- ALTER TABLE companies
--   ADD COLUMN onboarding_completed_at TIMESTAMP NULL DEFAULT NULL AFTER updated_at,
--   ADD COLUMN onboarding_completed_by_uuid VARCHAR(255) NULL DEFAULT NULL AFTER onboarding_completed_at,
--   ADD INDEX companies_onboarding_completed_at_index (onboarding_completed_at);
-- Verify both fields and index before retrying onboarding.
