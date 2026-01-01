-- ============================================
-- VERIFICATION SCRIPT: Check item_type Column
-- Run this FIRST before deciding on migration
-- ============================================

-- Check 1: Does item_type column exist?
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'invoice_new_item'
            AND column_name = 'item_type'
        ) 
        THEN '✅ Column EXISTS - No migration needed'
        ELSE '⚠️ Column MISSING - Migration required'
    END AS verification_result;

-- Check 2: Show all columns in invoice_new_item table
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    column_default,
    is_nullable,
    ordinal_position
FROM information_schema.columns
WHERE table_name = 'invoice_new_item'
ORDER BY ordinal_position;

-- Check 3: If column exists, show its details
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'invoice_new_item'
AND column_name = 'item_type';

-- Check 4: Count records with/without item_type (if column exists)
-- This will error if column doesn't exist - that's OK, it confirms column is missing
SELECT 
    item_type,
    COUNT(*) as count
FROM invoice_new_item
GROUP BY item_type
ORDER BY count DESC;








