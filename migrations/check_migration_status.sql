-- Migration Status Check Script
-- Run this on PRODUCTION database to verify if migrations are needed
-- Date: 2025-01-30

-- ============================================
-- CHECK 1: Verify item_type column exists
-- ============================================
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'invoice_new_item'
            AND column_name = 'item_type'
        ) 
        THEN '✅ Migration ALREADY APPLIED - item_type column exists'
        ELSE '⚠️ Migration NOT APPLIED - item_type column missing'
    END AS migration_status;

-- ============================================
-- CHECK 2: Show column details (if exists)
-- ============================================
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'invoice_new_item'
AND column_name = 'item_type';

-- ============================================
-- CHECK 3: Check existing records item_type values
-- ============================================
SELECT 
    item_type,
    COUNT(*) as count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM invoice_new_item
GROUP BY item_type
ORDER BY count DESC;

-- ============================================
-- CHECK 4: Check for records with NULL item_type (if column exists)
-- ============================================
SELECT 
    COUNT(*) as null_item_type_count
FROM invoice_new_item
WHERE item_type IS NULL;

-- ============================================
-- SUMMARY
-- ============================================
-- If migration_status shows "NOT APPLIED":
--   → Run: migrations/add_item_type_to_invoice_item.sql
--
-- If migration_status shows "ALREADY APPLIED":
--   → No action needed, proceed with code deployment
--
-- If null_item_type_count > 0:
--   → Run UPDATE statement to set default values:
--   UPDATE invoice_new_item SET item_type = 'package' WHERE item_type IS NULL;















